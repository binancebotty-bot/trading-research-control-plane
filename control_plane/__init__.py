"""
Trading Research Control Plane
===============================
Unified interface for three research backends:
- Python / py2pine (fast backtesting)
- Custom TradingView MCP (Pine/TV validation)
- Official TradingView MCP/API (data/research)
"""

# Lazy imports to avoid cascading failures from optional dependencies
__all__ = [
    'PythonPy2PineBackend',
    'CustomTradingViewMCPBackend',
    'OfficialTradingViewBackend',
    'CapabilityRegistry',
    'ResearchPipeline',
    'ExperimentProvenance',
    'ResearchSafety',
    'ObservabilityLogger',
]

__version__ = '0.2.0'


def __getattr__(name):
    """Lazy import to avoid cascading failures."""
    if name == 'PythonPy2PineBackend':
        from .backends.python_py2pine import PythonPy2PineBackend
        return PythonPy2PineBackend
    elif name == 'CustomTradingViewMCPBackend':
        from .backends.custom_tradingview_mcp import CustomTradingViewMCPBackend
        return CustomTradingViewMCPBackend
    elif name == 'OfficialTradingViewBackend':
        from .backends.official_tradingview import OfficialTradingViewBackend
        return OfficialTradingViewBackend
    elif name == 'CapabilityRegistry':
        from .registry import CapabilityRegistry
        return CapabilityRegistry
    elif name == 'ResearchPipeline':
        from .pipeline import ResearchPipeline
        return ResearchPipeline
    elif name == 'ExperimentProvenance':
        from .provenance import ExperimentProvenance
        return ExperimentProvenance
    elif name == 'ResearchSafety':
        from .safety import ResearchSafety
        return ResearchSafety
    elif name == 'ObservabilityLogger':
        from .observability import ObservabilityLogger
        return ObservabilityLogger
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")