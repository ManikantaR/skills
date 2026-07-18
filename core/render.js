/* render.js — shared render helpers for repo-pulse + codebase-walkthrough.
   Inlined into each single-file offline artifact by assemble.py. Exposes a
   tiny `PC` (pulse-core) namespace; templates do their own rendering on top. */
(function () {
  const PC = (window.PC = window.PC || {});

  PC.esc = (s) =>
    String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );

  PC.el = (html) => {
    const t = document.createElement("template");
    t.innerHTML = String(html).trim();
    return t.content.firstElementChild;
  };

  PC.$ = (sel, root) => (root || document).querySelector(sel);

  /* Standalone theme toggle: the Artifact viewer stamps data-theme itself, so
     only inject our own control when it hasn't (i.e. hosted/opened directly). */
  PC.themeToggle = function () {
    if (document.documentElement.hasAttribute("data-theme")) return; // host controls it
    const saved = localStorage.getItem("pc-theme");
    if (saved) document.documentElement.setAttribute("data-theme", saved);
    const btn = PC.el(
      '<button aria-label="Toggle light/dark theme" title="Toggle theme" ' +
      'style="position:fixed;top:14px;right:14px;z-index:99;width:34px;height:34px;border-radius:100px;' +
      'border:1px solid var(--line);background:var(--surface);color:var(--ink-2);cursor:pointer;' +
      'font-family:var(--mono);font-size:14px;box-shadow:var(--shadow)">◐</button>'
    );
    btn.addEventListener("click", () => {
      const cur =
        document.documentElement.getAttribute("data-theme") ||
        (matchMedia("(prefers-color-scheme:dark)").matches ? "dark" : "light");
      const next = cur === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("pc-theme", next);
    });
    document.body.appendChild(btn);
  };

  PC.pct = (num, den) => (den ? Math.round((num / den) * 100) : 0);
})();
