#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Read-only, model-free waiting for one owned Claude tmux pane.

Emits only a compact event, never pane contents. A stopped event is a reason
for PM inspection, not proof that work is complete. Python 3.9+, tmux.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import uuid


FOREGROUND = re.compile(r'agentctl[^\n]*(?:model-active|tool-running)|Running \d+ shell|^[^\w\n]*\w+[^\n]*…\s*\(', re.M)
BACKGROUND = re.compile(r'\d+ shells? (?:still )?running|· \d+ shells?(?: ·|$)', re.M)
LIVE_IDLE = re.compile(r'agentctl[^\n]*· idle \d+s', re.I)
IDLE = re.compile(r'agentctl[^\n]*· idle \d+s|(?:Worked|Churned|Crunched|Cogitated)[^\n]*· done ', re.I)
PROMPT = re.compile(r'^❯', re.M)
IDLE_PROMPT = re.compile(r'^❯[^\S\n]*$', re.M)
CHOICE = re.compile(r'^[^\S\n]*❯[^\S\n]*\d+[.)][^\S\n]+\S', re.M)
FOOTER = re.compile(r'Enter to (?:select|confirm)|Esc to cancel', re.I)
QUESTION = re.compile(r'Do you want to (?:proceed|allow)|Allow (?:once|this)|permission (?:required|request)|Enter to (?:select|confirm)|Esc to cancel', re.I)


def classify(pane, has_handoff=False):
    tail = '\n'.join(pane.splitlines()[-22:])
    # A tool awaiting permission can still display "Running 1 shell command".
    # Require current menu chrome, not a historical or quoted question alone.
    choices = list(CHOICE.finditer(tail))
    if choices and QUESTION.search(tail):
        footer = FOOTER.search(tail, choices[-1].end())
        # Ignore remaining hints on the same footer line (e.g. "· Esc to cancel").
        after = tail[footer.end():].partition('\n')[2] if footer else ''
        menu_with_status = LIVE_IDLE.search(after) and after.lstrip().startswith('agentctl')
        later_prompt = PROMPT.search(after)
        blank_status_prompt = menu_with_status and all(IDLE_PROMPT.fullmatch(m.group(0)) for m in re.finditer(r'^❯[^\n]*', after, re.M))
        if footer and (not later_prompt or blank_status_prompt) and not FOREGROUND.search(after):
            return 'attention_required'
    prompts = list(PROMPT.finditer(tail))
    if prompts and IDLE.search(tail) and not FOREGROUND.search(tail):
        # Old "done" text is not enough to reinterpret a still-running shell.
        # A current idle status with a background shell is a candidate to inspect,
        # never a claim that reviewers/tests have stopped (it may be a preview).
        if BACKGROUND.search(tail) and not LIVE_IDLE.search(tail):
            return None
        current_prompt = tail[prompts[-1].start():].splitlines()[0]
        if IDLE_PROMPT.fullmatch(current_prompt):
            if BACKGROUND.search(tail):
                return 'stopped_with_background'
            return 'stopped_with_handoff' if has_handoff else 'stopped_without_handoff'
        # Plain capture cannot distinguish a draft from a prompt suggestion.
        # Wake the PM for inspection; never clear or submit either automatically.
        return 'attention_required'
    return None


