# Product PM workflow validation

Date: 2026-11-24. Release target: v0.4.0, based on v0.3.0 (`4414cad`). Scope: product acceptance, team/PM ownership, design/assets, skill routing, requested remote archive, and CLI permission capability checks. This is **an independent document walkthrough plus offline regression/packaging validation**, not a live Claude/RC run, remote archive, product integration or harness gate execution.

## Curated public behavior

The entrypoint and mission/handoff/ledger now separate product decisions from Claude's technical loop. Additional references cover product acceptance, optional design/assets, loaded Claude skill selection and requested remote archive. Team coordination keeps the existing canonical data maps, selective revalidation and exact tested combinations; responsible Claude owners perform technical reconciliation and reviews while the PM checks product scenarios and evidence applicability.

The runner adds only permission-mode capability validation and metadata; the waiter and configurable model-policy resolver are unchanged. Public models, effort, accounts, subscription periods and quota thresholds remain user-controlled. There is no personal account prefix, fixed waiting-round policy, private companion dependency, new scheduler or automatic cross-session injection. Media tooling is selected from available authorized tools. Historical field notes and private project examples were not imported.

The public sd0x-harness README/catalog was checked on this date for full-plugin installation, project setup and candidate skill names. Target sessions still need their installed-version readiness readback; an upstream catalog or cached skill is not proof that a particular session loaded it.

## Independent scenario walkthrough

| Scenario | Observed instruction outcome |
|---|---|
| API/SDK/Web already have main Claude sessions; Web has an unsent draft | Recover each identity, name one dispatching PM per team, queue the Web update without touching the draft, and deliver only at an existing safe point. Sub-PMs report milestones/blockers/cross-team decisions to the lead PM. |
| SDK sub-PM handover | Transfer current run/session, last delivered mission, queued work, existing authorization and next action; update sole dispatch ownership before the successor sends. No competing PM injection. |
| Design-only redesign, then “start over,” with asynchronous assets | Default Claude designer; replace superseded directions while retaining history and scope. No implied implementation or deployment. Asset producer/consumer use disjoint paths and immutable READY revisions with separate receipt/runtime acceptance. |
| Tests pass but a product scenario fails; repo requires a parent-runtime gate | Keep AC open, send expected/observed behavior to the original Claude owner, and use the required native gate executor at its required snapshot stage. Do not create a duplicate PM technical review or relabel another runtime's pass. |
| Archive requested, only local exit evidence exists | Remote archive remains unconfirmed. Verify exact target using available supported controls; preserve history. Do not resume merely to verify an already-confirmed archive. |
| Unsupported permission mode, unrecognized help, or old-run resume | Fail before new run creation; never choose another mode automatically. Resume checks current CLI support while preserving model policy, effort and session semantics. |

The independent evaluator identified an unconditional implementation instruction and ambiguous gate/delivery order in the mission template. The corrected template explicitly selects research/design/prototype/implementation/acceptance scope, conditions implementation on authorization and requires applicable gates before the delivery they govern. Focused rereview confirmed the finding resolved, with no remaining actionable findings. This review was performed by a separate Codex agent under skill-authoring validation, not by pretending to run a target product's Claude harness.

## Deterministic checks

- 64 offline runner/waiter/model-policy tests passed, including four new permission-capability regressions. Fixtures cover wrapped help, option isolation, unsupported and unrecognized help, no launch/fallback, resume capability drift and supported choice retention.
- Existing RC-unsupported and effort-unsupported tests were adjusted to exercise their intended errors after adding permission preflight. Existing custom-ID policy and same-session tests still pass.
- 7 installer tests passed. An isolated packaged installation verified dry-run, fresh/repeat install, overwrite refusal, update preview and backup preservation; all 23 packaged files' SHA-256 hashes and executable bits match source.
- Skill validator, relative Markdown target checks and `git diff --check` passed. No tests were added merely to match prose/headings.
- Claude Code 2.1.331 help was inspected locally and exposes wrapped permission choices. This does not establish any account capability or live session result.

CI and clean installation from the published tag must be verified separately at release time and linked in the release notes. Installation checks use temporary skills roots; no maintainer's installed private skill is replaced.

## Limits

No paid model run, live sub-PM dispatch, RC connection, remote archive, media generation/import, application runtime, or target-project harness gate was executed. These procedures preserve the required evidence boundaries rather than claiming those outcomes. A CLI with an unrecognized help format now stops with `PERMISSION_MODE_UNVERIFIED`; inspect that version before extending the parser, rather than assuming or silently changing permissions.
