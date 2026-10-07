"""Synthesizes project rules (.agents/rules/*.md) from user corrections and constraints."""

import re
from pathlib import Path
from typing import Any, Dict, List
from brain.db.repository import BrainRepository
from brain.synthesizer.pattern_miner import PatternMiner

class RuleDistiller:
    def __init__(self, repo: BrainRepository):
        self.repo = repo
        self.miner = PatternMiner(repo)

    def distill_rules(self) -> List[Dict[str, Any]]:
        """Distills candidate rules from user corrections and prompt steering."""
        corrections = self.miner.mine_user_corrections()
        rules = []

        for idx, corr in enumerate(corrections):
            text = corr["text"]
            proj = corr["project_name"]
            conv_id = corr["conversation_id"]

            rule_title = f"Guideline from {proj} Session"
            # Summarize the rule
            rule_content = f"""# {rule_title}

**Context**: Derived from developer guidance in project `{proj}` (Session `{conv_id[:8]}`).

## Instruction
> {text}

## Key Directives
- Follow developer guidance consistently across future sessions.
- Avoid repeating previously identified errors or suboptimal patterns.
"""
            rules.append({
                "id": f"rule_{idx+1}",
                "title": rule_title,
                "project_name": proj,
                "conversation_id": conv_id,
                "content": rule_content,
            })

        return rules
