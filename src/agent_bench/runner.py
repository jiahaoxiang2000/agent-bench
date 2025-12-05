"""Task runner for executing benchmarks."""

import logging
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

from git import Repo

from .agents import Agent, AgentType, create_agent
from .error import AgentError, GitError, VerificationError
from .evaluator import BenchmarkResult, SuiteResults, Verifier
from .task import Task, TaskLoader

logger = logging.getLogger(__name__)


@dataclass
class RunnerConfig:
    """Configuration for the task runner."""

    tasks_dir: Path
    results_dir: Path
    workspace_dir: Path
    max_iterations: int = 1

    @classmethod
    def default(cls) -> "RunnerConfig":
        """Create a default configuration."""
        return cls(
            tasks_dir=Path("tasks"),
            results_dir=Path("results"),
            workspace_dir=Path("/tmp/agent-bench"),
            max_iterations=1,
        )


class TaskRunner:
    """Task runner for executing benchmarks."""

    def __init__(self, config: RunnerConfig):
        self.config = config

    @classmethod
    def with_defaults(cls) -> "TaskRunner":
        """Create a task runner with default configuration."""
        return cls(RunnerConfig.default())

    async def run_task(self, task_id: str, agent_type: AgentType) -> BenchmarkResult:
        """Run a single task with the specified agent."""
        loader = TaskLoader(self.config.tasks_dir)
        task = loader.load_by_id(task_id)
        agent = create_agent(agent_type)

        return await self._execute_task(task, agent)

    async def run_all(self, agent_type: AgentType) -> SuiteResults:
        """Run all tasks with the specified agent."""
        loader = TaskLoader(self.config.tasks_dir)
        tasks = loader.load_all()
        agent = create_agent(agent_type)

        results = []
        for task in tasks:
            print(f"Running task: {task.id} - {task.title}")
            result = await self._execute_task(task, agent)
            status = "PASS" if result.success else "FAIL"
            print(f"  Result: {status} (score: {result.score}, duration: {result.duration_secs:.2f}s)")
            results.append(result)

        suite = SuiteResults.from_results(agent.name(), results)
        path = suite.save(self.config.results_dir)
        print(f"\nSuite results saved to: {path}")

        return suite

    async def _execute_task(self, task: Task, agent: Agent) -> BenchmarkResult:
        """Execute a single task."""
        start = time.time()

        # Prepare workspace
        try:
            workspace = self._prepare_workspace(task)
        except Exception as e:
            duration = time.time() - start
            return BenchmarkResult.create_failure(
                task_id=task.id,
                agent=agent.name(),
                iterations=0,
                tokens_used=None,
                duration_secs=duration,
                error=f"Failed to prepare workspace: {e}",
                agent_version=None,
                model_name=None,
            )

        # Execute agent
        try:
            agent_result = await agent.execute(task, workspace)
        except Exception as e:
            duration = time.time() - start
            return BenchmarkResult.create_failure(
                task_id=task.id,
                agent=agent.name(),
                iterations=0,
                tokens_used=None,
                duration_secs=duration,
                error=f"Agent execution failed: {e}",
                agent_version=None,
                model_name=None,
            )

        # Run verification
        try:
            verification = await Verifier.verify(task, workspace)
        except Exception as e:
            duration = time.time() - start
            result = BenchmarkResult.create_failure(
                task_id=task.id,
                agent=agent.name(),
                iterations=agent_result.iterations,
                tokens_used=agent_result.tokens_used,
                duration_secs=duration,
                error=f"Verification failed: {e}",
                agent_version=agent_result.agent_version,
                model_name=agent_result.model_name,
            )
            result.with_agent_output(agent_result.output)
            path = result.save(self.config.results_dir)
            print(f"Result saved to: {path}")
            return result

        duration = time.time() - start

        # Create result
        if verification.passed:
            result = BenchmarkResult.create_success(
                task_id=task.id,
                agent=agent.name(),
                iterations=agent_result.iterations,
                tokens_used=agent_result.tokens_used,
                duration_secs=duration,
                agent_version=agent_result.agent_version,
                model_name=agent_result.model_name,
            )
        else:
            result = BenchmarkResult.create_failure(
                task_id=task.id,
                agent=agent.name(),
                iterations=agent_result.iterations,
                tokens_used=agent_result.tokens_used,
                duration_secs=duration,
                error="Verification tests failed",
                agent_version=agent_result.agent_version,
                model_name=agent_result.model_name,
            )

        result.with_agent_output(agent_result.output)
        result.with_verification_output(
            f"Exit code: {verification.exit_code}\n\n"
            f"STDOUT:\n{verification.stdout}\n\n"
            f"STDERR:\n{verification.stderr}"
        )

        # Save individual result
        path = result.save(self.config.results_dir)
        print(f"Result saved to: {path}")

        return result

    def _prepare_workspace(self, task: Task) -> Path:
        """Prepare a workspace for task execution."""
        workspace = self.config.workspace_dir / task.id

        # Clean up existing workspace if it exists
        if workspace.exists():
            shutil.rmtree(workspace)

        # Clone the repository only if not "none"
        if task.source.repository != "none" and task.source.repository:
            self._clone_repo(task.source.repository, task.source.commit, workspace)
        else:
            # Create empty workspace directory for tasks that don't need a repository
            workspace.mkdir(parents=True, exist_ok=True)

        return workspace

    def _clone_repo(self, repo_url: str, commit: str, workspace: Path) -> None:
        """Clone a repository to the workspace."""
        try:
            # Clone the repository
            repo = Repo.clone_from(repo_url, str(workspace))

            # If commit is "main", "master", or "HEAD", stay on default branch
            if commit in {"main", "master", "HEAD"}:
                return

            # Try to checkout as a commit hash or branch
            try:
                repo.git.checkout(commit)
            except Exception as e:
                raise GitError(f"Failed to checkout '{commit}': {e}")

        except Exception as e:
            raise GitError(f"Failed to clone repository: {e}")

    def list_tasks(self) -> List[Task]:
        """List all available tasks."""
        loader = TaskLoader(self.config.tasks_dir)
        return loader.load_all()
