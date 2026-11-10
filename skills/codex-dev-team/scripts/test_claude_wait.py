# SPDX-License-Identifier: MPL-2.0
"""Offline pane fixtures; no tmux, model, credentials, or key presses."""
import unittest
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from claude_wait import Events, classify, watch


class ClassifyTests(unittest.TestCase):
    def test_live_permission_overrides_tool_busy(self):
        for busy in ('Running 1 shell command…',
                     'agentctl · model-active', 'agentctl · tool-running'):
            with self.subTest(busy=busy):
                pane = f"""{busy}
Do you want to proceed?
❯ 1. Yes
  2. No
Esc to cancel · Tab to amend
"""
                self.assertEqual(classify(pane), 'attention_required')

    def test_write_permission(self):
        pane = """Do you want to create handoff.md?
❯ 1. Yes
  2. No
Esc to cancel
"""
        self.assertEqual(classify(pane), 'attention_required')

    def test_historical_menu_followed_by_idle(self):
        pane = """Do you want to proceed?
❯ 1. Yes
Esc to cancel
Completed the command.
agentctl · no task · idle 8s
❯
"""
        self.assertEqual(classify(pane, True), 'stopped_with_handoff')

    def test_quoted_question_is_not_permission(self):
        pane = """The old error said: Do you want to proceed? Esc to cancel
agentctl · no task · idle 8s
❯
"""
        self.assertEqual(classify(pane), 'stopped_without_handoff')

    def test_busy_with_no_live_menu_keeps_waiting(self):
        for busy in ('Running 1 shell command…', 'agentctl · model-active',
                     'agentctl · tool-running', '2 shells still running'):
            with self.subTest(busy=busy):
                self.assertIsNone(classify(f'Worked for 3s · done 9:00 AM\n❯\n{busy}'))

    def test_resumed_work_after_old_menu_keeps_waiting(self):
        self.assertIsNone(classify('Do you want to proceed?\n❯ 1. Yes\nEsc to cancel\nagentctl · tool-running'))

    def test_nonempty_idle_prompt_requires_inspection(self):
        for text in ('unsent user draft', 'Suggested next step'):
            with self.subTest(text=text):
                self.assertEqual(classify(f'agentctl · no task · idle 8s\n❯ {text}'),
                                 'attention_required')

    def test_old_blank_prompt_does_not_hide_current_draft(self):
        self.assertEqual(classify('❯\nagentctl · no task · idle 8s\n❯ draft', True),
                         'attention_required')

    def test_no_chrome_or_idle_signal_is_unknown(self):
        for pane in ('Do you want to proceed?', '❯', 'Task complete.',
                     'Do you want to proceed?\n❯ 1. Yes'):
            with self.subTest(pane=pane):
                self.assertIsNone(classify(pane, True))

    def test_idle_with_preview_is_inspection_not_completion(self):
        pane = 'agentctl · no task · idle 229s\n❯\n ⏵⏵ auto mode on · 1 shell · ← 2 agents'
        self.assertEqual(classify(pane, True), 'stopped_with_background')

    def test_active_foreground_with_idle_history_keeps_waiting(self):
        self.assertIsNone(classify('agentctl · idle 2s\nRunning 2 shell commands…\n❯\n · 1 shell ·'))

    def test_current_teaching_menu_above_blank_status_prompt(self):
        pane = 'Teach auto mode about your environment?\n❯ 1. Yes\n  2. Not now\nEnter to confirm · Esc to cancel\nagentctl · idle 229s\n❯\n · 1 shell ·'
        self.assertEqual(classify(pane), 'attention_required')


