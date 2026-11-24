<!-- SPDX-License-Identifier: MPL-2.0 -->
# Mission: <component/task>

## Shared objective and acceptance

- Outcome and observable acceptance criteria (preconditions → user action → expected result, environment and evidence):
- Non-goals:
- Contract/schema revision and dependencies:

## Ownership and permissions

- Repo/selected worktree and baseline branch/HEAD/dirty/index/stash state:
- Lead PM / team dispatch owner / existing main Claude conversation:
- Allowed files; other active owners and excluded paths:
- Authorized external actions (commit/push/deploy only if applicable):
- Chosen model/effort and supported permission mode:

## Harness and execution

- Mode: setup-only or scoped task. Authorized stage/deliverable: research / design / prototype / implementation / acceptance (select only what is authorized).
- Effective sd0x-harness version/scope and readiness evidence:
- Read this project's loaded rules and applicable installed contracts.
- Product work requires ready harness; do not change product code during setup-only work.
- Deliver only the authorized stage. For implementation work, choose architecture, code and tests within the agreed product constraints; research/design does not authorize implementation. Complete applicable project gates after final relevant edits and before any delivery action that those gates govern. Perform only authorized delivery, then stop editing and hand off. The PM does not prescribe algorithms or additional review rounds.
- Report contract changes to the PM before downstream integration. Preserve other owners' files.

## Evidence and delivery

- Required behavior/contract/integration checks:
- Unique handoff path outside product repos:
- Exact component revision, changed paths, original gate evidence, blockers, and downstream inputs:

## Shared-team work only (omit for a small single-repo task)

- External team ledger / team entry / shared AC IDs:
- Canonical responsibility table and write/query/async maps: location, maintenance owner, revision (reuse existing docs):
- Contract target and this team's adopted version; upstream/downstream owners:
- Data/ID semantics and access-vs-query-scope questions to resolve by code inspection:
- Docs and durable product handover notes this owner must update in its repo:
- Integration owner / required inputs and impacted real success/error paths:
- Report contract changes with old/new revision and affected evidence; wait for PM-coordinated adoption. Do not expand visibility or permissions to fit an example.
- Review updated docs through this project's existing loop, checking code, maps, tables and contract at final revisions. Return original evidence and distinguish code inspection from runtime results.
- Do not copy the shared plan into this mission; link to the relevant entries and record only this team's assignment.

## Design/assets only (omit when irrelevant)

- Designer: Claude by default, or user-selected Codex-led brief; choice/evidence:
- Stage deliverable and authorization: research / design / prototype / implementation / deployment:
- User requirements and hard constraints (separate from PM suggestions):
- Assigned asset producer / engineering consumer / disjoint staging and product paths:
- Immutable READY manifest revision/hash and expected receipt/runtime evidence, if using an asset set:
