# AGENTS.md

## Project Overview

Agent Bench is a CLI tool for evaluating AI coding agents on real-world engineering tasks.
It runs tasks defined as YAML files, executes an AI agent (via OpenCode SDK) in a git-cloned
workspace, then verifies results with a Python script.

**Runtime**: Bun (>=1.0.0) | **Language**: TypeScript (strict) | **Target**: ES2022/ESNext

---

## Build & Test Commands

```bash
# Install dependencies
bun install

# Type check (primary lint — no separate eslint config)
bun run typecheck        # tsc --noEmit

# Run CLI in development (no build step needed)
bun run src/index.ts <command>

# Build for production
bun run build            # outputs to dist/

# Run production build
bun run start

# Enable debug output for any command
bun run src/index.ts --debug <command>
```

### CLI Commands

```bash
# List all available tasks
bun run src/index.ts list

# Run a single task (most common during development)
bun run src/index.ts run --task CODING-001 --model anthropic/claude-sonnet-4-5

# Run a single task, skip verification (faster iteration)
bun run src/index.ts run --task CODING-001 --no-verify

# Run all tasks in a category
bun run src/index.ts run --suite coding --model anthropic/claude-sonnet-4-5

# Run all tasks
bun run src/index.ts run --suite all

# Verify a task manually (without running the agent)
bun run src/index.ts verify --task CODING-001

# Collect results into CSV/JSON
bun run src/index.ts collect --format csv
bun run src/index.ts collect --format json

# Initialize user config
bun run src/index.ts init
```

### Running a Verification Script Directly

```bash
# From the workspace root (tasks/ submodule checkout)
python3 CODING/001/verify.py
python3 TOOLS/003/verify.py
# Exit 0 = PASS, exit 1 = FAIL
```

---

## Repository Structure

```
src/
├── index.ts              # CLI entry point
├── cli/
│   ├── index.ts          # Commander.js setup, global options
│   └── commands/         # One file per CLI subcommand
│       ├── run.ts
│       ├── list.ts
│       ├── verify.ts
│       ├── collect.ts
│       └── init.ts
├── core/
│   ├── task.ts           # Zod schemas + Task types
│   ├── loader.ts         # YAML task discovery & loading
│   ├── runner.ts         # Orchestrates agent + verifier per task
│   ├── workspace.ts      # Git clone / workspace setup
│   └── config.ts         # RunnerConfig, user config file (~/.config/agent-bench/)
├── agents/
│   ├── types.ts          # Agent interface, AgentResult, ModelConfig
│   ├── factory.ts        # createAgent() / createCustomAgent()
│   └── opencode.ts       # OpencodeAgent — OpenCode SDK adapter
├── evaluator/
│   ├── verifier.ts       # Runs task.verification.command via child_process
│   └── results.ts        # BenchmarkResult, SuiteResults, save helpers
├── collectors/
│   ├── csv.ts            # CSV export
│   └── json.ts           # JSON export / auto-append
└── utils/
    ├── errors.ts         # Custom error hierarchy
    └── logger.ts         # Chalk-based Logger class + global instance

tasks/                    # Git submodule — benchmark task definitions
docs/                     # Results output directory (default)
dist/                     # Production build output (gitignored)
```

---

## Code Style Guidelines

### TypeScript

- **Strict mode** is enabled; all `strict`, `noUnusedLocals`, `noUnusedParameters`,
  `noImplicitReturns`, and `noFallthroughCasesInSwitch` flags are on.
- Target **ES2022**, module resolution **bundler** (Bun-native).
- Use `type` imports for type-only symbols: `import type { Foo } from './foo.js'`.
- Always include the `.js` extension in relative imports (required for ESM):
  `import { Bar } from './bar.js'`.
- Use `@/*` path alias for `src/` imports where appropriate.
- Resolve JSON modules with `import data from './file.json'` (resolveJsonModule enabled).

### Naming Conventions

| Construct | Convention | Example |
|-----------|-----------|---------|
| Classes | PascalCase | `TaskRunner`, `OpencodeAgent` |
| Interfaces | PascalCase | `AgentResult`, `RunnerConfig` |
| Type aliases | PascalCase | `Task`, `TaskCategory` |
| Functions / methods | camelCase | `createAgent()`, `runTask()` |
| Variables | camelCase | `taskId`, `workspacePath` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_MODEL` |
| Enum members | UPPER_SNAKE_CASE | `LogLevel.DEBUG` |
| Files | camelCase | `runner.ts`, `opencode.ts` |

### Imports

- Prefer **named exports**; avoid default exports except for the CLI entry point.
- Group imports: external packages first, then internal (`../`, `./`).
- Use `import type` for anything that is only a type (interfaces, type aliases).

### Error Handling

- All custom errors extend `BenchError` (in `src/utils/errors.ts`).
- Available subclasses: `TaskNotFoundError`, `InvalidTaskFormatError`, `TaskLoadError`,
  `AgentError`, `VerificationError`, `TimeoutError`, `GitError`.
- Throw the most specific subclass; never throw plain strings.
- In CLI command handlers, catch errors, call `logger.error(...)`, and `process.exit(1)`.

### Logging

- Use the global `logger` instance from `src/utils/logger.ts` (never `console.log` in
  library code; `console.warn` is acceptable for non-fatal warnings in utilities).
- Log levels: `logger.debug()`, `logger.info()`, `logger.success()`, `logger.warn()`,
  `logger.error()`.
- Debug messages are suppressed unless `--debug` flag is passed.
- Structured output helpers: `logger.taskHeader()`, `logger.taskResult()`,
  `logger.suiteSummary()`.

### Validation

- Define data shapes as **Zod schemas** first, then derive TypeScript types with
  `z.infer<typeof Schema>`.
- Always parse untrusted input (YAML files, CLI args, API responses) through the
  relevant Zod schema before use.
- Use `.passthrough()` on schemas that intentionally allow extra fields (e.g.,
  `TaskMetadataSchema`).

### Documentation

- Add a **JSDoc block** to every exported class, interface, function, and non-trivial
  method. Include `@param` and `@returns` tags where helpful.
- File-level doc comment at the top of each file (one-liner describing the module).

### Async / Promises

- Use `async/await` throughout; avoid raw `.then()` chains.
- Always `await` cleanup in `finally` blocks (e.g., closing servers, restoring `cwd`).

---

## Task Definition Format (tasks/ submodule)

Tasks live in `tasks/<CATEGORY>/<NNN>/task.yaml`. Key fields:

```yaml
id: CODING-001                  # CATEGORY-NNN, uppercase
category: coding                # coding | writing | tools | bug-fix | feature | refactor
difficulty: easy                # easy | medium | hard
source:
  repository: https://github.com/org/repo.git
  commit: "main"
prompt: |
  Agent instructions. Paths relative to workspace root.
verification:
  type: python
  command: "python3 CODING/001/verify.py"
  timeout: 30
permissions:
  mode: "dontAsk"               # dontAsk | bypassPermissions | default
  write: true
  bash: true
  read: true
  web_fetch: false
```

Verification scripts (`verify.py`) must exit `0` on PASS and `1` on FAIL, print
`PASS: <description>` or `FAIL: <reason>`, and use only the Python standard library.
All paths are relative to the workspace root.

---

## Configuration

User config is stored at `~/.config/agent-bench/config.json`. Defaults:

| Key | Default |
|-----|---------|
| `tasksDir` | `<cwd>/tasks` |
| `resultsDir` | `<cwd>/docs` |
| `workspaceDir` | `<tmpdir>/agent-bench` |

CLI flags (`--tasks-dir`, `--results-dir`, `--workspace-dir`) override config file values.
