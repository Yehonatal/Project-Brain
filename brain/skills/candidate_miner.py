"""Mines candidate draft skills using failure-then-fix heuristics and repeated domain commands."""

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List
from brain.db.repository import BrainRepository
from brain.security.redactor import SecretRedactor

TRIVIAL_COMMANDS = {"ls", "cat", "echo", "pwd", "rm", "mkdir", "cd", "head", "tail", "which", "true", "date"}

class CandidateSkillMiner:
    def __init__(self, repo: BrainRepository):
        self.repo = repo

    def mine_draft_skills(self) -> List[Dict[str, Any]]:
        """
        Extracts candidate draft skills based on:
        1. Failure-then-fix sequences (troubleshooting recipes)
        2. Non-trivial domain commands (docker, dotnet, pip, npm, database tools)
        """
        draft_skills = []

        # 1. Failure-then-fix episodes
        fix_episodes = self.repo.conn.execute(
            """
            SELECT e.*, p.name as project_name
            FROM episodes e
            LEFT JOIN projects p ON e.project_id = p.id
            WHERE e.outcome = 'SUCCESS' AND e.outcome_score > 1.0
            """
        ).fetchall()

        for row in fix_episodes:
            ep = dict(row)
            cmds = json.loads(ep.get("commands_json", "[]"))
            non_trivial_cmds = [c for c in cmds if c.split()[0].split("/")[-1] not in TRIVIAL_COMMANDS]

            if non_trivial_cmds:
                primary_bin = non_trivial_cmds[0].split()[0].split("/")[-1]
                skill_name = f"draft-fix-{primary_bin}-{ep['id'][-8:]}"
                proj_name = ep.get("project_name") or "Global"

                instructions = f"""---
name: {skill_name}
description: Draft troubleshooting recipe for {primary_bin} discovered in {proj_name}.
status: draft
---

> [!IMPORTANT]
> **DRAFT CANDIDATE**: Auto-extracted by Project Brain from a failure-then-fix episode in `{proj_name}`.
> **Human review required** before saving to active skills.

# Troubleshooting Recipe: {primary_bin.capitalize()}

## Observed Context
> {SecretRedactor.redact_text(ep['intent'])}

## Verified Resolution Commands
```bash
{chr(10).join(non_trivial_cmds[:4])}
```

## Resolution Summary
{SecretRedactor.redact_text(ep['resolution'][:350])}
"""
                skill_obj = {
                    "id": skill_name,
                    "name": skill_name,
                    "description": f"Draft troubleshooting recipe for {primary_bin} in {proj_name}",
                    "instructions": instructions,
                    "trigger_pattern": primary_bin,
                    "source_sessions": f"Episode {ep['id']}",
                    "status": "draft",
                    "installed_path": None,
                    "created_at": "",
                    "updated_at": "",
                }
                draft_skills.append(skill_obj)
                self.repo.upsert_skill(skill_obj)

        # 2. Multi-step domain commands (grouped by non-trivial binary)
        all_episodes = self.repo.conn.execute(
            """
            SELECT e.commands_json, p.name as project_name
            FROM episodes e
            LEFT JOIN projects p ON e.project_id = p.id
            WHERE e.outcome = 'SUCCESS'
            """
        ).fetchall()

        grouped_cmds: Dict[str, List[str]] = defaultdict(list)
        grouped_projs: Dict[str, set] = defaultdict(set)

        for row in all_episodes:
            cmds = json.loads(row["commands_json"]) if row["commands_json"] else []
            for c in cmds:
                tokens = c.strip().split()
                if not tokens:
                    continue
                bin_name = tokens[0].split("/")[-1]
                if bin_name not in TRIVIAL_COMMANDS and len(bin_name) > 2:
                    grouped_cmds[bin_name].append(c)
                    if row["project_name"]:
                        grouped_projs[bin_name].add(row["project_name"])

        for bin_name, cmd_list in grouped_cmds.items():
            if len(cmd_list) >= 2:
                distinct_cmds = list(dict.fromkeys(cmd_list))[:6]
                projs = ", ".join(grouped_projs[bin_name]) or "Local Environment"
                skill_name = f"draft-{bin_name}-workflow"

                instructions = f"""---
name: {skill_name}
description: Draft workflow recipe for {bin_name} observed in {projs}.
status: draft
---

> [!IMPORTANT]
> **DRAFT WORKFLOW**: Synthesized from {len(cmd_list)} successful executions across `{projs}`.
> **Human review required** before saving to active skills.

# {bin_name.capitalize()} Workflow Guidelines

## Recommended Command Patterns
```bash
{chr(10).join(distinct_cmds)}
```

## Best Practices
1. Ensure proper environment scoping before running.
2. Verify exit codes before proceeding with dependent tasks.
"""
                skill_obj = {
                    "id": skill_name,
                    "name": skill_name,
                    "description": f"Draft workflow recipe for {bin_name} observed in {projs}",
                    "instructions": instructions,
                    "trigger_pattern": bin_name,
                    "source_sessions": f"Observed {len(cmd_list)} times across {projs}",
                    "status": "draft",
                    "installed_path": None,
                    "created_at": "",
                    "updated_at": "",
                }
                draft_skills.append(skill_obj)
                self.repo.upsert_skill(skill_obj)

        return draft_skills
