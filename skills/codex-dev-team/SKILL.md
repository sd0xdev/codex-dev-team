---
name: codex-dev-team
description: Coordinate one or more Claude Code conversations from a Codex PM conversation to deliver related features or integrate multiple projects. Requires the full sd0x-harness Claude Code plugin in every target project. Use for delegated development, session continuation, product/integration acceptance, and requested archive of its recorded conversations.
---

<!-- SPDX-License-Identifier: MPL-2.0 -->

# Codex Dev Team

Codex is the product PM: it owns user scenarios, business rules, scope, priorities, constraints, dependencies and product acceptance. Claude Code owns architecture, implementation, tests and the project's sd0x-harness review/verify loop. This skill runs in Codex; it is not a Claude Code plugin.

## Start with a bounded mission

Read [product-acceptance.md](references/product-acceptance.md) when defining scope/AC, writing revisions or accepting delivery. Specify observable outcomes and hard boundaries rather than algorithms, refactors or review round counts. Do not add a competing code/document review loop. Read the project's instructions and current Git state. Preserve existing changes. Determine acceptance criteria, non-goals, allowed paths, interface contracts, and already-authorized external actions. Honor the user's explicit model or optional local stage/quota policy; there is no bundled model, effort, quota, or account policy. For configured selection, read [model-selection.md](references/model-selection.md), classify each mission, and pass its stage without repeatedly asking the user. Running existing tests is acceptance; writing tests alone is test-writing; implementation plus tests is development. Check the installed CLI's supported permission modes before choosing one. Never bypass permission checks.

Briefly state who coordinates each team and why. For one project, use one Claude conversation unless distinct ownership justifies more. Recover each team’s existing main Claude conversation first; create a separately resumable conversation only if missing. Internal research/reviewer subagents do not replace that delivery owner. When independent teams need substantial follow-up and the host permits delegation, use one Codex sub-PM per team; otherwise coordinate directly. Keep one dispatching PM per Claude session and record handovers. For work sharing data, contracts, or service dependencies across teams/repos, read [team-coordination.md](references/team-coordination.md). Keep one Codex PM conversation and a separately recorded Claude run per owner; use its canonical data-map, ledger, change-impact, integration and recovery guidance. A small single-repo edit does not require a multi-team ledger or integration document. Do not parallelize conflicting writers. Avoid grouping unrelated projects into one PM context.

Use [mission.md](assets/templates/mission.md) and [handoff.md](assets/templates/handoff.md) when creating task artifacts. Store this skill’s orchestration artifacts outside this skill and product repos; reference project-native review/verify reports at their original workflow-managed locations. For cross-team work only, use the [team ledger](assets/templates/team-ledger.md) and [integration record](assets/templates/integration-record.md), or equivalent existing records. Keep architecture/contracts and durable product handover notes in the appropriate repos, with one canonical shared map owner. The [worked example](references/team-example.md) illustrates this workflow without prescribing a service architecture.

## Design and skill selection

For UI/UX or visual work, default to Claude as designer; the PM preserves user requirements and hard constraints. Codex leads the visual brief only when the user chooses that role. An optional design preference question does not block work or expand implementation/deployment permission. Read [visual-design.md](references/visual-design.md) for design resets and optional asset handoff, including immutable revisions and engineering receipt.

Before suggesting a Claude skill, read [claude-skill-guide.md](references/claude-skill-guide.md) and verify availability in the target conversation. The actual project harness owns technical gate selection. There is no private companion-skill dependency.

## Required: sd0x-harness

Before **each target project's** development loop, read [harness.md](references/harness.md). Require the full [sd0x-harness](https://github.com/sd0xdev/sd0x-harness) Claude Code plugin (`sd0x-dev-flow@sd0xdev-marketplace`) plus complete project setup and effective rules, hooks, and runners.

Missing readiness permits a **setup-only** run, never product implementation. After installation/setup writes, end that Claude process, start a new one, and verify the settings loaded. If readiness cannot be established, report `setup blocked` with evidence and the specific missing action. Do not substitute skills-only installation, ordinary tests, or another harness. No private companion skill is required: the procedure is bundled here.

## Dispatch and supervise

Read [orchestration.md](references/orchestration.md) before launching, dispatching, monitoring, or resuming. Use the included helpers with explicit repo, permission mode, run directory, socket, and recorded session identity. Select the model via this run’s explicit override, a configured quota rule, or stage mapping, in that order. With no applicable policy, launch requires a model and resume inherits the prior choice. Model changes use a safe stopped-process resume boundary and fresh actual-model readback.

Remote Control is the normal interactive workflow. Launch without sending the mission; inspect the current session's RC state, model, and empty idle prompt, then dispatch once. Share the current session URL before sending the mission. A stored URL is not proof of current connectivity or that the user has opened it. If the user chooses a non-RC run, record that choice with `--no-rc-reason`; do not silently fall back when RC fails.

While Claude is editing, do not edit its owned files or start a competing review loop. Wait using the local event watcher, inspect relevant events, and preserve unsent drafts. A timeout or stopped event is an inspection trigger, not completion. Respect the host's wait limits and keep the user informed without repeatedly polling through model turns. Do not promise background callbacks the host does not provide.

Keep the same recorded Claude conversation for related revisions where possible. Resume only after its previous process has stopped. Never use a guessed ID or `--continue` to select an arbitrary recent conversation.

## Accept the result

Require a fresh handoff, final response, stopped editing and finished background work. Accept through the agreed product entry point: record preconditions, actions, expected and observed results at the delivered version. Reference original harness review/verify evidence for technical readiness; missing evidence returns to the original owner. Follow applicable repo rules without inventing another PM review loop. A hook exiting zero is not a passing review, and a Claude-side pass is not a parent-runtime pass.

For shared cross-team work, apply the [PM final integration acceptance](references/team-coordination.md#pm-final-integration-acceptance) conditions: have the responsible Claude owners reconcile data ownership and write/query/event paths with code, use their final-revision contract/document review evidence, and require the integration owner’s record of the exact tested component combination. Include dirty content fingerprints and deployed versions when applicable. On contract changes, retain historical results, mark affected evidence for revalidation, and notify affected owners only at existing safe dispatch points. Before resuming after context loss, reconcile the external ledger with original run/evidence records. Per-project green checks do not close cross-project acceptance. Report local checks, harness review/verify, CI, deployment, runtime readback, and acceptance separately; only require deployment when it belongs to the user's scope.

Send a bounded revision mission when acceptance fails. Do not rewrite evidence, invent successful gates, escalate permissions, or broaden scope to force completion. Preserve active sessions unless stopping them is requested or necessary to prevent an actual unauthorized action.

## Retain or archive the conversation

Keep a completed idle RC conversation available for the user by default, with its recorded name and current URL. Closing a process is not remote archive. When the user requests archiving, follow [remote-archive.md](references/remote-archive.md); verify the same remote target and preserve history. This maintenance path does not launch development or rerun harness setup.
