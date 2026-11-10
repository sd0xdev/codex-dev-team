# SPDX-License-Identifier: MPL-2.0
"""Offline RC launch/dispatch regression tests; no Claude service or user tmux access."""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import claude_run as cr


class RemoteControlTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='dev-team-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        self.mission = self.root / 'input.md'
        self.mission.write_text('Read this mission.\nDo not commit.\n')
        self.cli = self.root / 'fake-claude'
        self.cli.write_text('#!/bin/sh\ncase "$1" in\n--help) echo "--remote-control --session-id --effort";;\n--version) echo "fake-offline";;\n*) exit 91;;\nesac\n')
        self.cli.chmod(0o700)
        self.args = argparse.Namespace(mission=str(self.mission), permission_mode='auto',
            claude_bin=str(self.cli), setenv=[], runs_root=str(self.root / 'runs'),
            tmux_session=None, tmux_socket=str(self.root / 't.sock'), prepare_only=True,
            path_prepend=[], add_dir=[], task_name='TEST-1', no_rc_reason=None)

    def prepare(self, **changes):
        for k, v in changes.items():
            setattr(self.args, k, v)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            cr.prepare_and_start(self.args, 'launch', self.repo, 'exact-model')
        return Path(json.loads(out.getvalue())['run_dir'])

    def ready(self):
        directory = self.prepare()
        meta = json.loads((directory / 'meta.json').read_text())
        meta.update(started=True, pane_id='%7')
        (directory / 'meta.json').write_text(json.dumps(meta))
        a = argparse.Namespace(run_dir=str(directory), remote_url='https://claude.ai/code/session_test',
                               actual_model='exact-model', confirm_rc_active_and_idle=True)
        return directory, meta, a

    def fake_tmux(self, meta):
        def call(socket, *args, **kwargs):
            self.assertEqual(str(socket), meta['tmux_socket'])
            body = meta['tmux_session'].encode() if args[0] == 'display-message' else b'Current pane'
            return subprocess.CompletedProcess(args, 0, body, b'')
        return call

    def test_default_launch_waits_without_mission(self):
        directory = self.prepare()
        meta = json.loads((directory / 'meta.json').read_text())
        script = (directory / 'run.sh').read_text()
        self.assertIn('--remote-control', meta['argv'])
        self.assertIn('--session-id', meta['argv'])
        self.assertNotIn('-p', meta['argv'])
        self.assertNotIn('mission.md', script)
        self.assertNotIn('stream.jsonl', script)
        self.assertEqual(cr.status(directory)['state'], 'prepared')
        self.assertEqual(directory.stat().st_mode & 0o777, 0o700)
        self.assertEqual((directory / 'meta.json').stat().st_mode & 0o777, 0o600)

    def test_cli_launch_defaults_and_explicit_overrides(self):
        for overrides, model, effort in [(['--model', 'test-model-a'], 'test-model-a', None),
                (['--model', 'test-model-b', '--effort', 'high'], 'test-model-b', 'high')]:
            args = ['claude_run.py', 'launch', '--repo', str(self.repo),
                    '--mission', str(self.mission), '--runs-root', str(self.root / 'runs'),
                    '--tmux-socket', str(self.root / 't.sock'), '--claude-bin', str(self.cli),
                    '--prepare-only', '--permission-mode', 'manual', *overrides]
            output = io.StringIO()
            with patch('sys.argv', args), contextlib.redirect_stdout(output):
                cr.main()
            directory = Path(json.loads(output.getvalue())['run_dir'])
            meta = json.loads((directory / 'meta.json').read_text())
            self.assertEqual(meta['requested_model'], model)
            self.assertEqual(meta['requested_effort'], effort)
            if effort is None:
                self.assertNotIn('--effort', meta['argv'])
            else:
                self.assertEqual(meta['argv'][meta['argv'].index('--effort') + 1], effort)
            self.assertEqual(meta['argv'][meta['argv'].index('--model') + 1], model)
            self.assertFalse(meta['started'])

    def test_resume_preserves_effort_and_supports_explicit_change(self):
        directory = self.prepare(effort='medium')
        (directory / 'exit.json').write_text('{"exit_code": 0}')
        for overrides, effort in [([], 'medium'), (['--effort', 'high'], 'high')]:
            args = ['claude_run.py', 'resume', '--from', str(directory), '--mission', str(self.mission),
                    '--prepare-only', '--permission-mode', 'manual', *overrides]
            output = io.StringIO()
            with patch('sys.argv', args), patch.object(cr, 'session_processes', return_value=[]), contextlib.redirect_stdout(output):
                cr.main()
            resumed = Path(json.loads(output.getvalue())['run_dir'])
            meta = json.loads((resumed / 'meta.json').read_text())
            self.assertEqual(meta['requested_model'], 'exact-model')
            self.assertEqual(meta['requested_effort'], effort)
            self.assertEqual(meta['argv'][meta['argv'].index('--effort') + 1], effort)

    def test_launch_requires_an_explicit_model(self):
        args = ['claude_run.py', 'launch', '--repo', str(self.repo),
                '--mission', str(self.mission), '--runs-root', str(self.root / 'runs'),
                '--permission-mode', 'manual', '--prepare-only']
        with patch('sys.argv', args), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            cr.main()
        self.assertEqual(error.exception.code, 2)
        self.assertFalse((self.root / 'runs').exists())

    def test_related_projects_keep_separate_conversation_identities(self):
        first_repo = self.repo
        first = self.prepare(task_name='api')
        self.repo = self.root / 'sdk'
        self.repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        second = self.prepare(task_name='sdk')
        a = json.loads((first / 'meta.json').read_text())
        b = json.loads((second / 'meta.json').read_text())
        self.assertNotEqual(a['session_id'], b['session_id'])
        self.assertNotEqual(a['tmux_session'], b['tmux_session'])
        self.assertNotEqual(first, second)
        self.assertEqual(a['fingerprint']['repo'], str(first_repo))
        self.assertEqual(b['fingerprint']['repo'], str(self.repo))
        self.assertEqual(a['tmux_socket'], b['tmux_socket'])
        self.assertFalse((first / 'dispatch.json').exists())
        self.assertFalse((second / 'dispatch.json').exists())

    def test_unsupported_effort_stops_before_creating_run(self):
        self.cli.write_text('#!/bin/sh\necho "--remote-control --session-id"\n')
        with self.assertRaises(SystemExit):
            self.prepare(effort='medium')
        self.assertFalse((self.root / 'runs').exists())

    def test_print_requires_explicit_reason(self):
        directory = self.prepare(no_rc_reason='User requested a single offline print run')
        meta = json.loads((directory / 'meta.json').read_text())
        self.assertEqual(meta['mode'], 'print')
        self.assertIn('-p', meta['argv'])
        self.assertIn('mission.md', (directory / 'run.sh').read_text())

    def test_unsupported_rc_does_not_fall_back(self):
        self.cli.write_text('#!/bin/sh\necho old-version\n')
        with self.assertRaises(SystemExit):
            self.prepare()
        self.assertFalse((self.root / 'runs').exists())

    def test_permission_and_env_guards(self):
        for field, value in [('permission_mode', 'bypassPermissions'), ('setenv', [('HOME', '/tmp')])]:
            with self.subTest(field=field), self.assertRaises(SystemExit):
                self.prepare(**{field: value})
            self.args.permission_mode, self.args.setenv = 'auto', []
        self.assertFalse((self.root / 'runs').exists())

    def test_dispatch_rejects_unverified_or_wrong_identity_inputs(self):
        directory, meta, a = self.ready()
        for field, value in [('confirm_rc_active_and_idle', False), ('actual_model', 'wrong'),
                             ('remote_url', 'https://example.org/code/session_test')]:
            old = getattr(a, field)
            setattr(a, field, value)
            with self.subTest(field=field), self.assertRaises(SystemExit):
                cr.dispatch(a)
            setattr(a, field, old)
        self.assertFalse((directory / 'dispatch.json').exists())

    def test_dispatch_once_to_recorded_pane(self):
        directory, meta, a = self.ready()
        with patch.object(cr, 'tmux_alive', return_value=True), patch.object(cr, 'tmux', side_effect=self.fake_tmux(meta)) as tmux, contextlib.redirect_stdout(io.StringIO()):
            cr.dispatch(a)
            with self.assertRaises(SystemExit):
                cr.dispatch(a)
        calls = tmux.call_args_list
        sends = [c for c in calls if c.args[1] == 'send-keys']
        self.assertEqual(len(sends), 1)
        self.assertIn('%7', sends[0].args)
        self.assertEqual(json.loads((directory / 'dispatch.json').read_text())['state'], 'sent')
        self.assertEqual((directory / 'dispatch-pane.txt').stat().st_mode & 0o777, 0o600)

    def test_optional_context_suffix_dispatch_and_status_preserve_raw_ids(self):
        base = 'test-model-a'
        for requested, actual in [(base + '[1m]', base), (base, base + '[1m]')]:
            with self.subTest(requested=requested, actual=actual):
                directory, meta, a = self.ready()
                meta['requested_model'] = requested
                (directory / 'meta.json').write_text(json.dumps(meta))
                a.actual_model = actual
                with patch.object(cr, 'tmux_alive', return_value=True), patch.object(cr, 'tmux', side_effect=self.fake_tmux(meta)), patch.object(cr, 'session_processes', return_value=[]), contextlib.redirect_stdout(io.StringIO()):
                    cr.dispatch(a)
                    state = cr.status(directory)
                self.assertTrue(state['model_match'])
                self.assertEqual(state['requested_model'], requested)
                self.assertEqual(state['actual_model'], actual)
                self.assertEqual(state['dispatch']['actual_model'], actual)

    def test_different_models_and_unrecognized_suffixes_still_block_dispatch(self):
        directory, meta, a = self.ready()
        meta['requested_model'] = 'test-model-a[1m]'
        (directory / 'meta.json').write_text(json.dumps(meta))
        for actual in ['test-model-b[1m]', 'test-model-old', 'model-alias',
                       'test-model-a[200k]', 'test-model-a[1m][1m]', '']:
            with self.subTest(actual=actual), self.assertRaises(SystemExit):
                a.actual_model = actual
                cr.dispatch(a)
        self.assertFalse((directory / 'dispatch.json').exists())

    def test_print_status_compares_optional_suffix_without_losing_evidence(self):
        directory = self.prepare(no_rc_reason='Offline test')
        meta = json.loads((directory / 'meta.json').read_text())
        meta['requested_model'] = 'test-model-a[1m]'
        (directory / 'meta.json').write_text(json.dumps(meta))
        for actual, expected in [('test-model-a', True),
                                 ('test-model-a[1m]', True),
                                 ('test-model-b[1m]', False), (None, None)]:
            with self.subTest(actual=actual):
                event = {'type': 'system', 'subtype': 'init', 'model': actual}
                (directory / 'stream.jsonl').write_text(json.dumps(event) + '\n')
                state = cr.status(directory)
                self.assertIs(state['model_match'], expected)
                self.assertEqual(state['requested_model'], meta['requested_model'])
                self.assertEqual(state['actual_model'], actual)

    def test_partial_send_cannot_be_replayed(self):
        directory, meta, a = self.ready()
        base = self.fake_tmux(meta)
        def fail(socket, *args, **kwargs):
            if args[0] == 'send-keys':
                raise SystemExit(2)
            return base(socket, *args, **kwargs)
        with patch.object(cr, 'tmux_alive', return_value=True), patch.object(cr, 'tmux', side_effect=fail):
            with self.assertRaises(SystemExit):
                cr.dispatch(a)
            with self.assertRaises(SystemExit):
                cr.dispatch(a)
        self.assertEqual(json.loads((directory / 'dispatch.json').read_text())['state'], 'sending_or_unknown')

    def test_dead_run_cannot_receive_mission(self):
        directory, meta, a = self.ready()
        with patch.object(cr, 'tmux_alive', return_value=False), self.assertRaises(SystemExit):
            cr.dispatch(a)
        self.assertFalse((directory / 'dispatch.json').exists())

    def test_current_rc_not_inferred_from_historical_dispatch(self):
        directory, meta, a = self.ready()
        with patch.object(cr, 'tmux_alive', return_value=True), patch.object(cr, 'session_processes', return_value=[]):
            self.assertEqual(cr.status(directory)['state'], 'awaiting_rc_readback')
            (directory / 'dispatch.json').write_text(json.dumps({'state': 'sent', 'actual_model': 'exact-model'}))
            state = cr.status(directory)
        self.assertEqual(state['state'], 'interactive_alive')
        self.assertIn('unverified', state['rc_current_state'])

    def test_resume_uses_same_id_but_requires_new_rc_readback(self):
        directory, meta, a = self.ready()
        (directory / "exit.json").write_text('{"exit_code": 0}')
        args = ['claude_run.py', 'resume', '--from', str(directory), '--mission', str(self.mission), '--prepare-only']
        output = io.StringIO()
        with patch('sys.argv', args), patch.object(cr, 'session_processes', return_value=[]), contextlib.redirect_stdout(output):
            cr.main()
        new_dir = Path(json.loads(output.getvalue())['run_dir'])
        new_meta = json.loads((new_dir / 'meta.json').read_text())
        self.assertNotEqual(directory, new_dir)
        self.assertEqual(new_meta['session_id'], meta['session_id'])
        self.assertIn('--remote-control', new_meta['argv'])
        self.assertIn('--resume', new_meta['argv'])
        self.assertFalse((new_dir / 'dispatch.json').exists())

    def test_resume_rejects_live_interactive_session(self):
        directory, meta, a = self.ready()
        args = ['claude_run.py', 'resume', '--from', str(directory), '--mission', str(self.mission), '--prepare-only']
        with patch('sys.argv', args), patch.object(cr, 'tmux_alive', return_value=True), patch.object(cr, 'session_processes', return_value=[]), self.assertRaises(SystemExit):
            cr.main()
        self.assertEqual(len(list((self.root / 'runs').glob('resume-*'))), 0)

    def test_tmux_ignores_inherited_socket(self):
        with patch.dict(os.environ, {'TMUX': 'foreign', 'TMUX_TMPDIR': 'foreign'}):
            env = cr.tmux_env()
        self.assertNotIn('TMUX', env)
        self.assertNotIn('TMUX_TMPDIR', env)


if __name__ == '__main__':
    unittest.main()
