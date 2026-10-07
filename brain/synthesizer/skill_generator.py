"""Synthesizes candidate Antigravity Skills from mined cross-session workflows."""

import os
from pathlib import Path
from typing import Any, Dict, List
from brain.config import CONFIG, BrainConfig
from brain.db.repository import BrainRepository
from brain.synthesizer.pattern_miner import PatternMiner

class SkillSynthesizer:
    def __init__(self, repo: BrainRepository, config: BrainConfig = CONFIG):
        self.repo = repo
        self.config = config
        self.miner = PatternMiner(repo)

    def synthesize_candidates(self) -> List[Dict[str, Any]]:
        """Synthesizes candidate skills from mined patterns across all projects."""
        recipes = self.miner.mine_command_recipes(min_frequency=1)
        candidates = []

        for rec in recipes:
            binary = rec["binary"]
            freq = rec["frequency"]
            projects_str = ", ".join(rec["projects"])
            commands = rec["distinct_commands"]
            actions = rec["sample_actions"]

            skill_name = f"auto-{binary}-workflow"
            skill_desc = f"Automated workflow and operational patterns for {binary} observed across {projects_str}."

            # Construct markdown instructions
            cmd_bullets = "\n".join(f"```bash\n{c}\n```" for c in commands[:5])
            action_bullets = "\n".join(f"- {a}" for a in actions if a) or f"- Run {binary} commands safely and effectively."

            markdown_content = f"""---
name: {skill_name}
description: {skill_desc}
---

# {binary.capitalize()} Automation & Operational Workflow

This skill was automatically synthesized by **Project Brain** by clustering {freq} actions observed across projects: `{projects_str}`.

## Common Operations
{action_bullets}

## Standard Command Patterns
{cmd_bullets}

## Best Practices
1. Ensure sandboxed execution policies or required environment variables are set.
2. Verify exit codes before chaining dependent steps.
3. Use non-interactive flags when executing commands in background subagents.
"""

            candidate = {
                "id": skill_name,
                "name": skill_name,
                "description": skill_desc,
                "instructions": markdown_content,
                "trigger_pattern": binary,
                "source_sessions": f"Discovered across {freq} executions in {projects_str}",
                "status": "candidate",
                "installed_path": None,
                "frequency": freq,
                "projects": rec["projects"],
            }
            candidates.append(candidate)
            # Store in repository
            self.repo.upsert_skill(candidate)

        return candidates

    def install_skill(self, skill_name: str, target_dir: Path | None = None) -> Path:
        """Installs a synthesized skill into the Antigravity skills directory."""
        dest_dir = target_dir if target_dir else self.config.skills_dir / skill_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        skill_file = dest_dir / "SKILL.md"

        cursor = self.repo.conn.execute("SELECT instructions FROM skills WHERE name = ?", (skill_name,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Skill '{skill_name}' not found.")

        instructions = row["instructions"]
        skill_file.write_text(instructions, encoding="utf-8")

        # Update DB status
        self.repo.conn.execute(
            "UPDATE skills SET status = 'installed', installed_path = ? WHERE name = ?",
            (str(skill_file), skill_name),
        )
        self.repo.conn.commit()
        return skill_file
