# Agent Bench

Open-source benchmark for evaluating AI coding agents on real engineering tasks.

## Live Results

See benchmark results here: https://isomoes.github.io/agent-bench/

## Quick Start

### Prerequisites

- [Bun](https://bun.sh/) (>=1.0.0)
- Git

### Install

```bash
git clone https://github.com/isomoes/agent-bench.git
cd agent-bench
bun install
```

### Run Benchmarks

```bash
# List tasks
bun run src/index.ts list

# Run one task
bun run src/index.ts run --task <task-id> --agent <agent-name>

# Run full suite
bun run src/index.ts run --suite all --agent <agent-name>

# Aggregate JSON results into CSV
bun run src/index.ts collect
```

## Task Format (Example)

```yaml
id: BUG-001
title: "Fix race condition in cache invalidation"
category: bug-fix
difficulty: hard

source:
  repository: https://github.com/org/repo
  commit: abc123def456

prompt: |
  The cache invalidation has a race condition causing intermittent test failures.

verification:
  type: pytest
  command: "pytest tests/test_cache.py -v"
  timeout: 60
```

## Development

```bash
bun run typecheck
bun run src/index.ts <command>
bun run src/index.ts --debug <command>
bun run build
```

## License

MIT License - see [LICENSE](LICENSE).
