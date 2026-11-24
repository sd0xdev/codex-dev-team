<!-- SPDX-License-Identifier: MPL-2.0 -->
# One Codex PM, multiple Claude conversations

Use this workflow when teams share data, contracts, or service dependencies toward one outcome. Multiple conversations alone do not justify it: a small single-repo change uses the existing mission/handoff; unrelated work belongs in separate PM conversations. Reuse existing project records that cover these fields rather than making parallel paperwork.

The runner manages individual runs. Codex coordinates the teams, without an autonomous scheduler, timed LLM heartbeat, or automatic cross-session injection.

## Main conversations and PM delegation

Each independently accountable team has a recorded main Claude conversation that can be opened and resumed separately. Recover that existing identity before creating a new one. Team-internal forks/subagents may assist research and review; cross-team delivery and revisions go through the team's main conversation.

At kickoff, explain the coordination arrangement in one sentence. A single API change, or a second team only checking one field, usually needs direct PM coordination. When API, SDK and Web each have independent work and repeated follow-up, a Codex sub-PM per team can keep the main user conversation available for priorities and cross-team decisions. Use delegation only when supported and permitted by the host; direct coordination is a complete fallback.

- The lead PM owns shared goals, product decisions, dependencies, authorization boundaries and overall acceptance.
- Each sub-PM uses its team's recorded Claude conversation for dispatch, waiting, evidence handoff and bounded product revisions. Claude retains technical implementation/review ownership. Exactly one PM dispatches to a given Claude session at a time.
- Sub-PMs report completed milestones, blockers requiring coordination and decisions affecting other teams, with evidence and next actions. Routine follow-up stays with the responsible sub-PM; no autonomous cross-session message service is introduced.
- Reassigning a PM requires an explicit handover of current run/session, last delivered mission, queued unsent revisions, authorization and next action. Change the ledger's dispatch owner before another PM sends work. User updates stay with the existing team owner unless ownership is deliberately transferred.

## Shared records and ownership

- Keep the PM [team ledger](../assets/templates/team-ledger.md) and [integration records](../assets/templates/integration-record.md), run metadata, missions, and handoffs in an access-controlled task workspace **outside all product repos**. The helper's dedicated `--runs-root` contains only helper-created runs and its socket; keep the ledger and input missions in a sibling directory. Leave project-native harness review/verify reports in their original workflow-managed locations and link to them; do not relocate original evidence or reconfigure a runner just to fit the ledger. Preserve those reports under the project’s existing retention and access rules, without publishing credentials.
- Keep architecture, contracts, and durable product handover notes in their appropriate repos. Find existing documents first; update them, creating missing records only when needed. Select one canonical shared map/table location and maintenance owner. Other teams link to its pinned revision; they do not copy the whole map. Record each team's adopted contract separately from the PM's target contract.
- The ledger indexes original evidence and current pointers; it is not a transcript or a second handoff. It may link to a repo handover note describing design decisions, remaining product work, and validation boundaries. Do not commit runtime routing or machine paths into product notes. Do not store tokens, signed credential values, or credentials in any of these records; describe field names and semantics only.
- One owner per overlapping writable file set, including the shared docs. Serialize overlapping writes; use isolated worktrees only when the user or project instructions select that arrangement, with a named integration owner. Concurrent Git writers must not share a checkout. More sessions do not grant more permissions.

Use [mission.md](../assets/templates/mission.md) and [handoff.md](../assets/templates/handoff.md) for individual teams. Their cross-team sections link to the ledger and canonical docs instead of duplicating them. See the [worked example](team-example.md) for a filled synthetic plan, state transition, and recovery exercise.

## Establish the data map before dispatch

Assign the responsible Claude owners to inspect the actual routes, authorization checks, queries, producers/consumers, and schemas at identifiable revisions. The PM records ownership, product questions and evidence pointers; it does not run a parallel technical document/code review. Compare them with existing architecture docs. Label statements as code-inspected current behavior, proposed change, historical behavior, or runtime-observed behavior with original evidence. Unknown paths remain unknown; do not fill gaps by guessing from service names.

