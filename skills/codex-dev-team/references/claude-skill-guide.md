<!-- SPDX-License-Identifier: MPL-2.0 -->
# Discuss the right skill with Claude

Start with the decision, intended result and authorized scope. Suggest a skill when it directly fits that work. The examples below are names in the public [sd0x-harness catalog](https://github.com/sd0xdev/sd0x-harness#essential-skills), checked on 2026-11-24; resolve the actual names and instructions in the target session's loaded plugin. A name found only in a local cache is not proof that the session can use it. A full name can be `sd0x-dev-flow:req-analyze`.

| Need | Candidate in the installed harness | PM handoff |
|---|---|---|
| Ambiguous requirements | `req-analyze` | Identify user decisions and turn them into observable scenarios. |
| Source-backed product/use-case research | `deep-research` | Compare approaches, supporting sources and limitations. |
| Competing approaches with known goals | `codex-brainstorm` | Explain tradeoffs against the agreed scenarios and constraints. |
| Engineering specification | `tech-spec` | Let Claude document technical decisions and dependencies. |
| Authorized commit/push or CI follow-up | `smart-commit`, `push-ci`, `watch-ci` | Respect existing authorization and the installed contract; return exact revision/CI evidence. |
| Effective configuration or setup gaps | `claude-health`, full `project-setup`, `install-rules`, `install-hooks`, `install-scripts` | Follow [harness readiness](harness.md), preserve overrides and read back a new process after writes. |
| Understanding technical gate records | `codex-review-fast`, `codex-review-doc`, `precommit` | Read original evidence; the project harness chooses gate type, order and depth. |

If nothing fits, inspect the target session's loaded skill descriptions or ask the existing Claude dev to inspect them locally. Compare relevant candidates by purpose/output, not name alone. If no suitable skill exists, hand back the outcome and AC for Claude to choose its approach. Do not invent a command or silently install a new plugin.

Design plugins are optional and separate from the mandatory harness. When appropriate, discuss an available design skill with Claude as designer, checking its source and availability first. A suggestion does not authorize installation or replace the user's design choice.

If the user explicitly requests a Claude-side skill, invoke it in Claude and retain its actual result. A parent Codex analysis or similarly named parent skill is not that invocation. Research conclusions remain provisional until the required implementation/runtime checks exist.
