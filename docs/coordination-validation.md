# Coordination documentation validation

Date: 2026-11-16. Scope: shared-team instructions/templates and the synthetic activity example, based on `main` at `30b67dd`. This is a **document walkthrough plus offline tooling validation**, not a real multi-service E2E, paid Claude run, live RC check, or harness gate execution.

## Scenario walkthrough

The [worked example](../skills/codex-dev-team/references/team-example.md) supplies fictional owners, clean full commits, run identities, evidence pointers and transitions. None of its fictional success results is runtime evidence. The procedure was also read independently by a separate Codex reviewer using the skill's reference routing, without starting services or dispatching any session.

| Scenario | Procedure exercised and concrete decision | Document walkthrough result |
|---|---|---|
| Web / SDK / API with a fixed contract | Adopt v1 independently per team; API owns the canonical docs and integration workspace. I-01 freezes A1/S1/W1 and local environment; AC-1/2/3/4 require real pagination, scope/denial, cursor-error and async evidence. Fixture/component passes leave shared acceptance open. | Operable on paper; runtime not run |
| API changes mid-task | CH-01 targets v2; SDK/Web remain at adopted v1 until acknowledged. SDK's stopped process resumes the recorded session into a new run with fresh readback. Web's busy session receives no injection; update stays queued. AC-1/3 need revalidation; AC-2/4 require reviewed no-impact applicability if reused. I-02 pins A2/S2/W2; I-01 history is retained. | Operable on paper; notifications and tests not executed |
| One account, multiple devices | Trace device eligibility separately from authenticated tenant/account DB filters, header/claim binding and attribution. Same-account device B records are visible only because the example explicitly agrees that policy; an actual device filter disagreement returns to the owner rather than being removed. | Distinctions and escalation are explicit; no live authorization test |
| Small single-repo edit | Ordinary mission/handoff and the repo's existing gates; omit shared-team sections, ledger and integration artifacts. | Lightweight route preserved |
| Resume after compaction | Read target v2 and current sdk-02, not sdk-01; verify metadata and source state. Web remains W1/v1 with queued CH-01 and I-02 pending. Preserve an unsent draft, verify liveness/readiness, then use the exact recorded conversation at a safe point. | Recovery can identify owner, session, version and next action; live recovery not run |

## Review and correction

Independent review identified ambiguous wording: “historical passes cannot close” acceptance conflicted with selective reuse of unaffected evidence. The final rule distinguishes affected/superseded results from prior evidence explicitly reviewed as applicable to the new combination. The current integration record must link the original combination/case IDs and the reviewed rationale, separately from paths actually rerun. This avoids both blind reuse and unnecessary full reruns.

A second independent finding clarified evidence storage: external orchestration records must not require moving project-native harness reports. The instructions now retain those original reports in their workflow-managed locations and link to them, preserving the existing review process.

PM review also kept dirty-content fingerprints inside the shared-team integration section of the handoff, so a small ordinary edit does not acquire a new integration snapshot requirement. The user-selected model/effort, authorization, RC/non-RC choice, resume identity, one-shot initial dispatch and single-writer rules remain unchanged. No runner, waiter, permission policy or automatic messaging service changed.

## Deterministic validation

Run the existing suites from the repo root:

```bash
python3 -m unittest discover -s skills/codex-dev-team/scripts -p 'test_*.py'
python3 -m unittest discover -s tests -p 'test_*.py'
```

Observed locally: **43 runner/waiter tests and 7 installer tests passed**. These use synthetic CLI/tmux fixtures. No tests were added that merely assert document headings or phrasing.

Codex's available `skill-creator/scripts/quick_validate.py` accepted the revised skill. Its PyYAML dependency was installed in a temporary validation environment; no new runtime dependency was added to this repo. Frontmatter validation does not prove workflow behavior.

An isolated installation check installed the baseline package, added a synthetic local customization, and exercised overwrite refusal, explicit update dry-run, update with preserved backup, fresh install and idempotent reinstall. All 15 packaged files and executable bits matched the revised source, including the new templates/example. No installed private skill was changed. Relative Markdown links, the acceptance anchor, license notices and `git diff --check` were checked separately.

CI must be checked on the exact pushed commit; a local pass is not CI evidence. This report does not claim deployment, production behavior, or a new release. `VERSION` and release tags remain unchanged; the changelog entry is Unreleased.

## Coverage limits

- No real Web/SDK/API services, queue, multi-device auth flow or deployed image was executed. The example's version IDs and paths are synthetic.
- No actual Claude startup, RC connection, safe revision delivery or conversation recovery was performed. Existing offline protections were regression-tested.
- No project-specific diagram/code equivalence or sd0x-harness review/verify gates were executed against a product repo. The skill now requires those checks when used there; this documentation repo has no loaded project harness workflow.
- Dirty snapshot and deployment-source mapping are required fields/procedures, not new automated capture or validation tooling. Their completeness remains the integration owner's responsibility.
