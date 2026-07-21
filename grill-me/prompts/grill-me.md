# grill-me

Portable pointer for non-Claude harnesses (Codex, Copilot, etc.). Full text at
`skills/grill-me/SKILL.md` in this plugin.

Use when a plan is vague, a design needs pressure testing, or the user explicitly
asks to be grilled. Interview one branch at a time until the design is concrete
enough to implement safely:

- Ask one question at a time.
- Prefer discovering the answer from the codebase or specs over asking, when possible.
- For each unresolved branch, give a recommended answer and the tradeoff.
- Stop only when scope, file areas, validations, and risks are all explicit.
