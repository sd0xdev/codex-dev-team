<!-- SPDX-License-Identifier: MPL-2.0 -->
# Archive an owned Remote Control conversation

Use only when the user requests archiving a recorded conversation managed by this skill. Completion or PR merge alone does not authorize archive. This is session maintenance; it does not require a new development loop or harness setup. Preserve transcript, missions, handoffs and evidence.

1. Match the canonical repo, recorded local session UUID, current remote URL/identity and owned socket/pane. Local resume UUIDs and remote URL IDs are different; correlate them from original connection evidence rather than names alone.
2. If trustworthy remote archive evidence already exists, report it without resuming. Otherwise, operate only after the owned session is idle with no background work, pending approval or unsent draft. For an exited process, verify no other process owns that UUID before reconnecting.
3. Inspect the installed CLI's supported controls and current interactive RC menu. Do not guess an archive command or hard-code key counts. A disconnect action is not proof of archive. If CLI archive is unavailable or unverified, use the user's authenticated remote UI Archive action for the exact target, if available.
4. When reconnecting is necessary to finish authorized archive, use the recorded UUID, repo, account, model and permission settings in a fresh private operation directory, with no mission prompt, fork or `--continue`. Apply the existing explicit socket/ownership rules. Verify that the remote identity still matches before acting; a different URL is not a substitute target.
5. Confirm the result from the current remote Archived state or a version-understood successful archive response for that target. Keep minimal timestamp/identity/status evidence locally; never publish raw debug logs or credentials. Local exit, a missing pane, exit zero and “disconnected” alone leave **remote archive unconfirmed**.
6. After confirmed archive, exit the owned process and record local shutdown separately. Do not resume or re-enable RC to test archive; that can reactivate the conversation. Do not delete history, cache or transcripts as an archive substitute.

If authentication or organization policy blocks the action, report the concrete remaining user step. Do not extract credentials, replay internal APIs or repeatedly reconnect/disconnect. Keep an ordinary completed idle RC session available for the user unless archiving or stopping it was requested or is necessary for a safe process transition.

Current behavior is version-dependent. Consult [Remote Control](https://code.claude.com/docs/en/remote-control) and the [remote Archive documentation](https://code.claude.com/docs/en/claude-code-on-the-web#archive-sessions); their UI guidance is not a guarantee about any CLI disconnect implementation. This release does not claim a live archive test or add an automated archive command.
