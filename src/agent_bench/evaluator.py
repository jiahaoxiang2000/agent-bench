"""Evaluation and verification for Agent Bench."""

import asyncio
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

from .error import VerificationError
from .task import Task


class VerificationResult:
    """Verification result."""

    def __init__(
        self,
        passed: bool,
        exit_code: Optional[int],
        stdout: str,
        stderr: str,
        duration_secs: float,
    ):
        self.passed = passed
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.duration_secs = duration_secs


class Verifier:
    """Verifier for running task verification commands."""

    @staticmethod
    async def verify(task: Task, workspace: Path) -> VerificationResult:
        """Run verification for a task in the given workspace."""
        import time

        start = time.time()

        # Parse the command
        command_parts = shlex.split(task.verification.command)
        if not command_parts:
            raise VerificationError("Empty verification command")

        program = command_parts[0]
        args = command_parts[1:]

        # Build and execute the command with timeout
        try:
            process = await asyncio.create_subprocess_exec(
                program,
                *args,
                cwd=str(workspace),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=task.verification.timeout
            )

            exit_code = process.returncode
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

        except asyncio.TimeoutError:
            raise VerificationError(
                f"Verification command timed out after {task.verification.timeout} seconds"
            )
        except Exception as e:
            raise VerificationError(f"Failed to execute verification command: {e}")

        duration_secs = time.time() - start

        return VerificationResult(
            passed=(exit_code == 0),
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_secs=duration_secs,
        )


class BenchmarkResult(BaseModel):
    """Benchmark result for a single task run."""

    task_id: str
    agent: str
    success: bool
    score: int
    iterations: int
    tokens_used: Optional[int] = None
    duration_secs: float
    verification_output: Optional[str] = None
    agent_output: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error: Optional[str] = None

    @classmethod
    def create_success(
        cls,
        task_id: str,
        agent: str,
        iterations: int,
        tokens_used: Optional[int],
        duration_secs: float,
    ) -> "BenchmarkResult":
        """Create a successful result."""
        return cls(
            task_id=task_id,
            agent=agent,
            success=True,
            score=100,
            iterations=iterations,
            tokens_used=tokens_used,
            duration_secs=duration_secs,
        )

    @classmethod
    def create_failure(
        cls,
        task_id: str,
        agent: str,
        iterations: int,
        tokens_used: Optional[int],
        duration_secs: float,
        error: str,
    ) -> "BenchmarkResult":
        """Create a failed result."""
        return cls(
            task_id=task_id,
            agent=agent,
            success=False,
            score=0,
            iterations=iterations,
            tokens_used=tokens_used,
            duration_secs=duration_secs,
            error=error,
        )

    def with_verification_output(self, output: str) -> "BenchmarkResult":
        """Add verification output to the result."""
        self.verification_output = output
        return self

    def with_agent_output(self, output: str) -> "BenchmarkResult":
        """Add agent output to the result."""
        self.agent_output = output
        return self

    def save(self, results_dir: Path) -> Path:
        """Save result to a JSON file."""
        results_dir.mkdir(parents=True, exist_ok=True)

        filename = (
            f"{self.task_id}_{self.agent}_{self.timestamp.strftime('%Y%m%d_%H%M%S')}_"
            f"{'pass' if self.success else 'fail'}.json"
        )
        path = results_dir / filename

        with open(path, "w") as f:
            f.write(self.model_dump_json(indent=2))

        return path


class SuiteResults(BaseModel):
    """Suite results containing multiple benchmark results."""

    agent: str
    results: List[BenchmarkResult]
    total_tasks: int
    passed: int
    failed: int
    pass_rate: float
    total_duration_secs: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def from_results(cls, agent: str, results: List[BenchmarkResult]) -> "SuiteResults":
        """Create suite results from individual benchmark results."""
        total_tasks = len(results)
        passed = sum(1 for r in results if r.success)
        failed = total_tasks - passed
        pass_rate = passed / total_tasks if total_tasks > 0 else 0.0
        total_duration_secs = sum(r.duration_secs for r in results)

        return cls(
            agent=agent,
            results=results,
            total_tasks=total_tasks,
            passed=passed,
            failed=failed,
            pass_rate=pass_rate,
            total_duration_secs=total_duration_secs,
        )

    def save(self, results_dir: Path) -> Path:
        """Save suite results to a JSON file."""
        results_dir.mkdir(parents=True, exist_ok=True)

        filename = f"suite_{self.agent}_{self.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        path = results_dir / filename

        with open(path, "w") as f:
            f.write(self.model_dump_json(indent=2))

        return path
