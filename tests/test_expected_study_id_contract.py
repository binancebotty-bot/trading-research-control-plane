from unittest.mock import Mock
import pytest
from control_plane.backends.custom_tradingview_mcp import CustomTradingViewMCPBackend, TVCallResult


def make_backend():
    b = CustomTradingViewMCPBackend(autostart=False)
    b.call_tool = Mock(return_value=TVCallResult(tool='pine_add_to_chart', ok=True, payload={}))
    return b


def test_expected_study_id_is_forwarded_exactly():
    b = make_backend()
    b.add_to_chart(expected_study_id='Tt9oOD')
    b.call_tool.assert_called_once_with('pine_add_to_chart', {
        'allow_update_existing': True, 'expected_study_id': 'Tt9oOD',
    })


def test_add_mode_compatibility_omits_unspecified_identity():
    b = make_backend()
    b.add_to_chart(allow_update_existing=False)
    b.call_tool.assert_called_once_with('pine_add_to_chart', {'allow_update_existing': False})


@pytest.mark.parametrize('identity', ['', ' ', ' Tt9oOD', 'Tt9oOD ', 123, [], {}])
def test_invalid_explicit_identity_is_rejected_without_transport(identity):
    b = make_backend()
    with pytest.raises(ValueError):
        b.add_to_chart(expected_study_id=identity)
    b.call_tool.assert_not_called()
