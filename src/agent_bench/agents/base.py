"""Base agent interface and types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from ..task import Task


@dataclass
class AgentResult:
    """Result from an agent execution."""

    success: bool
    output: str
    iterations: int
    tokens_used: Optional[int] = None
    agent_version: Optional[str] = None
    model_name: Optional[str] = None


class Agent(ABC):
    """Base class for AI agent adapters."""

    @abstractmethod
    def name(self) -> str:
        """Get the agent's name."""
        pass

    @abstractmethod
    async def execute(self, task: Task, workspace: Path) -> AgentResult:
        """Execute a task in the given workspace."""
        pass


class AgentType(str, Enum):
    """Available agent types."""

    CLAUDE = "claude"
    CLAUDE_DEEPSEEK = "claude-deepseek"
    CLAUDE_KIMI = "claude-kimi"
    CLAUDE_BIGMODEL = "claude-bigmodel"


def create_agent(agent_type: AgentType) -> Agent:
    """Create an agent instance by type using Claude Agent SDK."""
    import os
    from .claude_sdk import ClaudeSDKAgent

    if agent_type == AgentType.CLAUDE:
        # Official Claude API with personal account
        # Uses ANTHROPIC_API_KEY from environment
        return ClaudeSDKAgent(display_name="claude")

    elif agent_type == AgentType.CLAUDE_DEEPSEEK:
        # DeepSeek API (Claude-compatible)
        env_vars = {
            "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
            "ANTHROPIC_MODEL": "deepseek-chat",
        }
        # Add auth token from environment if available
        if "DEEPSEEK_AUTH_TOKEN" in os.environ:
            env_vars["ANTHROPIC_API_KEY"] = os.environ["DEEPSEEK_AUTH_TOKEN"]
        return ClaudeSDKAgent(
            display_name="claude-deepseek",
            model="deepseek-chat",
            env_vars=env_vars
        )

    elif agent_type == AgentType.CLAUDE_KIMI:
        # Kimi (Moonshot) API (Claude-compatible)
        env_vars = {
            "ANTHROPIC_BASE_URL": "https://api.moonshot.cn/anthropic",
            "ANTHROPIC_MODEL": "kimi-k2-turbo-preview",
        }
        # Add auth token from environment if available
        if "KIMI_AUTH_TOKEN" in os.environ:
            env_vars["ANTHROPIC_API_KEY"] = os.environ["KIMI_AUTH_TOKEN"]
        return ClaudeSDKAgent(
            display_name="claude-kimi",
            model="kimi-k2-turbo-preview",
            env_vars=env_vars
        )

    elif agent_type == AgentType.CLAUDE_BIGMODEL:
        # BigModel (GLM) API (Claude-compatible)
        env_vars = {
            "ANTHROPIC_BASE_URL": "https://open.bigmodel.cn/api/anthropic",
            "ANTHROPIC_MODEL": "glm-4.6",
        }
        # Add auth token from environment if available
        if "BIGMODEL_AUTH_TOKEN" in os.environ:
            env_vars["ANTHROPIC_API_KEY"] = os.environ["BIGMODEL_AUTH_TOKEN"]
        return ClaudeSDKAgent(
            display_name="claude-bigmodel",
            model="glm-4.6",
            env_vars=env_vars
        )

    else:
        raise ValueError(f"Unknown agent type: {agent_type}")
