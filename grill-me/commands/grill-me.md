---
description: Interview the user relentlessly about a plan, spec, or design until every branch is resolved.
---

Invoke the **grill-me** skill (`skills/grill-me/SKILL.md`) against `$ARGUMENTS` (the
plan/spec/design in question; if omitted, use whatever is currently proposed in this
conversation).

- Ask one question at a time.
- Prefer discovering the answer from the codebase or specs over asking, when possible.
- For each unresolved branch, give a recommended answer and the tradeoff.
- Stop only when scope, file areas, validations, and risks are all explicit.
