# Agent Bench

An open-source benchmark initiative for evaluating AI coding agents on real-world engineering tasks specific to our workflows.

## Overview

Agent Bench creates reproducible evaluation environments derived from authentic development tasks encountered in our daily work. Unlike synthetic coding benchmarks, Agent Bench focuses on genuine engineering challenges that reflect the complexity of real-world software development.

## Goals

1. **Realistic Evaluation** - Test AI agents on actual engineering problems rather than artificial puzzles
2. **Domain-Specific Assessment** - Measure agent capabilities on tasks relevant to our specific technology stack and workflows
3. **Reproducible Benchmarking** - Provide standardized environments for consistent agent comparison
4. **Continuous Improvement** - Build a growing collection of tasks to track agent progress over time

## How It Works

### Task Collection

Tasks are collected through two channels:

- **Automatic Capture**: Identify challenging tasks where AI agents struggled or required human intervention
- **Manual Submission**: Engineers submit real problems from their development work

### Task Structure

Each benchmark task includes:

| Component | Description |
|-----------|-------------|
| Repository Snapshot | Git commit hash marking the starting state |
| Initial Prompt | The original task description given to the agent |
| Verification Criteria | Automated tests based on the actual solution |
| Metadata | Difficulty level, category, time constraints, etc. |

## Task Categories

- **Bug Fixes** - Debugging and resolving issues in existing code
- **Feature Implementation** - Adding new functionality to existing systems
- **Refactoring** - Code restructuring and optimization tasks
- **Integration** - Connecting systems, APIs, and services
- **Configuration** - Setup, deployment, and DevOps tasks
- **Documentation** - Technical writing and code documentation

## Evaluation Metrics

| Metric | Description |
|--------|-------------|
| Success Rate | Percentage of tasks completed correctly |
| Iteration Count | Number of attempts before success |
| Token Usage | Total tokens consumed during task completion |
| Time to Completion | Duration from start to successful verification |
| Human Intervention | Amount of manual assistance required |

## Getting Started

### Prerequisites

- Python 3.10+
- Git
- Docker (optional, for isolated environments)

### Installation

```bash
git clone https://github.com/your-org/agent-bench.git
cd agent-bench
pip install -e .
```

### Running a Benchmark

```bash
# List available tasks
agent-bench list

# Run a specific task
agent-bench run --task <task-id> --agent <agent-name>

# Run full benchmark suite
agent-bench run --suite all --agent <agent-name>
```

## Contributing Tasks

### Submission Guidelines

1. **Real-world Origin** - Tasks must come from actual development work
2. **Reproducibility** - Include all context needed to recreate the scenario
3. **Verifiability** - Provide automated tests that validate the solution
4. **Documentation** - Describe the problem clearly and include expected outcomes

### Task Template

```yaml
id: task-001
title: "Brief description of the task"
category: bug-fix | feature | refactor | integration | config | docs
difficulty: easy | medium | hard | expert
repository: https://github.com/org/repo
commit: abc123def456
prompt: |
  The full prompt given to the agent...
verification:
  type: test | script | manual
  command: "pytest tests/test_feature.py"
metadata:
  estimated_time: "30m"
  tags: ["python", "api", "database"]
```

## Project Structure

```
agent-bench/
├── README.md
├── pyproject.toml
├── src/
│   └── agent_bench/
│       ├── __init__.py
│       ├── cli.py
│       ├── runner.py
│       ├── evaluator.py
│       └── reporters/
├── tasks/
│   ├── bug-fixes/
│   ├── features/
│   └── refactoring/
├── agents/
│   └── adapters/
└── results/
```

## Roadmap

- [ ] Core benchmark infrastructure
- [ ] Task submission and validation pipeline
- [ ] Agent adapter interface
- [ ] Results dashboard and reporting
- [ ] CI/CD integration for automated benchmarking
- [ ] Public leaderboard

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

Inspired by the [Cline Bench Initiative](https://cline.bot/blog/cline-bench-initiative) and the need for realistic AI agent evaluation in software engineering contexts.
