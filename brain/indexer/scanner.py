"""Incremental scanner orchestrating adapters, episode segmentation, and offset tracking."""

import logging
from pathlib import Path
from typing import Dict, Tuple
from brain.adapters.antigravity import AntigravityAdapter
from brain.config import CONFIG, BrainConfig
from brain.db.repository import BrainRepository
from brain.indexer.episodes import EpisodeSegmenter
from brain.indexer.offset_tracker import OffsetTracker

logger = logging.getLogger("brain.indexer.scanner")

class IncrementalScanner:
    def __init__(self, repo: BrainRepository, config: BrainConfig = CONFIG):
        self.repo = repo
        self.config = config
        self.offset_tracker = OffsetTracker(repo.conn)
        self.adapter = AntigravityAdapter(config.gemini_dir)

    def scan_all(self, force: bool = False) -> Dict[str, int]:
        """Runs an incremental scan over projects and sessions."""
        projects_count = self.scan_projects()
        convs_count, episodes_count, steps_count = self.scan_sessions(force=force)

        return {
            "projects_indexed": projects_count,
            "conversations_indexed": convs_count,
            "episodes_indexed": episodes_count,
            "steps_indexed": steps_count,
        }

    def scan_projects(self) -> int:
        raw_projects = self.adapter.discover_projects()
        for p in raw_projects:
            self.repo.upsert_project({
                "id": p.id,
                "name": p.name,
                "root_path": p.root_path,
                "default_branch": p.default_branch,
                "raw_config": p.raw_config,
                "updated_at": p.updated_at,
            })
        return len(raw_projects)

    def scan_sessions(self, force: bool = False) -> Tuple[int, int, int]:
        # Build map of path -> project_id
        projects = self.repo.get_projects()
        projects_by_path: Dict[str, str] = {}
        for p in projects:
            if p.get("root_path"):
                projects_by_path[p["root_path"]] = p["id"]

        session_dirs = self.adapter.discover_sessions()
        conv_count = 0
        episodes_count = 0
        step_count = 0

        for sdir in session_dirs:
            # Check incremental offset
            transcript_path = sdir / ".system_generated" / "logs" / "transcript.jsonl"
            transcript_full = sdir / ".system_generated" / "logs" / "transcript_full.jsonl"
            active_file = transcript_full if transcript_full.exists() else transcript_path

            if not active_file.exists():
                continue

            needs_processing, _ = self.offset_tracker.check_file_status(active_file)
            if not needs_processing and not force:
                continue

            # Parse session with secret redaction
            raw_session = self.adapter.parse_session(sdir, projects_by_path)
            if not raw_session:
                continue

            # 1. Upsert Conversation
            self.repo.upsert_conversation({
                "id": raw_session.id,
                "project_id": raw_session.project_id,
                "title": raw_session.title,
                "model": raw_session.model,
                "total_steps": len(raw_session.steps),
                "created_at": raw_session.created_at,
                "updated_at": raw_session.updated_at,
            })
            conv_count += 1

            # 2. Segment into Episodes
            episodes = EpisodeSegmenter.segment_session(raw_session)
            for ep in episodes:
                self.repo.upsert_episode(ep)
                episodes_count += 1

            # 3. Upsert Steps & Tool Calls
            for step in raw_session.steps:
                step_obj = {
                    "id": f"{raw_session.id}_{step.step_index}",
                    "conversation_id": raw_session.id,
                    "step_index": step.step_index,
                    "source": step.source,
                    "type": step.step_type,
                    "status": step.status,
                    "thinking": step.thinking,
                    "content": step.content,
                    "created_at": step.created_at,
                }
                tool_calls_data = []
                for tc in step.tool_calls:
                    tool_calls_data.append({
                        "step_id": step_obj["id"],
                        "conversation_id": raw_session.id,
                        "tool_name": tc["tool_name"],
                        "tool_action": tc["tool_action"],
                        "tool_summary": tc["tool_summary"],
                        "arguments_json": str(tc.get("arguments", {})),
                        "output": tc.get("output", ""),
                        "exit_code": 0,
                        "created_at": tc.get("created_at", step.created_at),
                    })

                self.repo.upsert_step(step_obj, tool_calls_data, commit=False)
                step_count += 1

            # 4. Upsert Artifacts
            for art in raw_session.artifacts:
                self.repo.upsert_artifact(art, commit=False)

            self.repo.conn.commit()

            # 5. Commit offset tracker
            self.offset_tracker.commit_offset(active_file, active_file.stat().st_size)

        return conv_count, episodes_count, step_count
