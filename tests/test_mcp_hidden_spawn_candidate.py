from unittest.mock import Mock, patch
import sys
from control_plane.backends import mcp_client as module


def test_windows_hidden_spawn():
    child = Mock()
    child.poll.return_value = None
    with patch.object(sys, 'platform', 'win32'), patch.object(module.subprocess, 'Popen', return_value=child) as launch, patch.object(module.time, 'sleep'):
        assert module.MCPClient().start()
    kwargs = launch.call_args.kwargs
    assert kwargs['creationflags'] == module.subprocess.CREATE_NO_WINDOW
    assert kwargs['startupinfo'].dwFlags & module.subprocess.STARTF_USESHOWWINDOW
    assert kwargs['startupinfo'].wShowWindow == module.subprocess.SW_HIDE
    assert kwargs['stdin'] == module.subprocess.PIPE
    assert kwargs['stdout'] == module.subprocess.PIPE
    assert kwargs['stderr'] == module.subprocess.PIPE
    assert kwargs['text'] is True
    assert kwargs['bufsize'] == 1


def test_nonwindows_contract_unchanged():
    child = Mock()
    child.poll.return_value = None
    with patch.object(sys, 'platform', 'linux'), patch.object(module.subprocess, 'Popen', return_value=child) as launch, patch.object(module.time, 'sleep'):
        client = module.MCPClient()
        assert client.start()
    assert launch.call_args.args == (['node', 'src/server.js'],)
    assert launch.call_args.kwargs == dict(cwd=client.server_dir, stdin=module.subprocess.PIPE, stdout=module.subprocess.PIPE, stderr=module.subprocess.PIPE, text=True, bufsize=1)


def test_stop_only_owns_assigned_child():
    owned = Mock()
    unrelated = Mock()
    client = module.MCPClient()
    client._process = owned
    client.stop()
    owned.terminate.assert_called_once_with()
    owned.wait.assert_called_once_with(timeout=5)
    owned.kill.assert_not_called()
    assert unrelated.mock_calls == []
    assert client._process is None

