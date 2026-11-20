<!-- SPDX-License-Identifier: MPL-2.0 -->
# Optional stage and quota model selection

Configure once, then let the PM classify each bounded mission and pass `--stage` on launch/resume. Do not repeatedly ask for a model when the user's configuration or explicit choice supplies one. This is local selection at safe run boundaries, not a scheduler, usage collector, or background model switcher. No model IDs, account names, subscription periods, or quota thresholds are built in.

## Classify the work

| `--stage` | Work in this mission |
| --- | --- |
| `research` | Investigate requirements, source code, alternatives, or evidence. |
| `design` | Design or architecture decisions and their documentation. |
| `acceptance` | Execute existing tests, inspect results, and assess acceptance criteria. |
| `development` | Implement or fix code, including adding/modifying tests in the same mission. |
| `test-writing` | Add or modify tests without implementation work. |

For mixed implementation and tests, use `development`. Running tests alone is `acceptance`, not `test-writing`. An acceptance phase in the same session does not create an independent reviewer; keep the project's separate harness review requirements and PM acceptance checks.

## Configure once

Copy [model-policy.example.json](../assets/model-policy.example.json) outside the skill and product repos. Replace its placeholder IDs with full IDs available in your account. This minimal configuration disables quota handling; individual stage entries may be omitted. There is no default policy file discovered from a product repo.

```bash
export CODEX_DEV_TEAM_MODEL_POLICY='/absolute/private/path/model-policy.json'
```

Alternatively, pass `--model-policy '/absolute/private/path/model-policy.json'`. The resolved path is recorded, not the entire configuration. Resume selects the policy path in this order: explicit flag, previous run's recorded path, environment variable. The file is read again for each launch/resume, so edits apply to the next run. Use an explicit flag to move an existing session to another policy. `--no-model-policy` bypasses policy loading for this invocation; a subsequent resume can still opt in via the environment. An absent recorded policy in an old run is supported.

Selection priority is **this invocation's `--model` > enabled matching quota rule > current stage's model > legacy behavior**. Legacy launch requires an explicit model; legacy resume inherits the prior requested model. Explicit overrides are per invocation: a later configured stage can select another model. `--stage` is not inherited, since an old research phase must not silently classify a new development mission. The PM supplies the stage from current scope. With no stage, a matching quota rule can still apply; otherwise resume keeps the prior model.

An explicitly configured but missing/malformed policy fails with `MODEL_POLICY_INVALID`, including when `--model` is supplied: fix it or deliberately bypass it with `--no-model-policy`. This differs from missing usage observations, which are expected and fall back. Unknown configuration keys fail validation to catch typos. The policy only selects a model; it cannot change effort, permissions, account authentication, allowed directories, RC choice, or authorization.

## Optional quota rule

Replace the `quota` object with one of these user-selected strategies. All numbers below are examples, not account defaults:

```json
{
  "enabled": true,
  "strategy": "projected_exhaustion",
  "snapshot_path": "usage.json",
  "max_age_seconds": 3600,
  "fallback_model": "your-quota-pressure-model-id",
  "projected_fraction_threshold": 1.0,
  "min_elapsed_seconds": 3600
}
```

`projected_exhaustion` estimates end-of-period usage as `used_fraction × (resets_at − period_start) / (observed_at − period_start)`. It matches when the estimate is at least `projected_fraction_threshold`. `min_elapsed_seconds` optionally avoids decisions very early in a period (default zero). An observation exactly at period start is unknown. Use the observation time for elapsed consumption, not the later decision time; time passing alone does not imply consumption slowed down. Linear extrapolation is a heuristic, not a guarantee of future usage.

For a fixed usage threshold instead:

```json
{
  "enabled": true,
  "strategy": "usage_threshold",
  "snapshot_path": "usage.json",
  "max_age_seconds": 3600,
  "fallback_model": "your-quota-pressure-model-id",
  "used_fraction_threshold": 0.8
}
```

Use only the threshold fields for the selected strategy. Enabled rules require a strategy, snapshot path, positive freshness window, fallback model ID, and the corresponding threshold. Fractions are numbers from 0 to 1; a projected threshold may exceed 1. Set `"quota": {"enabled": false}` to stop reading usage entirely.