In the shared architecture document, maintain a responsibility table covering:

| Data or contract | Owner team / repo | Authoritative source; raw fact vs projection/cache | Ownership and relation keys; ID meanings | Write/update trigger | Query source and readers | Code revision / evidence |
|---|---|---|---|---|---|---|
| <one record family or interface> | <maintainer> | <source of truth and derived copies> | <tenant, account, device, business key, correlation ID as applicable> | <writer and timing> | <actual store and callers> | <path/symbol at revision; runtime evidence if any> |

Keep diagrams in the same canonical location. Separate these paths (distinct diagrams or labeled edges), adapting the topology to the actual code:

- **Operation/write:** entry → identity acquisition → policy decision → durable write → external side effects. Show transaction/order/failure boundaries where they affect the shared contract.
- **Query:** client → called service → access verification → authorized subject and scope decision → actual database/query source.
- **Asynchronous:** producer → event/queue → consumer → accounting or analytics projection, including lag/idempotency where relevant. If no asynchronous path exists, say so rather than inventing one.

An API entrypoint need not own the data. A projection's existence does not prove the query reads it. A diagram is a representation of verified code, not a required gateway/service layering pattern.

Explicitly reconcile four distinct layers in the table or adjacent notes:

| Layer | What to trace |
|---|---|
| Access eligibility | How token, account, tenant, device/session are validated; rejection cases |
| Query scope | The actual authorized subject and final DB filter, including joins and repository helpers |
| Transport credentials | Which header names, signed claim names, or function arguments carry identity; who verifies/binds them; never record secret values |
| Logging and attribution | Which IDs support tracing, ownership attribution, or filtering; which do not participate in filtering |

For example, validating the current device does not establish a device-only record filter. Inspect code and requirements before deciding whether the document is unclear or behavior must change. Record any disagreement for the owner/user; do not broaden data visibility to make an example fit. Verify both same-account multi-device behavior and cross-account/tenant denial when relevant to the agreed AC.

## Dispatch and keep the ledger current

Agree the shared goal, integration AC, integration owner, canonical document locations/owners and contract target. Record the lead PM, any sub-PM and the sole dispatch owner for each main Claude conversation. Each team records its repo/worktree, baseline and allowed paths, dependencies, adopted contract, current run and actual Claude session/socket/pane, effective harness readiness evidence, selected model/effort and existing authorization. Keep deployment revisions separate from source revisions when deployment is in scope.

Before dispatch, apply [harness readiness](harness.md) per repo and the existing [orchestration](orchestration.md) readback rules. Record last-checked time with timezone and next action. Update the ledger at meaningful events: dispatch/resume, changed contract, new handoff or revision, blocker, verification, and before context handover. These are task events, not a new polling schedule.

Allow parallel development only where ownership and inputs permit it. A labeled fixture can unblock development, but cannot close real integration AC. Owners update their repo's relevant docs and durable handover notes as part of the work. Documentation changes go through that project's existing review loop; the responsible Claude owner and project reviewers check the maps, tables, code, contracts and final revisions together. A code inspection is not a runtime check.

## Capture one tested component combination

The named integration owner creates a uniquely identified integration record for **each actual tested combination**. Freeze the inputs before testing and record:

- Every repo's full commit, and, for any uncommitted content, an identifiable content fingerprint and retained snapshot/patch reference. Include staged/unstaged changes, relevant untracked files, deletions and modes; a dirty boolean, branch name, timestamp or `git diff --stat` is not a content fingerprint. Avoid secrets; if a safe identifiable snapshot cannot be retained, mark the input unreproducible and acceptance open.
- Contract version, canonical doc revisions, environment and relevant configuration revision, plus deployed image digests/versions when applicable. Resolve mutable tags. Link source to the actual artifact; a source commit alone does not prove what ran.
- Required success/error paths, commands or scenario steps, observed result and original evidence, tester and time. Label code inspection, fixture/mock, local execution, real integration, CI, deployment and runtime readback separately. Use `not run` / `not applicable` with a reason rather than blank success claims.

