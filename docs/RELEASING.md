# Maintainer release procedure

Public releases are curated snapshots. There is no automatic synchronization with another repository and no fixed release lag. The maintainer chooses when to publish updates; urgent correctness or security fixes may ship sooner.

1. Work on the public tree only. Copy selected source changes without importing another repository's Git history, runtime artifacts, credentials, or personal configuration.
2. Preserve explicit model selection and portable paths. Keep sd0x-harness mandatory and verify its current install/setup interface. Update both READMEs when user-visible behavior changes.
3. Run the offline runner/waiter tests and installer tests documented in README. Run Codex's skill validator when available. Test installation into a temporary skills root, including update/backup behavior. Do not replace a maintainer's private skill to test packaging.
4. Review the complete staged diff, local paths, identifying examples, links, license notices, and all files in the release. Verify the source version and installed-copy hashes separately when extracting changes.
5. Update VERSION and CHANGELOG. Commit, push, and wait for CI on that exact commit. Create the matching `vX.Y.Z` tag and GitHub release from that commit.
6. From a clean clone of the tag, install into a temporary root and compare the installed file contents and executable bits with `skills/codex-dev-team`. Read back the GitHub repository visibility, release tag/target, and CI result.

Offline tests use synthetic CLI/tmux fixtures. They do not prove a paid Claude task, live RC access, harness gates, or real multi-project integration ran. Record any live compatibility checks separately, with versions and scope.