class Events:
    """Debounce and deduplicate episodes. Never decides PM wait-round counts."""

    def __init__(self, stable_samples, identity, state_file=None):
        self.samples, self.identity = stable_samples, identity
        self.path = Path(state_file) if state_file else None
        self.data = {'version': 1, 'identity': identity, 'last_event': None, 'stop_id': None}
        if self.path and self.path.exists():
            if self.path.is_symlink():
                raise ValueError('state-file must not be a symlink')
            loaded = json.loads(self.path.read_text())
            if not isinstance(loaded, dict) or loaded.get('version') != 1 or loaded.get('identity') != identity:
                raise ValueError('state-file belongs to another run or format')
            if not {'last_event', 'stop_id'} <= loaded.keys():
                raise ValueError('state-file is incomplete')
            self.data = loaded
        self.prior, self.count = None, 0

    def save(self):
        if not self.path:
            return
        if self.path.is_symlink():
            raise ValueError('state-file must not be a symlink')
        fd, name = tempfile.mkstemp(prefix='.claude-wait-', dir=self.path.parent)
        try:
            with os.fdopen(fd, 'w') as out:
                json.dump(self.data, out)
                out.write('\n')
            os.replace(name, self.path)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def observe(self, event, working=False):
        candidate = event or ('working' if working else None)
        self.count = self.count + 1 if candidate and candidate == self.prior else int(bool(candidate))
        self.prior = candidate
        if self.count < self.samples:
            return None
        if candidate == 'working':
            if self.data['last_event'] is not None or self.data['stop_id'] is not None:
                self.data.update(last_event=None, stop_id=None)
                self.save()
            return None
        if not event or event == self.data['last_event']:
            return None
        stopped = event.startswith('stopped_')
        if stopped and self.data['stop_id'] is None:
            self.data['stop_id'] = uuid.uuid4().hex
        self.data['last_event'] = event
        self.save()
        result = {'event': event}
        if stopped:
            result.update(stop_id=self.data['stop_id'], requires_pm_verification=True)
        return result


def watch(args, emit=None):
    env = dict(os.environ)
    env.pop('TMUX', None)
    env.pop('TMUX_TMPDIR', None)
    started = time.monotonic()
    identity = [args.socket, args.target, args.handoff, args.exit_marker]
    events = Events(args.stable_samples, identity, args.state_file)
    while True:
        working = False
        try:
            result = subprocess.run(
                [args.tmux_bin, '-S', args.socket, 'capture-pane', '-p', '-t', args.target],
                env=env, text=True, capture_output=True, timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired):
            event = 'monitor_error'
        else:
            if result.returncode:
                event = 'process_exited' if args.exit_marker and Path(args.exit_marker).is_file() else 'pane_unavailable'
            else:
                event = classify(result.stdout, bool(args.handoff and Path(args.handoff).is_file()))
                working = event is None and bool(FOREGROUND.search('\n'.join(result.stdout.splitlines()[-22:])))
        notification = events.observe(event, working)
        if notification:
            notification['elapsed_seconds'] = round(time.monotonic() - started)
            if not args.follow or event == 'process_exited':
                return notification
            emit(notification)
        if time.monotonic() - started >= args.timeout:
            return {'event': 'timeout', 'state': 'waiting', 'elapsed_seconds': round(time.monotonic() - started)}
        time.sleep(args.poll_seconds)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--socket', required=True, help='Explicit owned tmux socket')
    parser.add_argument('--target', required=True, help='Recorded session or pane target; no discovery')
    parser.add_argument('--handoff', help='Unique current-run handoff path')
    parser.add_argument('--exit-marker', help='Unique current-run exit.json path')
    parser.add_argument('--follow', action='store_true', help='Keep watching after events; emit only transitions')
    parser.add_argument('--state-file', help='External per-run dedup state; no pane text or credentials')
    parser.add_argument('--tmux-bin', default='tmux')
    parser.add_argument('--poll-seconds', type=float, default=5)
    parser.add_argument('--stable-samples', type=int, default=3)
    parser.add_argument('--timeout', type=float, default=1800, help='Total local wait; timeout is not failure')
    args = parser.parse_args()
    if args.poll_seconds <= 0 or args.stable_samples < 1 or args.timeout <= 0:
        parser.error('poll-seconds, stable-samples and timeout must be positive')
    if not os.path.isabs(args.socket):
        parser.error('socket must be an absolute recorded path')
    if args.state_file and not os.path.isabs(args.state_file):
        parser.error('state-file must be an absolute external per-run path')
    try:
        result = watch(args, lambda event: print(json.dumps(event), flush=True))
    except (OSError, ValueError, TypeError, KeyError):
        print(json.dumps({'event': 'monitor_error', 'reason': 'invalid or unwritable monitor state'}), flush=True)
        return 1
    print(json.dumps(result), flush=True)
    return 124 if result['event'] == 'timeout' else 0


if __name__ == '__main__':
    raise SystemExit(main())
