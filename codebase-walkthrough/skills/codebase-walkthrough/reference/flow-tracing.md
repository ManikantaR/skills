# Flow tracing — code → honest call lifecycle

A flow is one entrypoint's journey through the code, shown as an indented call trace (the Django
"request lifecycle" idiom). The goal: the reader sees the *real path*, not a call-graph hairball.

## The rules

1. **One entrypoint per flow.** A CLI subcommand, an HTTP route handler, a job tick, or a tool/
   adapter's public methods. Never trace the whole program into one diagram.
2. **Follow the real code.** Open the entry function and read it top to bottom, stepping into calls
   that cross a module/layer boundary. The `steps` order MUST match execution order.
3. **Collapse helpers.** Skip pure getters, formatting, tiny private helpers. Show a call only if it
   (a) crosses a layer, (b) does I/O or spends the expensive resource, or (c) enforces an invariant.
   Aim for 6–15 rows. If you have 30, you're not collapsing.
4. **Depth = call-stack depth.** `depth 0` = the entrypoint; `+1` each time you step into a callee
   you're showing. Siblings share a depth.
5. **Each row = method + key params + ONE responsibility.** Params teach the contract; the
   responsibility is a single clause, present-tense ("pins a model", "refuses unless landed").
6. **Tag the meaningful rows.** `free` (deterministic/cheap), `tok:…` (spends the costly resource —
   LLM tokens, an external paid API, a heavy query), `guard:…` (an invariant proven here), `stop:…`
   (this branch hands off to a human / errors out). Don't tag every row — tag the ones that teach.
7. **Show the fork, not every branch.** If a step can fail into a human-handoff, add one row for it
   with a `stop:` tag. Don't enumerate every exception.

## How to verify (do this — it's the whole point)

For each flow, after drafting `steps`, re-open the entry file and check: does row N's call actually
happen, in that order, with those params? Fix mismatches. A confident wrong trace is the failure
mode this skill exists to avoid. If a path is genuinely dynamic/uncertain, mark it and say so in the
`summary` rather than inventing an order.

## Optional: cross-check with a tool (not required)

For large/unfamiliar Python code you may sanity-check your hand-trace against a scoped static graph:
`code2flow --target-function <entry> --downstream-depth 3 path/` (outputs the reachable calls). Use
it as a checklist to catch a branch you missed — NOT as the published artifact (its raw graph is the
hairball you're avoiding). For a truly accurate single run, a dynamic trace (`viztracer`, or a small
`sys.settrace` hook around one real invocation) shows exactly what executed. Prefer hand-tracing +
verification for curated teaching quality; reach for tools only when the code is too big to hold.

## Grouping entrypoints

Put each flow in a `group` that fits the stack: **Commands** (CLI), **Routes** (web/API),
**Jobs** (schedulers/workers/queues), **Tools** (adapters, clients, stored-proc wrappers). Mixed
stacks can use several groups. The Flows tab lists them under these headers.
