<!-- SPDX-License-Identifier: MPL-2.0 -->
# One Codex PM, multiple Claude conversations

Use multiple conversations for related components with distinct ownership, such as a web app, API service, and SDK implementing one feature. The included runner manages individual runs; Codex maintains the team plan. There is no autonomous fleet scheduler or automatic cross-session messaging.

## Shared plan and ownership

Keep a team ledger outside the product repos containing:

| Field | Purpose |
|---|---|
| Objective and acceptance criteria | One shared integration outcome |
| Contract revision | Schema/API document or commit all consumers must use |
| Owner and repo/worktree | One writer per overlapping file set |
| Allowed paths and non-goals | Prevent accidental overlapping work |
| Dependencies | What must finish before this owner starts or integrates |
| Run directory, session ID, socket, pane | Route actions to the right conversation |
| Harness readiness | Effective version and evidence for this project |
| Model/effort and authorization | Explicit choices and allowed external actions |
| Handoff and verified component revision | Inputs to integration acceptance |
| Next action/blocker | Recover the plan after context compaction |

Use the existing checkouts when ownership is disjoint. If two workers must change overlapping files, serialize them or use isolated worktrees with an explicit integration owner. Do not assign the same checkout to concurrent Git writers. Extra sessions do not grant extra permissions.

## Example: web + API + SDK

1. Codex agrees the request/response schema, authentication behavior, error contract, and an end-to-end acceptance scenario with the task requirements.
2. Claude API owns the service and its tests. Claude SDK owns generated/client code and contract tests. Claude Web owns the UI and user-visible states. Each project passes its own harness readiness before implementation.
3. Parallel work starts only where contracts and write ownership are stable. A consumer waiting for an API change can use a clearly labeled fixture; a fixture is not integration evidence.
4. An API contract change returns to Codex. Codex records the revision and sends a targeted update to affected conversations; one worker cannot silently redefine another worker's input.
5. Each Claude completes its harness loop, records its exact revision and handoff, and stops editing.
6. A designated integration owner wires those revisions into an isolated test environment. Codex checks the real web → SDK → API path, including error cases required by the mission. Failures return to the responsible conversation and invalidate affected downstream evidence.

Do not declare the feature complete because all three conversations said “done.” Record component checks and integration checks separately. Independent work may continue if another component is blocked, but the shared acceptance remains open.

## Coordination boundaries

- Send another conversation only the relevant contract, findings, and paths; do not duplicate entire histories or expose credentials.
- Separate a task's Claude developer from harness-created reviewer conversations. “One Codex PM” does not mean the harness stops using its own independent Codex reviewer.
- Choose concurrency from the user's machine capacity and budget. More sessions can increase cost and coordination work; there is no automatic throughput guarantee.
- For unrelated objectives, prefer separate Codex PM conversations so acceptance criteria and decisions remain focused.
