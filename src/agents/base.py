"""Base agent interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class AgentResult:
    """Result from an agent operation."""

    success: bool
    data: Any
    message: str
    timestamp: datetime
    duration_ms: int
    errors: list[str]


class BaseAgent(ABC):
    """Abstract base class for agents."""

    agent_name: str = "base"

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}

    @abstractmethod
    async def run(self, *args, **kwargs) -> AgentResult:
        """Execute the agent's primary function."""
        pass

    def log(self, message: str, level: str = "info") -> None:
        """Log a message from this agent."""
        timestamp = datetime.utcnow().isoformat()
        print(f"[{timestamp}] [{self.agent_name}] [{level.upper()}] {message}")
