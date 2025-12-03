"""Custom error types for Agent Bench."""


class BenchError(Exception):
    """Base exception for Agent Bench errors."""
    pass


class TaskNotFoundError(BenchError):
    """Raised when a task is not found."""
    pass


class InvalidTaskFormatError(BenchError):
    """Raised when a task has an invalid format."""
    pass


class TaskLoadError(BenchError):
    """Raised when a task fails to load."""
    pass


class AgentError(BenchError):
    """Raised when an agent execution fails."""
    pass


class VerificationError(BenchError):
    """Raised when verification fails."""
    pass


class TimeoutError(BenchError):
    """Raised when an operation times out."""

    def __init__(self, timeout_secs: int):
        super().__init__(f"Timeout after {timeout_secs} seconds")
        self.timeout_secs = timeout_secs


class GitError(BenchError):
    """Raised when a git operation fails."""
    pass
