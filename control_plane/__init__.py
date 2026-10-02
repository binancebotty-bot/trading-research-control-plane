"""
Trading Research Control Plane
===============================
Unified interface for three research backends:
- Python / py2pine (fast backtesting)
- Custom TradingView MCP (Pine/TV validation)
- Official TradingView MCP/API (data/research)
"""

from .backends.python_py2pine import PythonPy2PineBackend
from .backends.custom_tradingview_mcp import CustomTradingViewMCPBackend
from .backends.official_tradingview import OfficialTradingViewBackend
from .registry import CapabilityRegistry
from .pipeline import ResearchPipeline
from .provenance import ExperimentProvenance
from .safety import ResearchSafety
from .observability import ObservabilityLogger

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

__version__ = '0.1.0'