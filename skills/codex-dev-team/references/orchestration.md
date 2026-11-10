<!-- SPDX-License-Identifier: MPL-2.0 -->
# Run and resume a Claude conversation

Requires macOS or Linux, Python 3.9+, Git, tmux, and an authenticated Claude Code CLI. Check `claude --help` for the requested model, permission mode, RC, and effort support. Models are account-dependent; select an explicit full model ID rather than copying a fixed recommendation. Effort is optional and otherwise follows CLI behavior. The full sd0x-harness setup is required for product development; setup-only runs may precede it.

Use absolute paths. Examples below contain placeholders; resolve them before execution. `H` points into this installed skill, not a product repo.

```bash
H='<skill-dir>/scripts/claude_run.py'
python3 "$H" launch \
  --repo '<project-repo>' --mission '<mission-file>' \
  --model '<full-model-id>' --permission-mode '<supported-mode>' \
  --runs-root '<dedicated-external-runs-directory>' --task-name api
```

Each launch/resume creates a new private directory containing a mission, script, and metadata. `--prepare-only` generates files without starting a process; it is not a queued launch and cannot be resumed as though it had run. Inspect it and issue a new launch when ready. The run directory records the actual socket, session, pane, repo fingerprint, requested settings, and CLI version. Keep these artifacts local: missions, terminal captures, URLs, and logs may contain private project information.

`--runs-root` must be dedicated to helper-created run directories and its socket; put team ledgers and input mission files elsewhere. Keep socket paths short (at most 100 characters). An explicitly supplied socket must be one you own. The helper removes inherited `TMUX`/`TMUX_TMPDIR` and never kills a server.

## Interactive readback before dispatch

Launch creates an interactive RC conversation without submitting the mission. Inspect only its recorded pane using `env -u TMUX -u TMUX_TMPDIR tmux -S '<socket>' capture-pane -p -t '<pane-id>'`. Resolve startup trust/permission prompts within existing authorization. In that conversation, read the current RC panel and model settings. Verify the session identity, active RC connection, actual full model ID, and an empty idle prompt. Close menus before dispatch. Do not clear a user draft or submit a prompt suggestion.

```bash
python3 "$H" dispatch '<run-dir>' \
  --remote-url '<current-session-url>' --actual-model '<observed-full-id>' \
  --confirm-rc-active-and-idle
python3 "$H" status '<run-dir>' --json
```

Dispatch records a PM attestation; it is not an automated RC or model check. Only a trailing `[1m]` difference is normalized; model identity and context capacity are different facts. Dispatch claims the send before pasting, so a partial failure cannot silently replay a mission. If it fails, inspect the pane and dispatch record; never delete the claim and blindly retry. A saved RC URL proves neither current connectivity nor remote-client access.

## Wait for evidence

```bash
python3 '<skill-dir>/scripts/claude_wait.py' \
  --socket '<recorded-socket>' --target '<recorded-pane>' \
  --handoff '<unique-current-handoff>' --exit-marker '<run-dir>/exit.json' \
  --state-file '<run-dir>/wait-state.json' --follow --timeout 1800
```

The watcher is read-only and never sends keys. Its local polling does not call a model; the host's tool handling and Claude's work still consume resources. Use the host's supported background handle and bounded waits, rather than blocking communication for the full timeout.

`attention_required` prompts a bounded inspection. `stopped_*` events carry deduplicated stop IDs but do not prove completion; verify background reviewers/tests, a fresh handoff, final response, and stopped editing. `timeout` (exit 124) means the observation window ended. Reuse the state file for the same run. `pane_unavailable`, `monitor_error`, and `process_exited` require checking the actual run; do not restart automatically. Detection is heuristic and recognizes the harness status line and some native Claude terminal states. Unknown UI formats may time out; inspect once rather than assuming a crash.

## Continue the recorded conversation

If the original interactive process is still idle and healthy, send a bounded revision only after inspecting that exact pane and confirming no draft/background work. The one-shot `dispatch` command is for the initial saved mission. Record later revisions separately; never delete its original dispatch record.

To resume after that process exits:

```bash
python3 "$H" resume --from '<previous-run-dir>' --mission '<revision-file>'
```

The helper inherits recorded model, effort, permission mode, socket, PATH additions, and allowed directories. It rejects a live/prepared prior run and uses the exact recorded session ID. For an unknown prior state, verify no process still owns the conversation before `--ack-unknown-prior`. A resumed RC run needs fresh readback and dispatch. `--setenv` values are not inherited; supply only non-secret settings again if needed. Do not use `--continue` or fork an unrelated session.

When the user chooses non-RC execution, add `--no-rc-reason '<recorded user choice>'` to each launch/resume. This sends the mission in print mode and records stream JSON plus an exit marker. It is not a fallback for failed RC. `exited_ok` means the process completed normally, not that acceptance passed. Interactive processes can remain alive for RC after finishing their work.

Never put secrets in missions, argv, or `--setenv`; its values are saved in `run.sh`. `--path-prepend` affects only this run. The helper refuses `bypassPermissions` and reserved environment overrides. Retain project-native authorization gates. Stop only the owned session when justified; closing a local process does not archive the remote conversation.
