from unittest.mock import Mock, patch

from control_plane.backends import custom_tradingview_mcp as backend_module
from control_plane.backends import mcp_client as client_module
from control_plane.invariants import parity_requires_real_tv_result


def test_backend_and_client_keep_same_cdp_identity():
    with patch.object(backend_module, 'MCPClient') as client_type:
        client_type.return_value.cdp_host = '127.0.0.9'
        client_type.return_value.cdp_port = 9333
        backend = backend_module.CustomTradingViewMCPBackend(
            autostart=False, cdp_host='127.0.0.9', cdp_port=9333
        )
    assert backend.cdp_host == '127.0.0.9'
    assert backend.cdp_port == 9333
    client_type.assert_called_once_with(
        server_dir=str(backend.mcp_dir), server_script='src/server.js',
        cdp_host='127.0.0.9', cdp_port=9333
    )


def test_describe_session_uses_backend_cdp_fields():
    backend = backend_module.CustomTradingViewMCPBackend(autostart=False)
    backend._started = True
    client = Mock(unsafe=True)
    client.cdp_host = '127.0.0.1'
    client.cdp_port = 9222
    client.verify_cdp_endpoint.return_value = {
        'reachable': True, 'browser': 'Edge', 'protocol_version': '1.3',
        'targets': [{'id': 'target-1'}],
        'tradingview_targets': [{'id': 'target-1', 'url': 'https://www.tradingview.com/chart/layout/'}]
    }
    client.assert_target_matches_cdp.return_value = {
        'mcp_target_id': 'target-1', 'mcp_target_url': 'https://www.tradingview.com/chart/layout/',
        'mcp_target_title': 'chart', 'verdict': 'PASS', 'target_found_on_cdp': True
    }
    client.get_target_identity.return_value = {'target_id': 'target-1', 'target_url': 'https://www.tradingview.com/chart/layout/', 'target_title': 'chart'}
    client.call_tool.side_effect = [
        client_module.MCPToolResult(tool='chart_get_state', success=True, result={'symbol': 'BINANCE:ETHUSDT'}, request_id='1'),
        client_module.MCPToolResult(tool='tv_state_snapshot', success=True, result={'symbol': 'BINANCE:ETHUSDT'}, request_id='2'),
    ]
    backend._client = client
    session = backend.describe_session()
    assert session['cdp_endpoint'] == '127.0.0.1:9222'
    assert session['mcp_cdp_endpoint_match'] == 'PASS'
    assert session['visible_session'] is True


def test_backend_call_routes_real_failure_and_rejects_placeholder_evidence():
    backend = backend_module.CustomTradingViewMCPBackend(autostart=False)
    backend._started = True
    client = Mock()
    client.cdp_host = '127.0.0.1'
    client.cdp_port = 9222
    client.get_target_identity.return_value = {'target_id': 'target-1', 'target_url': 'https://www.tradingview.com/chart/x/'}
    client.call_tool.return_value = client_module.MCPToolResult(
        tool='chart_get_state', success=False,
        result={'note': 'Tool metadata - actual execution requires MCP client'},
        error='transport failed', execution_time_ms=9, request_id='3'
    )
    backend._client = client
    result = backend.call_tool('chart_get_state', {'symbol': 'ETHUSDT'})
    client.call_tool.assert_called_once_with('chart_get_state', {'symbol': 'ETHUSDT'})
    assert result.ok is False
    assert result.error == 'transport failed'
    assert result.attestation.placeholder_markers
    verdict = parity_requires_real_tv_result(result.attestation, result.payload)
    assert verdict.passed is False


def test_client_target_identity_and_endpoint_use_configured_cdp():
    client = client_module.MCPClient(cdp_host='127.0.0.9', cdp_port=9333)
    client.call_tool = Mock(return_value=client_module.MCPToolResult(
        tool='tv_health_check', success=True,
        result={'cdp_connected': True, 'target_id': 'target-9',
                'target_url': 'https://www.tradingview.com/chart/layout/',
                'target_title': 'chart', 'chart_symbol': 'BINANCE:ETHUSDT',
                'chart_resolution': '15'}, request_id='4'
    ))
    with patch('urllib.request.urlopen') as open_url:
        open_url.side_effect = [
            Mock(__enter__=Mock(return_value=Mock(read=Mock(return_value=b'{"Browser":"Edge","Protocol-Version":"1.3","webSocketDebuggerUrl":"ws://endpoint"}'))), __exit__=Mock(return_value=False)),
            Mock(__enter__=Mock(return_value=Mock(read=Mock(return_value=b'[{"id":"target-9","type":"page","url":"https://www.tradingview.com/chart/layout/","title":"chart"}]'))), __exit__=Mock(return_value=False)),
        ]
        identity = client.get_target_identity()
        binding = client.assert_target_matches_cdp()
    assert identity['target_id'] == 'target-9'
    assert binding['cdp_endpoint'] == '127.0.0.9:9333'
    assert binding['target_found_on_cdp'] is True
    assert all('127.0.0.9:9333' in call.args[0] for call in open_url.call_args_list)


def test_backend_stop_only_stops_its_client_owned_process():
    backend = backend_module.CustomTradingViewMCPBackend(autostart=False)
    owned = Mock()
    client = Mock()
    client._process = owned
    backend._client = client
    backend.stop()
    client.stop.assert_called_once_with()
    owned.terminate.assert_not_called()
