---
name: rubber-duck-review
description: Run a rubber-duck review on a plan, spec, implementation, or fix before handoff or completion — five forced statements that surface hand-waving before it ships.
---

Run this before calling any plan, spec, implementation, or fix done. It was
originally duplicated (byte-for-byte) into three separate repos before being
promoted here — keep edits in this one place so they don't drift again.

Checklist — state each of the following explicitly, out loud (in the response),
not just implicitly assumed:

1. State the exact problem.
2. State the smallest solving change.
3. State the invariant that must remain true.
4. State the validation that proves success.
5. State the next likely failure mode.

If any answer is unclear or hand-wavy, keep refining the plan or implementation
before treating it as ready — don't paper over a weak answer with more words.
