import ast
import copy
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def functions():
    tree = ast.parse((ROOT / 'control_plane/registry.py').read_text())
    wanted = {'discover_pine_control', 'pine_control_session_route'}
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in wanted]
    ns = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), 'registry-control-functions', 'exec'), ns)
    return ns


class ControlDiscoveryTests(unittest.TestCase):
    def test_registered_state_discovery(self):
        ns = functions()
        self.assertIn('discover_pine_control', ns, 'Existing registry has no control discovery implementation')
        state = json.loads((ROOT / 'docs/handoff/CURRENT_STATE.json').read_text())
        out = ns['discover_pine_control'](state)
        self.assertEqual(out['COMPANY_CONTROL_PROTOCOL_SHA'], '0df93c7a2d31e235915d61712c17d28c822e7da9')
        self.assertEqual(out['PROJECT_ARCHITECT_SESSION_UUID'], '6abf7e35-26f4-83eb-ac7d-2e238d241d55')
        self.assertEqual(out['REVIEWER_CONTROLLER_SESSION_UUID'], '6abf60c8-4598-83eb-bc80-57a926d80b2e')
        self.assertEqual(out['MANAGING_DIRECTOR_SESSION_UUID'], 'UNREGISTERED_IN_PINE_DO_NOT_GUESS')
        self.assertEqual(out['MIGRATION_STATE'], 'CUTOVER_READY')
        self.assertEqual(out['EFFECTIVE_GOVERNANCE'], 'LEGACY_GOVERNING_UNTIL_EXPLICIT_ARCHITECT_V1_CUTOVER')


class ControlNegativeTests(unittest.TestCase):
    def setUp(self):
        self.ns = functions()
        self.state = json.loads((ROOT / 'docs/handoff/CURRENT_STATE.json').read_text())

    def test_required_fields_fail_closed(self):
        for key in ('PROJECT_ARCHITECT_SESSION_UUID', 'REVIEWER_CONTROLLER_SESSION_UUID',
                    'COMPANY_CONTROL_PROTOCOL_SHA', 'GENERAL_OPERATIONS_EVIDENCE_BOARD',
                    'CONTROL_REGISTRY_ROUTING_INDEX', 'PROJECT_ARCHITECT_CONTROL_BOARD',
                    'MANAGING_DIRECTOR_CONTROL_BOARD'):
            for value in (None, 'wrong'):
                with self.subTest(key=key, value=value):
                    state = copy.deepcopy(self.state)
                    state[key] = value
                    with self.assertRaises(ValueError):
                        self.ns['discover_pine_control'](state)

    def test_unknown_md_route_rejected(self):
        with self.assertRaises(ValueError):
            self.ns['pine_control_session_route'](self.state, 'managing-director')
        state = copy.deepcopy(self.state)
        state['MANAGING_DIRECTOR_SESSION_UUID'] = state['REVIEWER_CONTROLLER_SESSION_UUID']
        with self.assertRaises(ValueError):
            self.ns['discover_pine_control'](state)

    def test_conflict_rejected(self):
        self.state['UNRESOLVED_CROSS_SURFACE_CONFLICT'] = 'AUTHORITY_CONFLICT'
        with self.assertRaises(ValueError):
            self.ns['discover_pine_control'](self.state)

    def test_cross_project_injections_rejected(self):
        for key in ('CONTROL_FALLBACK', 'SESSION_FALLBACK', 'AUTHORITY_FALLBACK',
                    'SUPERVISOR', 'CONTROL_NONCE', 'CONTROL_STATE_FALLBACK'):
            with self.subTest(key=key):
                state = copy.deepcopy(self.state)
                state[key] = {'candidate': 'hyperliquid-build4 Issue #1'}
                with self.assertRaises(ValueError):
                    self.ns['discover_pine_control'](state)

    def test_seen_not_consumed(self):
        self.state['GENERAL_CONTROL_HIGH_WATER'] += 1
        with self.assertRaises(ValueError):
            self.ns['discover_pine_control'](self.state)

    def test_exact_routes(self):
        for role, key in (('project-architect', 'PROJECT_ARCHITECT_SESSION_UUID'),
                          ('reviewer-controller', 'REVIEWER_CONTROLLER_SESSION_UUID')):
            self.assertEqual(self.ns['pine_control_session_route'](self.state, role), self.state[key])

    def test_cli_no_product_imports_or_connections(self):
        import subprocess
        import sys
        code = '''import sys, runpy
class Guard:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith('control_plane.backends'):
            raise AssertionError('product backend imported: ' + fullname)
sys.meta_path.insert(0, Guard())
def audit(event, args):
    if event in ('socket.connect', 'subprocess.Popen'):
        raise AssertionError('external call: ' + event)
sys.addaudithook(audit)
sys.argv = ['control_plane.registry', 'discover']
runpy.run_module('control_plane.registry', run_name='__main__')
'''
        result = subprocess.run([sys.executable, '-c', code], cwd=ROOT,
                                capture_output=True, text=True, timeout=15,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.assertEqual(result.returncode, 0, result.stderr)
        out = json.loads(result.stdout)
        self.assertEqual(out['GENERAL_CONTROL_HIGH_WATER'], self.state['GENERAL_CONTROL_HIGH_WATER'])
        self.assertEqual(out['MANAGING_DIRECTOR_SESSION_UUID'], 'UNREGISTERED_IN_PINE_DO_NOT_GUESS')
        self.assertEqual(out['SEEN_NE_CONSUMED'], 'LOCKED')

    def test_unknown_command_fail_closed(self):
        import subprocess
        import sys
        result = subprocess.run([sys.executable, '-m', 'control_plane.registry', 'unknown'],
                                cwd=ROOT, capture_output=True, text=True, timeout=15,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.assertEqual(result.returncode, 2)
        self.assertIn('FAIL_CLOSED', result.stderr)


if __name__ == '__main__':
    unittest.main()
