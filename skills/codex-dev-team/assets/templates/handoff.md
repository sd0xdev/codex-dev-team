<!-- SPDX-License-Identifier: MPL-2.0 -->
# Handoff: <component/task>

- Run/session and repo/worktree:
- Final HEAD and any uncommitted changes:
- Editing stopped; remaining background work:
- Shared contract revision:

| Acceptance criterion | Evidence | Result or gap |
|---|---|---|
| | | |

## Change and validation

- Changed files and behavior:
- Effective harness readiness/version:
- Independent review verdict, original report, and final-edit digest:
- Verify/precommit command, output, and report:
- Tests and cases not exercised:
- CI / deployment / runtime readback (each separately, or not requested/not run):

## Integration handoff (shared-team work only; otherwise omit)

- External ledger / team entry / integration record ID (if tested):
- For integration inputs, clean state or dirty content fingerprint (algorithm/scope and retained patch/snapshot, including relevant untracked content):
- Inputs or exact versions other components should use; adopted contract vs PM target:
- Contract changes and affected owners:
- End-to-end checks completed and still pending:
- Remaining blockers and required decisions:
- Updated canonical docs and durable repo notes: paths/owners/revisions; original review evidence covering final edits:
- Data ownership / write/query/async discrepancies resolved or still open; access eligibility vs query scope evidence:
- Affected AC/evidence IDs needing revalidation; preserved historical results / replacement pointers:
- Deployment version or image digest and source mapping when in scope; otherwise not applicable:
- Next owner/action and pending safe notification; distinguish delivered from acknowledged adoption:

Link to the original integration record for tested combinations rather than copying its matrix. Per-team checks do not close shared AC. A changed source, contract or environment does not inherit an old integration pass automatically.