Record completion against that combination, not whichever HEADs the repos have later. If inputs change during testing, preserve the attempt and create a new record for the new combination. Per-team local/review/verify passes never substitute for a real cross-team path. Tests against mocks/fixtures remain development evidence.

## Contract change and selective revalidation

When an upstream contract or shared data assumption changes:

1. Record a change ID, old → new revisions, changed fields/semantics, source evidence, dependencies and affected owners. Separate proposal from adopted/current behavior; do not silently replace the target contract.
2. Map the change to downstream AC/evidence IDs. Mark affected evidence **needs revalidation for the new target**, retaining historical outcomes and their original combinations. Keep unaffected results with an explicit impact rationale; acceptance stays open for missing paths.
3. Queue a bounded revision mission for each affected owner, including the new contract, required doc/code changes and checks. Record queued / delivered / acknowledged (adopted or blocked), timestamp and exact destination. A queued message is not delivery, and delivery is not adoption.
4. Dispatch only at the existing safe points: inspect the recorded idle interactive pane, no unsent draft or background writer; or resume the stopped recorded conversation with fresh readback. Do not inject into a busy session, replay initial one-shot dispatch, or bypass RC/permission choices. Queue the update until safe. Unaffected teams can continue.
5. Each affected owner repairs its work and docs, completes applicable review/verify after final edits, and returns a new handoff with adopted contract and revision. The integration owner runs the impacted paths with a new exact combination. PM links replacement evidence and records why other checks need not rerun. Do not demand a blanket test rerun merely because a contract changed.

## Recover after compaction or handover

1. Read the ledger's current pointers, target contract, open changes, integration records and repo handover notes before taking action. History explains earlier decisions; it is not current evidence.
2. Reconcile each current run with original metadata and handoff: owner, canonical repo/worktree, actual session ID, socket/pane, chosen model and existing permissions. Compare current source/dirty fingerprints, adopted contracts, and relevant deployed versions with the recorded inputs. Resolve conflicts instead of choosing the latest-looking transcript.
3. Read current run status and inspect only its owned pane. A last-checked timestamp, stored readiness report or RC URL does not establish present liveness, loaded settings or connectivity. Recheck effective readiness when repo/setup/process state has changed or is unknown. Preserve an active conversation and drafts; resume the recorded session only after its previous process has stopped, using orchestration's fresh readback. Never guess a session or use `--continue`.
4. Identify the next action for each owner and pending safe delivery. Treat old evidence for changed inputs as historical/needs revalidation. Update the ledger's check time and explicit gaps. If records are missing or contradictory, recover identity/evidence before dispatch; do not recreate a run blindly.

## PM final integration acceptance

The PM checks the agreed user-facing integration scenarios and references the responsible owners’ technical evidence, without adding a second technical review. Close the shared AC only when:

- The current data map/table agree with the final code and adopted contracts; document review is complete under each project's workflow, with unresolved uncertainties stated.
- Relevant owners have stopped editing and provided final-revision handoffs and original harness review/verify evidence. Background work is accounted for.
- Required teams agree on the target contract; pending changes, notifications and revalidation gaps are closed or explicitly excluded by the agreed scope.
- A named integration owner has evidence for the actual component combination and required real success/error paths. Each AC points to evidence applicable to the accepted combination. Affected or superseded historical passes and fixtures cannot close it. Unaffected prior evidence may be reused only through an explicit reviewed impact/applicability rationale linked in the current record; identify reused paths separately from those actually rerun.
- Durable repo notes and external ledger permit recovery of owners, inputs and remaining work. Report local checks, harness gates, code inspection, actual integration, CI, deployment and runtime readback separately. Deployment is only required when in scope.

The user's model/effort, account, environment, RC/non-RC decision, permissions and scope remain authoritative. The PM role is separate from harness-created reviewers. More conversations can increase cost; this workflow promises neither automatic throughput nor broader authorization.
