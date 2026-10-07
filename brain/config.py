"""Configuration and path management for Project Brain."""

import os
from pathlib import Path

# Base directories
HOME = Path(os.path.expanduser("~"))
DEFAULT_GEMINI_DIR = HOME / ".gemini"
DEFAULT_ANTIGRAVITY_DIR = DEFAULT_GEMINI_DIR / "antigravity"
DEFAULT_PROJECTS_DIR = DEFAULT_GEMINI_DIR / "config" / "projects"
DEFAULT_BRAIN_STORAGE = Path(os.getcwd()) / ".brain_data"

# Web Server defaults
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765

class BrainConfig:
    def __init__(
        self,
        gemini_dir: Path | None = None,
        db_path: Path | None = None,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
    ):
        self.gemini_dir = Path(gemini_dir) if gemini_dir else DEFAULT_GEMINI_DIR
        self.antigravity_dir = self.gemini_dir / "antigravity"
        self.brain_dir = self.antigravity_dir / "brain"
        self.projects_dir = self.gemini_dir / "config" / "projects"
        self.skills_dir = self.antigravity_dir / "builtin" / "skills"
        
        # SQLite DB path
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path(os.getcwd()) / "brain.db"
            
        self.host = host
        self.port = port
        
    def ensure_paths(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

# Singleton global instance
CONFIG = BrainConfig()
