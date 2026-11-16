---
name: codex-dev-team
description: Coordinate one or more Claude Code conversations from a Codex PM conversation to deliver related features or integrate multiple projects. Requires the full sd0x-harness Claude Code plugin in every target project. Use for delegated development, session continuation, and integration acceptance.
---

<!-- SPDX-License-Identifier: MPL-2.0 -->

# Codex Dev Team

Codex owns scope, architecture, dependencies, and acceptance. Claude Code owns implementation, tests, and the project's sd0x-harness review/verify loop. This skill runs in Codex; it is not a Claude Code plugin.

## Start with a bounded mission

Read the project's instructions and current Git state. Preserve existing changes. Determine acceptance criteria, non-goals, allowed paths, interface contracts, and already-authorized external actions. Choose the user's model explicitly; there is no bundled model, effort, quota, or account policy. Check the installed CLI's supported permission modes before choosing one. Never bypass permission checks.

For one project, use one Claude conversation unless distinct ownership justifies more. For work sharing data, contracts, or service dependencies across teams/repos, read [team-coordination.md](references/team-coordination.md). Keep one Codex PM conversation and a separately recorded Claude run per owner; use its canonical data-map, ledger, change-impact, integration and recovery guidance. A small single-repo edit does not require a multi-team ledger or integration document. Do not parallelize conflicting writers. Avoid grouping unrelated projects into one PM context.

Use [mission.md](assets/templates/mission.md) and [handoff.md](assets/templates/handoff.md) when creating task artifacts. Store this skill’s orchestration artifacts outside this skill and product repos; reference project-native review/verify reports at their original workflow-managed locations. For cross-team work only, use the [team ledger](assets/templates/team-ledger.md) and [integration record](assets/templates/integration-record.md), or equivalent existing records. Keep architecture/contracts and durable product handover notes in the appropriate repos, with one canonical shared map owner. The [worked example](references/team-example.md) illustrates this workflow without prescribing a service architecture.

## Required: sd0x-harness

Before **each target project's** development loop, read [harness.md](references/harness.md). Require the full [sd0x-harness](https://github.com/sd0xdev/sd0x-harness) Claude Code plugin (`sd0x-dev-flow@sd0xdev-marketplace`) plus complete project setup and effective rules, hooks, and runners.

Missing readiness permits a **setup-only** run, never product implementation. After installation/setup writes, end that Claude process, start a new one, and verify the settings loaded. If readiness cannot be established, report `setup blocked` with evidence and the specific missing action. Do not substitute skills-only installation, ordinary tests, or another harness. No private companion skill is required: the procedure is bundled here.

## Dispatch and supervise

Read [orchestration.md](references/orchestration.md) before launching, dispatching, monitoring, or resuming. Use the included helpers with explicit repo, model, permission mode, run directory, socket, and recorded session identity.

Remote Control is the normal interactive workflow. Launch without sending the mission; inspect the current session's RC state, model, and empty idle prompt, then dispatch once. A stored URL is not proof of current connectivity. If the user chooses a non-RC run, record that choice with `--no-rc-reason`; do not silently fall back when RC fails.

While Claude is editing, do not edit its owned files or start a competing review loop. Wait using the local event watcher, inspect relevant events, and preserve unsent drafts. A timeout or stopped event is an inspection trigger, not completion. Respect the host's wait limits and keep the user informed without repeatedly polling through model turns. Do not promise background callbacks the host does not provide.

Keep the same recorded Claude conversation for related revisions where possible. Resume only after its previous process has stopped. Never use a guessed ID or `--continue` to select an arbitrary recent conversation.

## Accept the result

Require a fresh handoff, final response, and stopped editing. Read the original harness review and verification evidence, then inspect the resulting diff against the acceptance criteria. Follow the installed harness contracts; required gates must cover the final edits. A hook exiting zero is not a passing review. Report any parent Codex checks separately.

For shared cross-team work, apply the [PM final integration acceptance](references/team-coordination.md#pm-final-integration-acceptance) conditions: reconcile data ownership and write/query/event paths with code, verify adopted contracts and documentation review, and require the integration owner’s record of the exact tested component combination. Include dirty content fingerprints and deployed versions when applicable. On contract changes, retain historical results, mark affected evidence for revalidation, and notify affected owners only at existing safe dispatch points. Before resuming after context loss, reconcile the external ledger with original run/evidence records. Per-project green checks do not close cross-project acceptance. Report local checks, harness review/verify, CI, deployment, runtime readback, and acceptance separately; only require deployment when it belongs to the user's scope.

Send a bounded revision mission when acceptance fails. Do not rewrite evidence, invent successful gates, escalate permissions, or broaden scope to force completion. Preserve active sessions unless stopping them is requested or necessary to prevent an actual unauthorized action.
