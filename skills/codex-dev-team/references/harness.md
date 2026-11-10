<!-- SPDX-License-Identifier: MPL-2.0 -->
# Mandatory sd0x-harness readiness

Upstream: https://github.com/sd0xdev/sd0x-harness. The required plugin ID is `sd0x-dev-flow@sd0xdev-marketplace`. Read its installed version's instructions and the current `claude plugin … --help` before selecting commands. This integration depends on the **full Claude Code plugin**, not the Codex skills-only distribution.

## Read back each target project

From its canonical repo directory, inspect `claude plugin list --json`. Verify the effective enabled record, version, install path, and scope. A project/local record must match this repo; a user-scope record must not be disabled by project settings. A cached installation or a record belonging to another repo is insufficient.

Read `<installPath>/skills/project-setup/SKILL.md` and its verification checklist. Verify the target repo's managed rules, loaded instruction references, executable hooks, hook settings, runners, and installation state against that version. Check required Node, jq, reviewer CLI/auth, and the installed version's health/drift check. File existence alone does not prove loaded behavior. Keep manual optional placeholders distinct from required missing configuration.

Record: repo/HEAD; plugin ID/version/effective scope/path; setup commands and results; managed file paths/hashes; dependencies; health result; process restart and post-restart readback; `ready` or `setup blocked` with a concrete gap.

## Install or repair before development

Use a setup-only mission. Prefer project/local scope; changing a user-wide installation requires that scope to be authorized. Preserve project customizations and overrides.

Typical shell commands, after checking local help:

```bash
claude plugin marketplace add sd0xdev/sd0x-harness
claude plugin install sd0x-dev-flow@sd0xdev-marketplace --scope project
```

Start a new Claude process after plugin installation. Inside Claude Code, run the full `/project-setup` (or its namespaced equivalent shown by the installed plugin). Slash commands belong inside Claude, not the shell. `--lite`, `--no-rules`, and `--no-hooks` do not meet this skill's requirements. Fill missing rules/hooks/runners using that version's official commands.

After **all** setup changes, end the setup run and start another process to read back loaded rules/hooks and effective settings. Resuming a recorded session in a new process is valid; sending keys into the old process is not a restart. Only then dispatch product work.

For existing setups, follow the installed plugin's upgrade procedure and preserve overrides; do not rerun a destructive fresh initialization or assume an `--update` flag exists. Recheck after actual drift. An unchanged continuation does not need repeated upgrades.

Existing task authorization remains valid. Ask only for a missing decision or permission; do not fabricate approval or bypass an actual tool refusal. If install/auth/setup/reviewer readiness fails, retain evidence and report `setup blocked`. Never proceed without the harness or call ordinary tests a substitute.

## Development gates

Claude reads the project's loaded rules, Required Checks, Contract Triggers, and applicable installed contracts. It owns implementation → tests → independent review → fixes/re-review → deterministic verification → authorized delivery → handoff. The installed version determines the precise gates and reviewer fallback conditions.

Completion requires the applicable gates after the final relevant edits. Preserve original reviewer verdicts, runner output and report paths, and the digest-bound state readback. Review hooks can be reminders that exit zero; that is not proof of a verdict. Missing contracts or unavailable reviewers remain unresolved, rather than being replaced with a self-written pass. These are Claude-side results, distinct from the parent Codex acceptance checks.