The snapshot is a local JSON file produced manually or by an already-authorized source. Relative paths resolve against the policy file's directory. No credentials, private usage APIs, shell commands, or automatic polling are involved. Use atomic replacement when updating the file. Example observation:

```json
{
  "scope": "shared",
  "used_fraction": 0.6,
  "period_start": "2030-01-01T00:00:00Z",
  "observed_at": "2030-01-03T00:00:00Z",
  "resets_at": "2030-01-08T00:00:00Z"
}
```

Dates are synthetic; replace them with the actual observed period and timezone-aware timestamps. `scope` is `shared` for quota shared across the candidate models, or `model` for a model-specific quota. The operator must identify which quota the snapshot represents and whether the fallback has separate capacity; selection never proves model availability. Supply only these observations, never a token, cookie, or raw account response.

With this seven-day example, 60% at two elapsed days projects to 210% and matches a threshold of 1.0; 60% at six elapsed days projects to 70% and does not. Both snapshots must be fresh at their respective decision times. The period comes entirely from the timestamps, not a hard-coded week.

Missing, malformed, future-dated, expired, or already-reset observations have `quota.state=unknown` and fall back to the stage rule (or legacy behavior). A **fresh shared quota at 100% stops before launch/resume with `SHARED_QUOTA_EXHAUSTED`**, even with an explicit model. This is an availability preflight, separate from model precedence: changing the model does not restore exhausted shared capacity. Report the observation and await a reset or corrected authorized information. Do not disable the policy merely to work around exhaustion. Model-scoped pressure can select the configured fallback but still does not prove it has capacity.

A personal configuration might map research/design/acceptance to **Fable 5.2**, development/test-writing to **Opus 5.5**, and projected exhaustion to **Opus 5.5** for every non-explicit stage. These display names are an example only: obtain the actual IDs available to that user and substitute them in the JSON. The open-source implementation does not encode either name, a weekly cycle, or any personal quota rule.

## Same-session continuation

Use the existing [orchestration procedure](orchestration.md) and readiness checks. Resolve placeholders before executing:

```bash
H='<skill-dir>/scripts/claude_run.py'
python3 "$H" launch --repo '<project-repo>' --mission '<research-mission>' \
  --runs-root '<dedicated-external-runs-directory>' --task-name feature \
  --permission-mode '<supported-mode>' --effort '<supported-effort>' \
  --model-policy '<absolute-policy-file>' --stage research
# Read back actual model + RC and dispatch; wait for work and process exit.
python3 "$H" resume --from '<research-run-dir>' \
  --mission '<implement-and-add-tests-mission>' --stage development
# Fresh readback + dispatch; wait for work and process exit again.
python3 "$H" resume --from '<development-run-dir>' \
  --mission '<separate-acceptance-mission>' --stage acceptance
```

All three runs use the original recorded Claude session ID, with the policy selecting a model afresh at each boundary. Resume still inherits effort, RC mode, permissions, socket, and allowed directories. A non-RC user choice must still be recorded with `--no-rc-reason` on every run. Do not resume a live or prepared run. For a stage change while the old process is idle, first confirm no draft/background work and close only that owned process when necessary; then use recorded-session resume and fresh readback. Never inject `/model`, restart an active writer, or silently switch models within a live conversation. Ordinary revisions that keep the current model can follow the existing safe idle dispatch procedure.

`meta.json`, command output, and `status --json` expose `model_selection`: stage, source (`explicit`, `quota`, `stage`, `previous_run`), resolved policy path/digest, evaluation time, and safe quota observations/digest when available. The selected model remains `requested_model` in metadata. Dispatch still requires the actual full model ID read from the current session; policy output is not actual-model evidence. Keep these local records out of public commits.

## Offline validation and limits

`test_model_policy.py` uses custom IDs and a fake Claude executable that serves only help/version. Its same-session fixture checks `custom-thinker-r1 → custom-coder-d2 → custom-review-a4`, inherited effort/RC/permissions, exact `--resume` identity, and fresh dispatch attestation rejecting a wrong model. Additional tests cover priority, both strategies, all stages, unknown/stale data, shared exhaustion, no configuration, old metadata, policy changes, and live/prepared guards.

These are offline runner regressions, not real Claude sessions, independent harness review, quota-account integration, or multi-service E2E. Actual model availability, switching support in the installed CLI, RC connection, and paid execution require runtime readback in the user's environment.
