"""Rule Distiller: Transforms user corrections and failure-then-fix sequences into project rules."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from brain.db.repository import BrainRepository
from brain.security.redactor import SecretRedactor

class RuleDistiller:
    def __init__(self, repo: BrainRepository):
        self.repo = repo

    def distill_rules(self) -> List[Dict[str, Any]]:
        """
        Scans all user inputs for course-corrections, negative constraints,
        and developer guidance, generating structured project rules.
        """
        cursor = self.repo.conn.execute(
            """
            SELECT s.id, s.conversation_id, s.step_index, s.content, c.project_id, p.name as project_name, p.root_path as project_root
            FROM steps s
            JOIN conversations c ON s.conversation_id = c.id
            LEFT JOIN projects p ON c.project_id = p.id
            WHERE s.type = 'USER_INPUT' AND s.step_index > 0
            ORDER BY s.created_at DESC
            """
        )

        distilled_rules = []
        correction_patterns = [
            (r"\b(?:don't|do not|never|stop|avoid|rather than|instead of)\b\s+([^\n.]+)", "negative_constraint"),
            (r"\b(?:always|make sure to|remember to|prefer|use \w+ instead)\b\s+([^\n.]+)", "best_practice"),
            (r"\b(?:fix|failed|error|wrong|incorrect)\b\s+([^\n.]+)", "troubleshooting_heuristic"),
        ]

        seen_texts = set()

        for row in cursor.fetchall():
            content = row["content"] or ""
            user_req_match = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", content, re.DOTALL)
            text = user_req_match.group(1).strip() if user_req_match else content

            for pat, rule_type in correction_patterns:
                match = re.search(pat, text, re.IGNORECASE)
                if match:
                    directive = match.group(0).strip()
                    # Clean up directive
                    directive = re.sub(r"\s+", " ", directive)[:180]
                    if directive in seen_texts:
                        continue
                    seen_texts.add(directive)

                    proj_name = row["project_name"] or "Global"
                    conv_id = row["conversation_id"]
                    rule_id = f"rule_{conv_id[:8]}_{row['step_index']}"

                    title = f"Guideline: {directive[:50]}..."
                    markdown_body = f"""# {title}

**Scope**: `{proj_name}`
**Source Session**: `{conv_id[:8]}` (Step {row['step_index']})
**Rule Type**: `{rule_type}`

## Directive
> {SecretRedactor.redact_text(text)}

## Practical Guidance
- Treat this as an explicit developer preference for future agents working in `{proj_name}`.
- Review commands and edits before proposing changes that violate this constraint.
"""

                    rule_obj = {
                        "id": rule_id,
                        "title": title,
                        "project_id": row["project_id"],
                        "project_name": proj_name,
                        "conversation_id": conv_id,
                        "rule_type": rule_type,
                        "content": markdown_body,
                        "created_at": "",
                    }
                    distilled_rules.append(rule_obj)
                    break

        self.repo.upsert_rules(distilled_rules)
        return distilled_rules

    def export_rule_to_project(self, rule_id: str, target_dir: Optional[Path] = None) -> Path:
        """Exports a rule into .agents/rules/<name>.md in the project directory."""
        cursor = self.repo.conn.execute("SELECT * FROM rules WHERE id = ?", (rule_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Rule {rule_id} not found.")

        rule = dict(row)
        clean_title = re.sub(r"[^a-zA-Z0-9_\-]", "_", rule["title"].lower())[:40].strip("_")
        filename = f"{clean_title}.md"

        if target_dir:
            out_dir = Path(target_dir)
        else:
            # Look up project root
            proj = self.repo.get_project(rule["project_id"]) if rule.get("project_id") else None
            if proj and proj.get("root_path"):
                out_dir = Path(proj["root_path"]) / ".agents" / "rules"
            else:
                out_dir = Path.home() / ".gemini" / "antigravity" / "rules"

        out_dir.mkdir(parents=True, exist_ok=True)
        dest_file = out_dir / filename
        dest_file.write_text(rule["content"], encoding="utf-8")
        return dest_file
