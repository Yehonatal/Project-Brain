"""Cross-session pattern miner to extract recurring workflows, commands, and rules."""

import json
import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple
from brain.db.repository import BrainRepository

class PatternMiner:
    def __init__(self, repo: BrainRepository):
        self.repo = repo

    def mine_command_recipes(self, min_frequency: int = 1) -> List[Dict[str, Any]]:
        """Mines recurring terminal commands across all projects."""
        cursor = self.repo.conn.execute(
            """
            SELECT tc.arguments_json, tc.conversation_id, tc.output, c.project_id, p.name as project_name
            FROM tool_calls tc
            JOIN conversations c ON tc.conversation_id = c.id
            LEFT JOIN projects p ON c.project_id = p.id
            WHERE tc.tool_name = 'run_command'
            """
        )

        recipes_by_binary: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for row in cursor.fetchall():
            try:
                args = json.loads(row["arguments_json"])
                cmd = args.get("CommandLine", "").strip()
                if not cmd:
                    continue

                # Extract primary binary/tool
                first_token = cmd.split()[0].split("/")[-1]
                if first_token in ("echo", "cat", "ls", "rm", "mkdir", "cd", "head", "tail"):
                    # Common shell utilities
                    continue

                recipes_by_binary[first_token].append({
                    "command": cmd,
                    "action": args.get("toolAction", ""),
                    "summary": args.get("toolSummary", ""),
                    "project_name": row["project_name"] or "Global",
                    "conversation_id": row["conversation_id"],
                })
            except Exception:
                pass

        mined_recipes = []
        for binary, instances in recipes_by_binary.items():
            if len(instances) >= min_frequency:
                # Group distinct commands
                distinct_cmds = list({inst["command"] for inst in instances})
                projects = list({inst["project_name"] for inst in instances})
                mined_recipes.append({
                    "binary": binary,
                    "frequency": len(instances),
                    "projects": projects,
                    "distinct_commands": distinct_cmds[:10],
                    "sample_actions": list({inst["summary"] for inst in instances if inst["summary"]})[:5],
                })

        mined_recipes.sort(key=lambda x: x["frequency"], reverse=True)
        return mined_recipes

    def mine_tool_chains(self, chain_length: int = 3, min_support: int = 2) -> List[Dict[str, Any]]:
        """Mines recurring tool sequence n-grams across sessions."""
        cursor = self.repo.conn.execute(
            "SELECT conversation_id, tool_name FROM tool_calls ORDER BY conversation_id, id ASC"
        )
        tools_by_conv: Dict[str, List[str]] = defaultdict(list)
        for row in cursor.fetchall():
            tools_by_conv[row["conversation_id"]].append(row["tool_name"])

        ngram_counts: Counter = Counter()
        for conv_id, tools in tools_by_conv.items():
            if len(tools) < chain_length:
                continue
            for i in range(len(tools) - chain_length + 1):
                ngram = tuple(tools[i : i + chain_length])
                ngram_counts[ngram] += 1

        results = []
        for ngram, count in ngram_counts.most_common(10):
            if count >= min_support:
                results.append({
                    "tool_chain": list(ngram),
                    "frequency": count,
                    "description": f"Workflow sequence: {' ➔ '.join(ngram)}",
                })
        return results

    def mine_user_corrections(self) -> List[Dict[str, Any]]:
        """Detects user corrections and feedback to synthesize rules."""
        correction_patterns = [
            r"\b(don't|do not|never|stop|instead of|rather than|please avoid)\b",
            r"\b(fix|failed|error|wrong|incorrect|not working)\b",
            r"\b(always|make sure to|remember to|use \w+ instead)\b",
        ]
        
        cursor = self.repo.conn.execute(
            """
            SELECT s.conversation_id, s.content, c.project_id, p.name as project_name
            FROM steps s
            JOIN conversations c ON s.conversation_id = c.id
            LEFT JOIN projects p ON c.project_id = p.id
            WHERE s.type = 'USER_INPUT' AND s.step_index > 0
            """
        )

        corrections = []
        for row in cursor.fetchall():
            content = row["content"]
            user_req_match = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", content, re.DOTALL)
            text = user_req_match.group(1).strip() if user_req_match else content

            for pat in correction_patterns:
                if re.search(pat, text, re.IGNORECASE):
                    corrections.append({
                        "conversation_id": row["conversation_id"],
                        "project_name": row["project_name"] or "Global",
                        "text": text[:300],
                    })
                    break

        return corrections
