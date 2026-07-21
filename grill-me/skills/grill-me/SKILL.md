---
name: grill-me
description: Interview the user relentlessly about a plan, spec, or design until each branch of the decision tree is resolved. Use when a plan is vague, a design needs pressure testing, or the user explicitly asks to be grilled.
---

Interview the user (or pressure-test the current spec) one branch at a time until
the design is concrete enough to implement safely. This had drifted into two
slightly different wordings across separate repos before being promoted here as
the single canonical copy — keep future edits in this one place.

- Ask one question at a time.
- If the answer can be discovered by reading the codebase or specs, do that
  instead of asking.
- For each unresolved branch, provide a recommended answer and the tradeoff —
  don't just ask open-ended questions with no opinion.
- Stop only when scope, file areas, validations, and risks are explicit.
