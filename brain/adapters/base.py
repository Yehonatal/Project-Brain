"""Pluggable Source Adapter base interface for agent transcript providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

@dataclass
class RawStep:
    step_index: int
    source: str
    step_type: str
    status: str
    thinking: str = ""
    content: str = ""
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = ""

@dataclass
class RawSession:
    id: str
    title: str
    project_id: Optional[str]
    model: str
    steps: List[RawStep]
    artifacts: List[Dict[str, Any]]
    created_at: str
    updated_at: str

@dataclass
class RawProject:
    id: str
    name: str
    root_path: Optional[str]
    default_branch: Optional[str]
    permissions: Dict[str, Any] = field(default_factory=dict)
    raw_config: str = ""
    updated_at: str = ""

class BaseSourceAdapter(ABC):
    """Abstract adapter to support multiple agent systems (Antigravity, Claude Code, Cursor, Codex)."""

    @abstractmethod
    def discover_projects(self) -> List[RawProject]:
        """Discovers and parses configured workspaces/projects."""
        pass

    @abstractmethod
    def discover_sessions(self) -> List[Path]:
        """Returns list of discovered session directory or file paths."""
        pass

    @abstractmethod
    def parse_session(self, path: Path, projects_by_path: Dict[str, str]) -> Optional[RawSession]:
        """Parses a raw session into a normalized RawSession instance."""
        pass
