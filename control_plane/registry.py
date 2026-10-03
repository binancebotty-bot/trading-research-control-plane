"""
Capability Registry
===================
Machine-readable registry covering ALL THREE systems.
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime

def discover_pine_control(state):
    """Validate registered Pine control metadata, without product discovery."""
    exact = {
        'HUMAN_AUTHORITY': 'richard:operator',
        'COMPANY_CONTROL_PROTOCOL': 'RICHARD-COMPANY-CONTROL-v1',
        'COMPANY_CONTROL_PROTOCOL_SHA': '0df93c7a2d31e235915d61712c17d28c822e7da9',
        'MIGRATION_STATE': 'CUTOVER_READY',
        'EFFECTIVE_GOVERNANCE': 'LEGACY_GOVERNING_UNTIL_EXPLICIT_ARCHITECT_V1_CUTOVER',
        'GENERAL_OPERATIONS_EVIDENCE_BOARD': 'Issue #1',
        'CONTROL_REGISTRY_ROUTING_INDEX': 'Issue #2',
        'PROJECT_ARCHITECT_CONTROL_BOARD': 'Issue #3',
        'MANAGING_DIRECTOR_CONTROL_BOARD': 'Issue #4',
        'PROJECT_ARCHITECT_SESSION_UUID': '6abf7e35-26f4-83eb-ac7d-2e238d241d55',
        'REVIEWER_CONTROLLER_SESSION_UUID': '6abf60c8-4598-83eb-bc80-57a926d80b2e',
        'HERMES_LOGICAL_OWNER': '20260803_100203_2a8a55',
        'MANAGING_DIRECTOR_SESSION_UUID': 'UNREGISTERED_IN_PINE_DO_NOT_GUESS',
        'PROJECT_ARCHITECT_BOARD_HIGH_WATER': 5962793620,
        'ARCHITECT_CONTROL_HIGH_WATER': 5962829405,
        'MANAGING_DIRECTOR_CONTROL_HIGH_WATER': 'NONE',
        'UNRESOLVED_CROSS_SURFACE_CONFLICT': 'NONE',
        'SEEN_NE_CONSUMED': 'LOCKED',
        'UNRESOLVED_AUTHORITY_CONFLICT_POLICY': 'FAIL_CLOSED_AND_ROUTE_UPWARD',
        'PRODUCT_PACKET_5962813500_STATE': 'SUSPENDED_PRESERVED',
    }
    if not isinstance(state, dict):
        raise ValueError('FAIL_CLOSED: control state must be an object')
    for key, expected in exact.items():
        if state.get(key) != expected:
            raise ValueError('FAIL_CLOSED: invalid registered field ' + key)
    # Never resolve a Pine route from injected cross-project control metadata.
    def cross_project(value):
        if isinstance(value, dict):
            return any(cross_project(k) or cross_project(v) for k, v in value.items())
        if isinstance(value, list):
            return any(cross_project(v) for v in value)
        return isinstance(value, str) and any(
            token in value.lower() for token in ('build4', 'build-4', 'build_4', 'hyperliquid'))
    control_keys = ('fallback', 'supervisor', 'nonce', 'session', 'authority', 'control', 'route')
    for key, value in state.items():
        if any(token in key.lower() for token in control_keys):
            # Existing negative policy text is not a fallback binding.
            if key == 'UNRESOLVED_AUTHORITY_CONFLICT_POLICY':
                continue
            if cross_project(key) or cross_project(value):
                raise ValueError('FAIL_CLOSED: cross-project control candidate ' + key)
    high = state.get('GENERAL_CONTROL_HIGH_WATER')
    if type(high) is not int or high < 5962898559:
        raise ValueError('FAIL_CLOSED: missing or invalid consumed high-water')
    if high not in state.get('CONTROL_ALIGNMENT_CONSUMED', []):
        raise ValueError('FAIL_CLOSED: high-water seen but not consumed')
    return {**{key: state[key] for key in exact}, 'GENERAL_CONTROL_HIGH_WATER': high}


def pine_control_session_route(state, role):
    """Return only validated registered direct routes; unknown MD fails closed."""
    out = discover_pine_control(state)
    routes = {'project-architect': 'PROJECT_ARCHITECT_SESSION_UUID',
              'reviewer-controller': 'REVIEWER_CONTROLLER_SESSION_UUID'}
    if role not in routes:
        raise ValueError('FAIL_CLOSED: role unavailable or unregistered')
    return out[routes[role]]


if __name__ == '__main__':
    import sys
    if sys.argv[1:] != ['discover']:
        print('FAIL_CLOSED: expected discover', file=sys.stderr)
        raise SystemExit(2)
    try:
        state_path = Path(__file__).resolve().parents[1] / 'docs/handoff/CURRENT_STATE.json'
        result = discover_pine_control(json.loads(state_path.read_text(encoding='utf-8-sig')))
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, TypeError) as exc:
        print('FAIL_CLOSED: ' + str(exc), file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(0)


class CapabilityClassification(Enum):
    """Classification of capability availability across backends."""
    OFFICIAL_ONLY = "OFFICIAL_ONLY"
    CUSTOM_ONLY = "CUSTOM_ONLY"
    PYTHON_ONLY = "PYTHON_ONLY"
    OFFICIAL_CUSTOM = "OFFICIAL_CUSTOM"
    CUSTOM_PYTHON = "CUSTOM_PYTHON"
    ALL_THREE = "ALL_THREE"
    UNAVAILABLE = "UNAVAILABLE"
    UNPROVEN = "UNPROVEN"


@dataclass
class Capability:
    """Single capability entry in the registry."""
    canonical_name: str
    backend: str  # OFFICIAL, CUSTOM_MCP, PYTHON_PY2PINE
    native_function: str
    description: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    authentication: str
    read_write: str  # READ, WRITE, READ_WRITE
    side_effects: List[str]
    dependencies: List[str]
    limitations: List[str]
    test_status: str  # PASS, FAIL, BLOCKED, NOT_TESTABLE_SAFELY, NOT_AVAILABLE
    reliability: str  # HIGH, MEDIUM, LOW, UNKNOWN
    routing_priority: int  # 1 = highest priority
    classification: CapabilityClassification
    last_tested: Optional[str] = None
    evidence_location: Optional[str] = None
    fallback: Optional[str] = None


class CapabilityRegistry:
    """
    Machine-readable capability registry for all three backends.
    
    Discovers, catalogs, and classifies every function across:
    - Python/py2pine
    - Custom TradingView MCP
    - Official TradingView MCP/API
    """
    
    def __init__(self, registry_path: Optional[Path] = None):
        from .backends.python_py2pine import PythonPy2PineBackend
        from .backends.custom_tradingview_mcp import CustomTradingViewMCPBackend
        from .backends.official_tradingview import OfficialTradingViewBackend
        self.registry_path = registry_path or Path("registry/capabilities.json")
        self.capabilities: Dict[str, Capability] = {}
        self._backends = {
            'PYTHON_PY2PINE': PythonPy2PineBackend(),
            'CUSTOM_MCP': CustomTradingViewMCPBackend(),
            'OFFICIAL': OfficialTradingViewBackend(),
        }
    
    def discover_all(self) -> Dict[str, Any]:
        """Discover capabilities from all three backends."""
        results = {}
        
        for backend_id, backend in self._backends.items():
            try:
                caps = backend.get_capability_registry()
                results[backend_id] = caps
                self._register_backend_capabilities(backend_id, caps)
            except Exception as e:
                results[backend_id] = {"error": str(e)}
        
        self._classify_capabilities()
        return results
    
    def _register_backend_capabilities(self, backend_id: str, caps: Dict[str, Any]):
        """Register capabilities from a backend."""
        backend_caps = caps.get('capabilities', [])
        
        for cap_name in backend_caps:
            canonical = f"{backend_id}.{cap_name}"
            
            # Get tool schema if available
            tool_schema = {}
            backend_obj = self._backends.get(backend_id)
            if backend_obj and hasattr(backend_obj, 'get_tool_schema'):
                tool_schema = backend_obj.get_tool_schema(cap_name)
            
            capability = Capability(
                canonical_name=canonical,
                backend=backend_id,
                native_function=cap_name,
                description=tool_schema.get('description', f"{cap_name} from {backend_id}"),
                inputs=tool_schema.get('args', {}),
                outputs={},
                authentication="NONE" if backend_id == "PYTHON_PY2PINE" else "REQUIRED",
                read_write="READ_WRITE" if "set_" in cap_name or "add_" in cap_name or "save" in cap_name else "READ",
                side_effects=[],
                dependencies=[],
                limitations=[],
                test_status="UNPROVEN",
                reliability="UNKNOWN",
                routing_priority=1,
                classification=CapabilityClassification.UNPROVEN,
            )
            self.capabilities[canonical] = capability
    
    def _classify_capabilities(self):
        """Classify capabilities across backends."""
        # Group by functional category
        functional_groups = {
            'backtest': ['backtest_single', 'backtest_parallel', 'parameter_sweep', 'walk_forward', 'benchmark_throughput'],
            'transpile': ['transpile_pine'],
            'strategy_list': ['list_strategies'],
            'indicator_list': ['list_indicators'],
            'data_load': ['load_data'],
            'tests': ['run_deterministic_tests'],
            'pine_source': ['pine_get_source', 'pine_set_source'],
            'pine_compile': ['pine_compile', 'pine_compile_facade', 'pine_analyze', 'pine_check', 'pine_get_errors', 'pine_get_console'],
            'pine_save': ['pine_save', 'pine_list_scripts', 'pine_new', 'pine_open'],
            'pine_inject': ['pine_replace_script', 'pine_add_to_chart', 'pine_save_script'],
            'pine_full_cycle': ['pine_full_cycle_indicator', 'pine_full_cycle_strategy'],
            'chart_control': ['chart_get_state', 'chart_set_symbol', 'chart_set_timeframe', 'chart_set_type', 'chart_manage_indicator', 'chart_get_visible_range', 'chart_set_visible_range', 'chart_scroll_to_date'],
            'symbol_info': ['symbol_info', 'symbol_search'],
            'strategy_tester': ['strategy_tester_read_summary'],
            'lab_tools': ['tv_state_snapshot', 'pine_detect_blocking_modal', 'pine_resolve_known_modal'],
            'market_data': ['market_data_ohlcv', 'market_data_quote'],
            'fundamentals': ['fundamentals', 'analyst_estimates', 'filings'],
            'news': ['news', 'economic_calendar'],
            'watchlists': ['watchlists_get', 'watchlists_create', 'watchlists_update', 'watchlists_delete'],
            'alerts': ['alerts_get', 'alerts_create', 'alerts_update', 'alerts_delete', 'alert_history'],
        }
        
        # Classify each capability
        for canonical, cap in self.capabilities.items():
            # Find which functional group this belongs to
            for group_name, group_caps in functional_groups.items():
                if any(group_cap in cap.native_function for group_cap in group_caps):
                    # Check which backends have this group
                    backends_with_group = []
                    for bid, bcaps in self._backends.items():
                        backend_caps = bcaps.get('capabilities', [])
                        if any(group_cap in backend_cap for backend_cap in backend_caps for group_cap in group_caps):
                            backends_with_group.append(bid)
                    
                    if len(backends_with_group) == 3:
                        cap.classification = CapabilityClassification.ALL_THREE
                    elif len(backends_with_group) == 2:
                        if set(backends_with_group) == {'OFFICIAL', 'CUSTOM_MCP'}:
                            cap.classification = CapabilityClassification.OFFICIAL_CUSTOM
                        elif set(backends_with_group) == {'CUSTOM_MCP', 'PYTHON_PY2PINE'}:
                            cap.classification = CapabilityClassification.CUSTOM_PYTHON
                        else:
                            cap.classification = CapabilityClassification.UNAVAILABLE
                    elif len(backends_with_group) == 1:
                        if backends_with_group[0] == 'OFFICIAL':
                            cap.classification = CapabilityClassification.OFFICIAL_ONLY
                        elif backends_with_group[0] == 'CUSTOM_MCP':
                            cap.classification = CapabilityClassification.CUSTOM_ONLY
                        elif backends_with_group[0] == 'PYTHON_PY2PINE':
                            cap.classification = CapabilityClassification.PYTHON_ONLY
                    else:
                        cap.classification = CapabilityClassification.UNAVAILABLE
                    break
    
    def get_capability(self, canonical_name: str) -> Optional[Capability]:
        """Get a capability by canonical name."""
        return self.capabilities.get(canonical_name)
    
    def get_capabilities_by_backend(self, backend: str) -> List[Capability]:
        """Get all capabilities for a specific backend."""
        return [c for c in self.capabilities.values() if c.backend == backend]
    
    def get_capabilities_by_classification(self, classification: CapabilityClassification) -> List[Capability]:
        """Get all capabilities with a specific classification."""
        return [c for c in self.capabilities.values() if c.classification == classification]
    
    def update_test_status(
        self,
        canonical_name: str,
        status: str,
        evidence: Optional[str] = None,
        reliability: Optional[str] = None,
    ):
        """Update test status for a capability."""
        if canonical_name in self.capabilities:
            cap = self.capabilities[canonical_name]
            cap.test_status = status
            cap.last_tested = datetime.now().isoformat()
            if evidence:
                cap.evidence_location = evidence
            if reliability:
                cap.reliability = reliability
    
    def to_json(self) -> Dict[str, Any]:
        """Export registry to JSON-serializable format."""
        return {
            'generated': datetime.now().isoformat(),
            'version': '1.0',
            'backends': list(self._backends.keys()),
            'total_capabilities': len(self.capabilities),
            'capabilities': {
                name: {
                    'canonical_name': cap.canonical_name,
                    'backend': cap.backend,
                    'native_function': cap.native_function,
                    'description': cap.description,
                    'inputs': cap.inputs,
                    'outputs': cap.outputs,
                    'authentication': cap.authentication,
                    'read_write': cap.read_write,
                    'side_effects': cap.side_effects,
                    'dependencies': cap.dependencies,
                    'limitations': cap.limitations,
                    'test_status': cap.test_status,
                    'reliability': cap.reliability,
                    'routing_priority': cap.routing_priority,
                    'classification': cap.classification.value,
                    'last_tested': cap.last_tested,
                    'evidence_location': cap.evidence_location,
                    'fallback': cap.fallback,
                }
                for name, cap in self.capabilities.items()
            },
            'summary': self._generate_summary(),
        }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics."""
        by_backend = {}
        by_classification = {}
        by_status = {}
        
        for cap in self.capabilities.values():
            by_backend[cap.backend] = by_backend.get(cap.backend, 0) + 1
            by_classification[cap.classification.value] = by_classification.get(cap.classification.value, 0) + 1
            by_status[cap.test_status] = by_status.get(cap.test_status, 0) + 1
        
        return {
            'by_backend': by_backend,
            'by_classification': by_classification,
            'by_test_status': by_status,
        }
    
    def save(self):
        """Save registry to file."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, 'w') as f:
            json.dump(self.to_json(), f, indent=2, default=str)
    
    def load(self):
        """Load registry from file."""
        if self.registry_path.exists():
            with open(self.registry_path, 'r') as f:
                data = json.load(f)
            # Reconstruct capabilities (simplified)
            return data
        return None


def create_registry(**kwargs) -> CapabilityRegistry:
    """Factory function to create capability registry."""
    return CapabilityRegistry(**kwargs)