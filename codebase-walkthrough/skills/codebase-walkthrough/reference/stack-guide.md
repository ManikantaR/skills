# Stack guide — finding entrypoints & tracing flows per stack

How to detect the stack, find the entrypoints (the "API entries"), and where a flow starts, for the
four supported stacks. A repo may mix several — do each.

## Python
- **Detect:** `pyproject.toml` / `setup.py` / `requirements.txt`, `.py` files.
- **Entrypoints:**
  - CLI: `[project.scripts]` in pyproject, `argparse`/`click`/`typer` subcommands, `if __name__ ==
    "__main__"`. Each subcommand = one flow (group **Commands**).
  - Web: FastAPI `@app.get/post`, Flask `@app.route`, Django `urls.py` → views, DRF viewsets. Each
    route = one flow (group **Routes**).
  - Jobs: Celery `@task`, APScheduler, a `while True` loop, cron entry. Group **Jobs**.
  - Tools: adapter/client classes, SDK wrappers. Group **Tools**.
- **Trace:** follow imports/method calls across modules. Layers are usually cli → service/handler →
  repository/store → external client. Note anything spending money/tokens or doing I/O.
- **Dev guide specifics:** exact `python3.x -m venv`, `pip install -e ".[dev]"`, `pytest`, `ruff`,
  `mypy`. Call out interpreter-version traps (system python too old).

## React / TypeScript
- **Detect:** `package.json`, `tsconfig.json`, `.tsx/.ts`, a bundler (vite/next/webpack).
- **Entrypoints (think in terms of user-driven flows, not "API"):**
  - Routes: React Router routes / Next.js `app/` or `pages/` files. Each route = a flow (group **Routes**).
  - Key user actions: a form submit / button handler → hook → API client → server. Group **Commands**
    ("user actions") or **Flows**.
  - Data hooks: `useQuery`/`useEffect` → fetch → cache. Group **Jobs** (background/data) if it fits.
  - API clients / service modules → group **Tools**.
  - Next.js server: API route handlers / server actions / RSC data loaders → group **Routes**.
- **Trace:** component render → event handler → custom hook → api client (`fetch`/axios/tRPC) →
  state update → re-render. Layers: component → hook → api-client → server. Show the round trip.
- **Dev guide:** `npm ci` / `pnpm i`, `npm run dev`, `npm test` (vitest/jest), `npm run build`,
  `tsc --noEmit`, `eslint`. Note the node version (`.nvmrc`/`engines`).

## C# / .NET
- **Detect:** `.csproj`/`.sln`, `Program.cs`, `.cs` files.
- **Entrypoints:**
  - Web API: `[HttpGet]/[HttpPost]` controller actions, or Minimal API `app.MapGet(...)`. Each = a
    flow (group **Routes**).
  - Console: `Program.Main`, `System.CommandLine` verbs. Group **Commands**.
  - Background: `IHostedService`/`BackgroundService.ExecuteAsync`, worker queues. Group **Jobs**.
  - Tools: service classes, repositories, `HttpClient` wrappers, EF `DbContext`. Group **Tools**.
- **Trace:** controller → service (DI) → repository/EF → DB or external client. Layers: controller →
  service → repository → data. Note async boundaries and transactions.
- **Dev guide:** `dotnet restore`, `dotnet build`, `dotnet run`, `dotnet test`, target framework and
  SDK version (`global.json`). User-secrets / appsettings for local config.

## SQL (schema / stored logic)
- **Detect:** `.sql` files, migration folders, a schema dir.
- **Entrypoints (the callable/observable objects):**
  - Stored procedures / functions → group **Commands** or **Tools**.
  - Views / materialized views → group **Tools**.
  - Triggers → group **Jobs** (they fire on events).
- **Trace:** a proc's body — the tables it reads/writes, functions/other procs it calls, triggers it
  fires. Layers: proc → table/view → trigger → downstream. "Flow" = data lineage. Tag heavy scans /
  locks / cross-DB calls as the costly hops.
- **Dev guide:** how to spin up the DB (docker compose / local engine), apply migrations, run the
  schema, run tests (tSQLt / pgTAP / a seed+assert script), connection string setup.

## Mixed repos (e.g. React front + C#/Python back + SQL)
Do each stack's entrypoints as its own group(s). Pick the Runtime hero flow as the **end-to-end user
request** that crosses stacks (UI action → API route → service → DB → response) — that single
cross-stack pipeline is the most illuminating animation for a full-stack repo.
