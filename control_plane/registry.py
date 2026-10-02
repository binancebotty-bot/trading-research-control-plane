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

from .backends.python_py2pine import PythonPy2PineBackend
from .backends.custom_tradingview_mcp import CustomTradingViewMCPBackend
from .backends.official_tradingview import OfficialTradingViewBackend


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