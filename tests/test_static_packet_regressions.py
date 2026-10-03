from types import SimpleNamespace
import pytest
from control_plane.registry import CapabilityRegistry, CapabilityClassification
from control_plane.safety import ResearchSafety

class Backend:
    def __init__(self, names, key='capabilities'):
        self.names, self.key, self.calls = names, key, 0
    def get_capability_registry(self):
        self.calls += 1
        return {self.key: self.names}


def test_registry_uses_discovery_snapshots_and_current_tools_key():
    r = CapabilityRegistry.__new__(CapabilityRegistry)
    r.capabilities = {}
    r._backends = {'PYTHON_PY2PINE': Backend(['backtest_single']),
                   'CUSTOM_MCP': Backend(['pine_set_source'], 'tools'),
                   'OFFICIAL': Backend(['news'])}
    result = r.discover_all()
    assert all('error' not in x for x in result.values())
    assert r.capabilities['CUSTOM_MCP.pine_set_source'].classification == CapabilityClassification.CUSTOM_ONLY
    assert r.capabilities['PYTHON_PY2PINE.backtest_single'].classification == CapabilityClassification.PYTHON_ONLY
    assert all(b.calls == 1 for b in r._backends.values())

@pytest.mark.parametrize('index', ['0', '1', ' 12 '])
def test_positive_literal_history_is_not_future(index):
    assert ResearchSafety().check_look_ahead_bias('x = close[' + index + ']', []).passed

@pytest.mark.parametrize('source', ['x=close[-1]', 'x=close[dynamic]', 'request.security(s, t, close, lookahead=barmerge.lookahead_on)', 'x=barstate.islast', 'x=barstate.isrealtime', 'x=security(s,t,close)'])
def test_unsafe_future_or_unknown_index_remains_blocked(source):
    assert not ResearchSafety().check_look_ahead_bias(source, []).passed
