from unittest.mock import Mock
from control_plane.backends.custom_tradingview_mcp import CustomTradingViewMCPBackend, TVCallResult


def test_failed_set_source_never_invokes_alternate_write():
    backend = CustomTradingViewMCPBackend(autostart=False)
    backend._read_pine_source = Mock(side_effect=['ORIGINAL', 'ORIGINAL'])
    backend.call_tool = Mock(return_value=TVCallResult(tool='pine_set_source', ok=False, error='MONACO_EDITOR_UNAVAILABLE'))
    result = backend.set_pine_source('REQUESTED', settle_seconds=0)
    backend.call_tool.assert_called_once_with('pine_set_source', {'source': 'REQUESTED'})
    assert result['passed'] is False
    assert result['tool_used'] == 'pine_set_source'
    assert result['after_sha256'] == result['before_sha256']


def test_tool_failure_with_matching_readback_still_fails_closed():
    backend = CustomTradingViewMCPBackend(autostart=False)
    backend._read_pine_source = Mock(side_effect=['ORIGINAL', 'REQUESTED'])
    backend.call_tool = Mock(return_value=TVCallResult(tool='pine_set_source', ok=False))
    result = backend.set_pine_source('REQUESTED', settle_seconds=0)
    assert result['passed'] is False


def test_success_claim_without_requested_readback_is_not_pass():
    backend = CustomTradingViewMCPBackend(autostart=False)
    backend._read_pine_source = Mock(side_effect=['ORIGINAL', 'ORIGINAL'])
    backend.call_tool = Mock(return_value=TVCallResult(tool='pine_set_source', ok=True))
    result = backend.set_pine_source('REQUESTED', settle_seconds=0)
    assert result['passed'] is False


def test_success_with_exact_changed_readback_preserves_success_path():
    backend = CustomTradingViewMCPBackend(autostart=False)
    backend._read_pine_source = Mock(side_effect=['ORIGINAL', 'REQUESTED'])
    backend.call_tool = Mock(return_value=TVCallResult(tool='pine_set_source', ok=True))
    result = backend.set_pine_source('REQUESTED', settle_seconds=0)
    backend.call_tool.assert_called_once_with('pine_set_source', {'source': 'REQUESTED'})
    assert result['passed'] is True
