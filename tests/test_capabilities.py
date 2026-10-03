"""
Test Capabilities
=================
Tests for the capability registry and backend discovery.
"""

import sys
import json
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from control_plane.registry import CapabilityRegistry, CapabilityClassification
from control_plane.backends.python_py2pine import PythonPy2PineBackend
from control_plane.backends.custom_tradingview_mcp import CustomTradingViewMCPBackend
from control_plane.backends.official_tradingview import OfficialTradingViewBackend


class TestCapabilityRegistry:
    """Test capability registry."""
    
    def test_registry_creation(self):
        registry = CapabilityRegistry()
        assert registry is not None
    
    def test_discover_all(self):
        registry = CapabilityRegistry()
        results = registry.discover_all()
        assert 'PYTHON_PY2PINE' in results
        assert 'CUSTOM_MCP' in results
        assert 'OFFICIAL' in results
    
    def test_capabilities_registered(self):
        registry = CapabilityRegistry()
        registry.discover_all()
        assert len(registry.capabilities) > 0
    
    def test_classification(self):
        registry = CapabilityRegistry()
        registry.discover_all()
        # Check that capabilities have valid classifications
        for cap in registry.capabilities.values():
            assert isinstance(cap.classification, CapabilityClassification)
    
    def test_to_json(self):
        registry = CapabilityRegistry()
        registry.discover_all()
        data = registry.to_json()
        assert 'capabilities' in data
        assert 'summary' in data
        assert data['total_capabilities'] > 0


class TestPythonPy2PineBackend:
    """Test Python/py2pine backend."""
    
    def test_backend_creation(self):
        backend = PythonPy2PineBackend()
        assert backend.backend_id == "PYTHON_PY2PINE"
    
    def test_capabilities(self):
        backend = PythonPy2PineBackend()
        caps = backend.capabilities
        assert "backtest_single" in caps
        assert "backtest_parallel" in caps
        assert "parameter_sweep" in caps
    
    def test_list_strategies(self):
        backend = PythonPy2PineBackend()
        strategies = backend.list_strategies()
        assert len(strategies) > 0
    
    def test_list_indicators(self):
        backend = PythonPy2PineBackend()
        indicators = backend.list_indicators()
        assert len(indicators) > 0
    
    def test_get_capability_registry(self):
        backend = PythonPy2PineBackend()
        reg = backend.get_capability_registry()
        assert reg['backend'] == "PYTHON_PY2PINE"
        assert 'capabilities' in reg


class TestCustomTVMCPBackend:
    """Test Custom TV MCP backend."""
    
    def test_backend_creation(self):
        backend = CustomTradingViewMCPBackend()
        assert backend.backend_id == "TRADINGVIEW_CUSTOM_MCP"
    
    def test_capabilities(self):
        backend = CustomTradingViewMCPBackend()
        caps = backend.capabilities
        assert "pine_compile" in caps
        assert "pine_full_cycle_strategy" in caps
        assert "strategy_tester_read_summary" in caps
    
    def test_list_tools(self):
        backend = CustomTradingViewMCPBackend()
        tools = backend.list_tools()
        assert len(tools) > 0
    
    def test_get_tool_schema(self):
        backend = CustomTradingViewMCPBackend()
        tool = next(t for t in backend.list_tools() if t.name == "pine_compile")
        assert tool.description
        assert "source" in tool.input_schema["properties"]
    
    def test_get_capability_registry(self):
        backend = CustomTradingViewMCPBackend()
        reg = backend.get_capability_registry()
        assert reg['backend'] == "TRADINGVIEW_CUSTOM_MCP"
        assert 'tools' in reg


class TestOfficialTVBackend:
    """Test Official TV backend."""
    
    def test_backend_creation(self):
        backend = OfficialTradingViewBackend()
        assert backend.backend_id == "TRADINGVIEW_OFFICIAL"
    
    def test_capabilities(self):
        backend = OfficialTradingViewBackend()
        caps = backend.capabilities
        assert "market_data_ohlcv" in caps
        assert "fundamentals" in caps
        assert "news" in caps
    
    def test_available_capabilities(self):
        backend = OfficialTradingViewBackend()
        available = backend.available_capabilities
        assert len(available) > 0
    
    def test_get_capability_registry(self):
        backend = OfficialTradingViewBackend()
        reg = backend.get_capability_registry()
        assert reg['backend'] == "TRADINGVIEW_OFFICIAL"
        assert 'available_capabilities' in reg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])