class EventTests(unittest.TestCase):
    def test_busy_unknown_and_transient_stop_do_not_emit(self):
        e = Events(3, ['run'])
        for _ in range(100):
            self.assertIsNone(e.observe(None, working=True))
        self.assertIsNone(e.observe('stopped_without_handoff'))
        self.assertIsNone(e.observe(None))
        self.assertIsNone(e.observe('stopped_without_handoff'))

    def test_same_stop_and_new_handoff_share_stop_id(self):
        e = Events(1, ['run'])
        first = e.observe('stopped_without_handoff')
        for _ in range(100):
            self.assertIsNone(e.observe('stopped_without_handoff'))
        handed = e.observe('stopped_with_handoff')
        self.assertEqual(first['stop_id'], handed['stop_id'])
        self.assertTrue(handed['requires_pm_verification'])

    def test_unknown_and_monitor_errors_do_not_rearm_stop(self):
        e = Events(1, ['run'])
        first = e.observe('stopped_without_handoff')
        e.observe(None)
        self.assertIsNone(e.observe('stopped_without_handoff'))
        self.assertNotIn('stop_id', e.observe('monitor_error'))
        after = e.observe('stopped_without_handoff')
        self.assertEqual(first['stop_id'], after['stop_id'])

    def test_only_stable_resumed_work_starts_another_episode(self):
        e = Events(2, ['run'])
        e.observe('stopped_without_handoff')
        first = e.observe('stopped_without_handoff')
        e.observe(None, working=True)
        e.observe('stopped_without_handoff')
        self.assertIsNone(e.observe('stopped_without_handoff'))
        e.observe(None, working=True)
        e.observe(None, working=True)
        e.observe('stopped_without_handoff')
        self.assertNotEqual(first['stop_id'], e.observe('stopped_without_handoff')['stop_id'])

    def test_restart_deduplicates_and_wrong_run_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'state.json'
            first = Events(1, ['run'], p).observe('stopped_without_handoff')
            e = Events(1, ['run'], p)
            self.assertIsNone(e.observe('stopped_without_handoff'))
            self.assertEqual(first['stop_id'], json.loads(p.read_text())['stop_id'])
            self.assertEqual(p.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(ValueError):
                Events(1, ['other-run'], p)

    def test_background_attention_and_errors_never_count_rounds(self):
        e = Events(1, ['run'])
        for event in ('attention_required', 'monitor_error', 'pane_unavailable', 'stopped_with_background'):
            r = e.observe(event)
            self.assertNotIn('wait_only_rounds', r)
            if event == 'stopped_with_background':
                self.assertTrue(r['requires_pm_verification'])

    def test_corrupt_or_symlink_state_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'state.json'
            for value in ('[]', '{', '{"version":1,"identity":["run"]}'):
                p.write_text(value)
                with self.assertRaises(ValueError):
                    Events(1, ['run'], p)
            alias = Path(d) / 'alias.json'
            alias.symlink_to(p)
            with self.assertRaises(ValueError):
                Events(1, ['run'], alias)


class WatchTests(unittest.TestCase):
    def args(self, **changes):
        a = dict(socket='/tmp/owned.sock', target='owned:0.0', handoff=None,
                 exit_marker=None, tmux_bin='tmux', poll_seconds=0.01,
                 stable_samples=1, timeout=10, follow=True, state_file=None)
        a.update(changes)
        return SimpleNamespace(**a)

    def test_follow_emits_only_changes_and_never_pane_text(self):
        idle = SimpleNamespace(returncode=0, stdout='private payload never emitted\nagentctl · idle 1s\n❯')
        busy = SimpleNamespace(returncode=0, stdout='agentctl · tool-running')
        emitted = []
        with patch('claude_wait.subprocess.run', side_effect=[busy, idle, idle, busy, idle]), \
             patch('claude_wait.time.monotonic', side_effect=[0, 1, 2, 3, 4, 5, 6, 11, 11]), \
             patch('claude_wait.time.sleep'):
            result = watch(self.args(), emitted.append)
        self.assertEqual(result['event'], 'timeout')
        self.assertEqual(len(emitted), 2)
        self.assertNotEqual(emitted[0]['stop_id'], emitted[1]['stop_id'])
        self.assertNotIn('private payload', json.dumps(emitted))

    def test_running_timeout_has_no_stop_id(self):
        busy = SimpleNamespace(returncode=0, stdout='agentctl · tool-running')
        with patch('claude_wait.subprocess.run', return_value=busy), \
             patch('claude_wait.time.monotonic', side_effect=[0, 11, 11]):
            result = watch(self.args())
        self.assertEqual(result['event'], 'timeout')
        self.assertNotIn('stop_id', result)

    def test_known_exit_marker_is_terminal(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'exit.json'
            p.write_text('{}')
            with patch('claude_wait.subprocess.run', return_value=SimpleNamespace(returncode=1)), \
                 patch('claude_wait.time.monotonic', side_effect=[0, 1]):
                r = watch(self.args(exit_marker=str(p)))
            self.assertEqual(r['event'], 'process_exited')

    def test_one_shot_only_captures_owned_pane_without_inherited_tmux(self):
        idle = SimpleNamespace(returncode=0, stdout='agentctl · idle 1s\n❯')
        with patch.dict('claude_wait.os.environ', {'TMUX': 'other', 'TMUX_TMPDIR': '/other'}), \
             patch('claude_wait.subprocess.run', return_value=idle) as capture:
            result = watch(self.args(follow=False))
        self.assertEqual(result['event'], 'stopped_without_handoff')
        self.assertEqual(capture.call_args.args[0],
                         ['tmux', '-S', '/tmp/owned.sock', 'capture-pane', '-p', '-t', 'owned:0.0'])
        self.assertNotIn('TMUX', capture.call_args.kwargs['env'])
        self.assertNotIn('TMUX_TMPDIR', capture.call_args.kwargs['env'])


if __name__ == '__main__':
    unittest.main()
