"""Agent-first Model Context Protocol (MCP) server for Project Brain.

Designed specifically for AI agents (Antigravity, Gemini, Claude):
- Compact outputs under strict token budgets
- Accurate citations [session_id:step_range]
- Pre-flight resource: brain_get_project_learnings
- Strict project isolation by default
- Double secret redaction on all outgoing tool results
"""

import json
import logging
import sys
from typing import Any, Dict, List, Optional
from brain.config import CONFIG, BrainConfig
from brain.db.repository import BrainRepository
from brain.security.redactor import SecretRedactor

logger = logging.getLogger("brain.mcp.server")

class BrainMCPServer:
    def __init__(self, repo: BrainRepository, config: BrainConfig = CONFIG):
        self.repo = repo
        self.config = config

    def handle_request(self, req: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        method = req.get("method")
        msg_id = req.get("id")
        params = req.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "project-brain", "version": "0.1.0"},
                    "capabilities": {"tools": {}},
                },
            }

        elif method == "notifications/initialized":
            return None

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": "brain_get_project_learnings",
                            "description": "PRE-FLIGHT CHECK: Call this at the start of any task in a repository to retrieve essential gotchas, past rules, allowed command patterns, and successful workflows for this project.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "project_name": {
                                        "type": "string",
                                        "description": "Name or identifier of the project (e.g., 'Project-Brain', 'odoo-addons', 'erp').",
                                    },
                                    "limit": {
                                        "type": "integer",
                                        "description": "Max number of past learnings to return (default 5).",
                                        "default": 5,
                                    },
                                },
                                "required": ["project_name"],
                            },
                        },
                        {
                            "name": "brain_search_episodes",
                            "description": "Search past problem-solving episodes and proven solutions across sessions. Returns compact answers, verified commands, and citations.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "Search query, error message, command name, or technical concept.",
                                    },
                                    "project_name": {
                                        "type": "string",
                                        "description": "Optional project scope to prevent cross-project contamination.",
                                    },
                                    "only_success": {
                                        "type": "boolean",
                                        "description": "Only return verified successful episodes (default: true).",
                                        "default": True,
                                    },
                                    "limit": {
                                        "type": "integer",
                                        "description": "Max results (default 3, keep compact for token budget).",
                                        "default": 3,
                                    },
                                },
                                "required": ["query"],
                            },
                        },
                        {
                            "name": "brain_get_episode_details",
                            "description": "Fetch complete step details, tool arguments, and output for a specific cited episode.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "episode_id": {
                                        "type": "string",
                                        "description": "The episode ID cited in previous search results.",
                                    },
                                },
                                "required": ["episode_id"],
                            },
                        },
                    ]
                },
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            result = self._execute_tool(tool_name, arguments)
            return {"jsonrpc": "2.0", "id": msg_id, "result": result}

        elif method == "ping":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

    def _execute_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if name == "brain_get_project_learnings":
            proj_name = args.get("project_name", "")
            limit = args.get("limit", 5)
            content = self._tool_project_learnings(proj_name, limit)
        elif name == "brain_search_episodes":
            query = args.get("query", "")
            proj_name = args.get("project_name")
            only_success = args.get("only_success", True)
            limit = args.get("limit", 3)
            content = self._tool_search_episodes(query, proj_name, only_success, limit)
        elif name == "brain_get_episode_details":
            ep_id = args.get("episode_id", "")
            content = self._tool_episode_details(ep_id)
        else:
            content = f"Error: Unknown tool '{name}'"

        # Apply secondary secret redaction prior to sending to agent
        safe_content = SecretRedactor.redact_text(content)
        return {"content": [{"type": "text", "text": safe_content}]}

    def _tool_project_learnings(self, project_name: str, limit: int) -> str:
        # Match project
        matched_proj = None
        for p in self.repo.get_projects():
            if p["name"].lower() == project_name.lower() or p["id"] == project_name:
                matched_proj = p
                break

        if not matched_proj:
            return f"No recorded project found matching '{project_name}'. Available projects: {', '.join(p['name'] for p in self.repo.get_projects()[:8])}"

        pid = matched_proj["id"]
        rules = self.repo.get_rules(project_id=pid)
        episodes = self.repo.search_episodes(project_name, project_id=pid, limit=limit, min_outcome="SUCCESS")

        lines = [f"# Project Learnings: {matched_proj['name']}"]
        if matched_proj.get("root_path"):
            lines.append(f"Root: `{matched_proj['root_path']}`")

        # Config permissions / allowed commands
        raw_cfg = json.loads(matched_proj.get("raw_config", "{}")) if matched_proj.get("raw_config") else {}
        grants = raw_cfg.get("permissionGrants", {}).get("permissionGrants", {}).get("allow", [])
        if grants:
            lines.append("\n### Approved Command & Access Grants:")
            for g in grants[:6]:
                lines.append(f"- `{g}`")

        # Distilled Rules / Constraints
        if rules:
            lines.append("\n### Rules & Developer Constraints:")
            for r in rules[:4]:
                lines.append(f"- **{r['title']}**: {r['content'][:180]}...")

        # Past Successful Episodes
        if episodes:
            lines.append("\n### Verified Past Solutions:")
            for ep in episodes[:4]:
                citation = f"[{ep['conversation_id'][:8]}:{ep['start_step_index']}-{ep['end_step_index']}]"
                cmds = " | ".join(f"`{c}`" for c in ep["commands_run"][:2])
                lines.append(f"- **{ep['title']}** {citation}")
                if cmds:
                    lines.append(f"  Commands: {cmds}")
                lines.append(f"  Resolution: {ep['resolution'][:150]}...")
        else:
            lines.append("\nNo previous successful episodes recorded yet for this project.")

        return "\n".join(lines)

    def _tool_search_episodes(self, query: str, project_name: Optional[str], only_success: bool, limit: int) -> str:
        project_id = None
        if project_name:
            for p in self.repo.get_projects():
                if p["name"].lower() == project_name.lower():
                    project_id = p["id"]
                    break

        min_outcome = "SUCCESS" if only_success else None
        results = self.repo.search_episodes(query, project_id=project_id, limit=limit, min_outcome=min_outcome)

        if not results:
            return f"No matching episodes found for query: '{query}'."

        lines = [f"Found {len(results)} relevant episode(s):\n"]
        for ep in results:
            citation = f"[{ep['conversation_id'][:8]}:{ep['start_step_index']}-{ep['end_step_index']}]"
            proj = f"({ep['project_name']})" if ep.get("project_name") else ""
            lines.append(f"### {ep['title']} {proj} {citation}")
            lines.append(f"- **Episode ID**: `{ep['id']}`")
            lines.append(f"- **Outcome**: {ep['outcome']} (score: {ep['score']})")
            if ep["commands_run"]:
                lines.append(f"- **Verified Commands**:\n```bash\n" + "\n".join(ep["commands_run"][:3]) + "\n```")
            lines.append(f"- **Summary**: {ep['resolution'][:220]}")
            lines.append("")

        return "\n".join(lines).strip()

    def _tool_episode_details(self, episode_id: str) -> str:
        cursor = self.repo.conn.execute("SELECT * FROM episodes WHERE id = ?", (episode_id,))
        row = cursor.fetchone()
        if not row:
            return f"Episode '{episode_id}' not found."

        ep = dict(row)
        conv_id = ep["conversation_id"]
        start_step = ep["start_step_index"]
        end_step = ep["end_step_index"]

        steps = self.repo.conn.execute(
            "SELECT * FROM steps WHERE conversation_id = ? AND step_index >= ? AND step_index <= ? ORDER BY step_index ASC",
            (conv_id, start_step, end_step),
        ).fetchall()

        lines = [f"# Episode Details: {ep['title']}", f"Outcome: {ep['outcome']} | Conversation: `{conv_id}`\n"]
        for s in steps:
            s_dict = dict(s)
            lines.append(f"## Step {s_dict['step_index']} ({s_dict['type']})")
            if s_dict["thinking"]:
                lines.append(f"**Thinking**: {s_dict['thinking'][:200]}...")
            if s_dict["content"]:
                lines.append(f"{s_dict['content'][:300]}")

            # Tool calls
            tcs = self.repo.conn.execute("SELECT * FROM tool_calls WHERE step_id = ?", (s_dict["id"],)).fetchall()
            for tc in tcs:
                t_dict = dict(tc)
                lines.append(f"- **Tool**: `{t_dict['tool_name']}` ({t_dict['tool_summary'] or ''})")
                if t_dict["arguments_json"]:
                    lines.append(f"  Args: `{t_dict['arguments_json'][:150]}`")
                if t_dict["output"]:
                    lines.append(f"  Output: {t_dict['output'][:150]}...")
            lines.append("")

        return "\n".join(lines)[:3500]  # Enforce strict token budget

    def run_stdio(self):
        """Standard IO JSON-RPC loop for MCP integration."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                res = self.handle_request(req)
                if res:
                    sys.stdout.write(json.dumps(res) + "\n")
                    sys.stdout.flush()
            except Exception as e:
                err_res = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {str(e)}"},
                }
                sys.stdout.write(json.dumps(err_res) + "\n")
                sys.stdout.flush()
