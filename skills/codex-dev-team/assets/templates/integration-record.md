<!-- SPDX-License-Identifier: MPL-2.0 -->
# Integration record: <unique attempt / combination ID>

Store outside product repos. One actual tested input combination per record; preserve prior attempts. This template is not needed for unrelated work or an ordinary single-repo edit.

- Ledger / shared AC reference (do not repeat the full plan):
- Integration owner / tester / started and ended at (timezone):
- Contract revision / canonical schema and data-map document revisions:
- Environment / relevant configuration revision:
- Evidence class: code inspection / fixture / local execution / real cross-service integration (state exactly what ran):
- Previous record / triggering change ID (if any):

## Exact inputs

| Team / repo | Full commit | Clean or dirty content fingerprint + retained snapshot/patch reference | Deployed image digest / version and source mapping (if applicable) | Original handoff / final-edit review + verify evidence |
|---|---|---|---|---|
| | | | | |

A dirty fingerprint identifies staged/unstaged content, relevant untracked files, deletions and modes. Record its algorithm and file scope, not just a dirty flag. Do not retain secrets. If input identity cannot be established, leave acceptance open. Resolve mutable deployment tags and verify actual running versions when in scope.

## Scenarios and original evidence

| AC / case ID | Required path and success/error inputs (no credentials) | Command or steps / actual endpoint or store | Observed result: pass / fail / not run | Original evidence / time | Applicability: current / historical / needs revalidation, with reason |
|---|---|---|---|---|---|
| | | | | | |

- Relevant access eligibility vs authorized query scope and actual DB filter evidence:
- Fixture/mock boundaries; unexercised paths and why:
- Code-inspected facts vs runtime-observed facts:
- CI / deployment / runtime readback: separate evidence or not run / not applicable with reason:
- Docs reviewed against these inputs; original review evidence:

## PM decision and follow-up

- Shared AC satisfied / still open, each linked to evidence:
- Blockers / responsible owner / next action:
- Superseded by / affected AC and evidence requiring revalidation / change ID:
- Unaffected prior evidence reused: original combination/case IDs, reviewed applicability rationale for this combination, reviewer/evidence; separate from paths actually rerun:
- Accepted combination and scope / PM / decision time (or pending):

Changed inputs require a new record. Preserve original outcomes when applicability changes. Per-team green checks, a stop event, and a successful process exit do not establish cross-team acceptance.
