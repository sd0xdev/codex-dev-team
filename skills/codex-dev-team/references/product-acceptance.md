<!-- SPDX-License-Identifier: MPL-2.0 -->
# Product PM scope and acceptance

The PM owns the outcome, business rules, boundaries, priorities and user decisions. Claude and the project's harness own architecture, implementation, technical tests, review, repairs and authorized delivery. The PM does not prescribe algorithms, refactors or review round counts, or add a competing code/document review loop. Existing mandatory repository checks still apply and cannot be waived by this role split.

## Define the mission

Read authoritative requirements and the repo baseline first. Record the goal, non-goals, hard data/privacy/compatibility constraints, cost limits, existing authorization and expected evidence. Write each acceptance criterion as a precondition, user action and observable result. Identify the intended environment and delivery stage. A research/design request is not permission to implement or deploy.

Use the [mission template](../assets/templates/mission.md). Let Claude choose the technical route and the installed harness choose applicable gates. A missing decision that changes product behavior or a real permission gap needs clarification; already-granted task authorization does not need repeated approval. Preserve current checkout changes, index and stash; creating a new run directory does not require a new worktree. Prefer the user's existing checkout. Create a worktree only when the user or project instructions select that arrangement; otherwise serialize conflicting Git writers.

For technical skill suggestions, use [claude-skill-guide.md](claude-skill-guide.md). For design/asset ownership, use [visual-design.md](visual-design.md).

## Accept through the product entry point

Wait for the final response, fresh handoff, stopped editing and completed background work. Exercise the agreed user scenarios in the identified environment/version. Compute expected results independently from business rules where necessary. For example, a notification and later finalized record for one purchase must count once if that is the agreed rule; Claude chooses how to correlate the records and test it.

Reference the original harness review/verify evidence for technical readiness. If evidence is missing, send the gap to the original Claude owner rather than inventing a pass or starting another technical review. Check that evidence applies to the delivered revision. Product acceptance is separate from local tests, review, verify, CI, deployment and runtime readback; deployment is required only when in scope.

Return a bounded revision with reproducible steps, expected versus observed behavior, affected AC and evidence. Claude diagnoses and repairs it in the recorded conversation; the PM rechecks affected product scenarios after the new handoff. Do not take over the code or demand a new gate unrelated to the project's rules.

## Cross-runtime responsibilities

Identify who can execute any mandatory parent-runtime gate before work starts. If a native gate requires an uncommitted snapshot, have Claude freeze the workspace and stop editing before that executor runs it, then continue authorized delivery in the same recorded Claude session. This is compliance with an existing gate, not an additional PM review loop. Never substitute a Claude-side verdict for a parent-runtime gate or rewrite protected state/transcripts to manufacture identity. Report a genuine unresolved rule conflict that affects delivery.

During research, honor a user-requested Claude plugin/skill in that runtime; a similarly named parent skill is not equivalent evidence. Research consensus is a proposed decision, not a technical gate or runtime proof. Preserve history, record new decisions and carry forward still-valid authorization into the implementation mission.
