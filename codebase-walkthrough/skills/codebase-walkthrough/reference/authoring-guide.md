# Authoring guide — the `DATA` block

`docs/walkthrough.html` renders entirely from one `const DATA = {…}` object near the top of its
`<script>`. Edit only that object and the `<!-- EDIT -->` prose in the markup. Every key below is
optional except `meta`, `components`, `flows`, and `dev`; omit a key and its tab/section hides
itself. Keep prose tight — junior-readable, one idea per unit.

## `meta`
```js
meta:{ name:"Acme", tagline:"one-line what-it-is", date:"2026-07-05",
       metaphor:"optional: intuition-building analogy, then mapped to real terms",
       stats:[["5","components"],["12k","lines"],["120","tests"],["8","guardrails"]] }
```

## `overview` (New-here tab prose)
`overview.question` — the single curiosity hook ("what happens when …?"). `overview.pillars` —
three cards, `[emoji, title, html]`, the three things to remember.

## `walk` (guided code-walk) + `code`
`walk` is an array of steps `{key, h, p, hot:[lineIdx,…]}`. Each `key` indexes into `code`:
```js
code:{ key:{ file:"path/to/file.ext", lang:"py|ts|cs|sql", lines:["real","source","lines"] } }
```
`hot` highlights lines (0-based) for that step. Use REAL source lines, trimmed; 8–16 lines per
snippet. This is a CodeTour-style step-through — narrate WHY each highlighted region matters.

## `arch` (Architect tab)
- `arch.context` — `[emoji, name, sub]` external actors/systems.
- `arch.components` — the 4–6 parts, `{emoji, name, files, note}`.
- `arch.modules` — optional dependency graph: `nodes:[{id,label,x,y,ext?}]`, `edges:[[fromId,toId],…]`
  (coords in a 760×250 viewBox). Keep ≤8 nodes.
- `arch.guards` — `[id, title, html-desc, "file that enforces it"]`. The design-review surface.
- `arch.decisions` — `[id, title, why]`. Optional.

## `flows` (Flows tab — the call lifecycles)
Ordered dict; render order = declaration order. See `flow-tracing.md` for how to build `steps`.
```js
flows:{ dispatch:{ group:"Commands", name:"cmd name", desc:"short",
  file:"a.py → b.py → c.py", summary:"2–3 sentence plain-English arc",
  steps:[ [depth, layer, "method(params)", "one responsibility", ["tag",…]], … ] } }
```
- `layer` must be a key of `DATA.layers` (below) — it picks the colored chip.
- Tags: `"free"` (0 tokens / cheap), `"tok:<detail>"` (spends the expensive resource),
  `"guard:P4"` (invariant), `"stop:reason"` (this branch hands off to a human), or any plain string.
- `depth` = indentation (call-stack depth). Collapse helpers; 6–15 rows.

## `layers`
```js
layers:{ cli:"cli", control:"control-plane", store:"store", ext:"external" }
```
Map each layer key to a display label. The template ships CSS classes `L-cli/control/store/lane/
scm/proc/ext`; reuse those keys so the colors work, or add your own `.L-x{…}` rule if you need more.

## `runtime` (Runtime tab — animated hero flow)
```js
runtime:{ stages:[ {id:"in", label:"request", sub:"parse", tok:false},
                   {id:"svc", label:"service", sub:"logic", tok:true}, … ],
          happy:["log line per stage, HTML ok", …],
          altLabel:"⚠ error path", alt:{ atStage:1, log:"what happens on the sad path" },
          costTable:[["hop","no|yes · detail"], …],
          notes:{ title:"The numbers behind the design", rows:[["label","value"], …] } }
```
The pipeline SVG, the moving token, and the play/step controls are generated from `stages`. Keep
4–6 stages. `tok:true` marks a stage that spends the expensive resource (colored red in the table).
`costTable` fills the first Runtime card; the optional `notes` fills a second card beside it (e.g.
key ratios / benchmarks that justify the design). Omit `notes` and the second card hides.

## `roadmap` (Roadmap tab)
```js
roadmap:[ {id:"M0", cls:"now|done|''", title:"", pill:["now","code-complete"],
           body:"", prog:[done,total], tasks:[["T-01","done|now|wait"], …]} ]
```
Omit the whole key if the repo has no roadmap.

## `dev` (Dev guide tab — HOW-TO ONLY)
```js
dev:{ steps:[ {n:1, h:"Prerequisites", body:"<p>…</p>", sh:[["cmd","p"],["# note","cmt"]]} ],
      trouble:[ ["error text", "fix (html)"], … ] }
```
`sh` lines: `["text","p"]` renders a `$ ` prompt; `["text","cmt"]` a dimmed comment. Copy buttons
strip prompts/comments automatically. **No explanation prose here — action only (Diátaxis how-to).**

## Keep-blocks (for UPDATE mode)
Wrap any hand-tuned region you want preserved across regenerations in
`<!-- KEEP -->  …  <!-- /KEEP -->`. UPDATE copies these verbatim.
