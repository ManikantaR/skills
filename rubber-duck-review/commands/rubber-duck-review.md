---
description: Run a rubber-duck review on the current plan, spec, or implementation before calling it done.
---

Invoke the **rubber-duck-review** skill (`skills/rubber-duck-review/SKILL.md`) against
`$ARGUMENTS` (the plan/spec/diff in question; if omitted, use whatever is currently
proposed or just implemented in this conversation).

State each of the five explicitly, out loud, not just implicitly assumed:
1. The exact problem.
2. The smallest solving change.
3. The invariant that must remain true.
4. The validation that proves success.
5. The next likely failure mode.

If any answer is unclear or hand-wavy, keep refining before treating it as ready.
