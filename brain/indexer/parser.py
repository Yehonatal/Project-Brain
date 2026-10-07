"""Parsers for Antigravity projects, transcripts, steps, and artifacts."""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

class GeminiParser:
    """Parses raw Antigravity and Gemini data structures."""

    @staticmethod
    def parse_project_file(file_path: Path) -> Optional[Dict[str, Any]]:
        """Parses a ~/.gemini/config/projects/<id>.json file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            project_id = data.get("id", file_path.stem)
            name = data.get("name", project_id)
            root_path = None
            default_branch = None

            resources = data.get("projectResources", {}).get("resources", [])
            if resources:
                first_res = resources[0]
                if "folderUri" in first_res:
                    uri = first_res["folderUri"]
                    if uri.startswith("file://"):
                        root_path = uri[7:]
                    else:
                        root_path = uri
                elif "gitFolder" in first_res:
                    git_info = first_res["gitFolder"]
                    uri = git_info.get("folderUri", "")
                    root_path = uri[7:] if uri.startswith("file://") else uri
                    default_branch = git_info.get("defaultBranch", "main")

            updated_at = data.get("updatedAt", "")
            return {
                "id": project_id,
                "name": name,
                "root_path": root_path,
                "default_branch": default_branch,
                "raw_config": json.dumps(data),
                "updated_at": updated_at,
            }
        except Exception:
            return None

    @staticmethod
    def parse_transcript_line(line: str) -> Optional[Dict[str, Any]]:
        """Parses a single JSON line from transcript.jsonl."""
        line = line.strip()
        if not line:
            return None
        try:
            return json.loads(line)
        except Exception:
            return None

    @classmethod
    def parse_conversation_dir(cls, conv_dir: Path, projects_by_path: Dict[str, str]) -> Optional[Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]]:
        """
        Parses a ~/.gemini/antigravity/brain/<conv_id>/ directory.
        Returns: (conversation_dict, steps_list, tool_calls_list, artifacts_list)
        """
        conv_id = conv_dir.name
        transcript_file = conv_dir / ".system_generated" / "logs" / "transcript.jsonl"
        transcript_full = conv_dir / ".system_generated" / "logs" / "transcript_full.jsonl"

        active_file = transcript_full if transcript_full.exists() else transcript_file
        if not active_file.exists():
            return None

        steps_data: List[Dict[str, Any]] = []
        tool_calls_data: List[Dict[str, Any]] = []
        artifacts_data: List[Dict[str, Any]] = []

        title = f"Session {conv_id[:8]}"
        model = "Gemini"
        created_at = None
        updated_at = None
        project_id = None

        # Read transcript
        try:
            with open(active_file, "r", encoding="utf-8") as f:
                for line in f:
                    entry = cls.parse_transcript_line(line)
                    if not entry:
                        continue

                    step_idx = entry.get("step_index", len(steps_data))
                    step_id = f"{conv_id}_{step_idx}"
                    source = entry.get("source", "")
                    stype = entry.get("type", "")
                    status = entry.get("status", "DONE")
                    thinking = entry.get("thinking", "")
                    content = entry.get("content", "")
                    step_time = entry.get("created_at", "")

                    if not created_at and step_time:
                        created_at = step_time
                    if step_time:
                        updated_at = step_time

                    # Extract first user prompt as title
                    if stype == "USER_INPUT" and content and title.startswith("Session "):
                        user_req_match = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", content, re.DOTALL)
                        if user_req_match:
                            clean_prompt = user_req_match.group(1).strip().replace("\n", " ")
                            if clean_prompt:
                                title = clean_prompt[:80] + ("..." if len(clean_prompt) > 80 else "")

                    # Detect model if mentioned
                    if "Gemini" in content:
                        model_match = re.search(r"Gemini [0-9.]+(?: [A-Za-z]+)?", content)
                        if model_match:
                            model = model_match.group(0)

                    # Detect project from tool arguments if not yet matched
                    if not project_id:
                        for tc in entry.get("tool_calls", []):
                            tc_args = tc.get("args", {})
                            if isinstance(tc_args, dict):
                                for path_key in ("Cwd", "DirectoryPath", "SearchDirectory", "TargetFile", "AbsolutePath"):
                                    raw_val = str(tc_args.get(path_key, "")).strip().strip('"\'')
                                    if raw_val:
                                        # Longest prefix match against known projects
                                        matched_pid = None
                                        matched_len = 0
                                        for root_p, pid in projects_by_path.items():
                                            if raw_val == root_p or raw_val.startswith(root_p + "/"):
                                                if len(root_p) > matched_len:
                                                    matched_pid = pid
                                                    matched_len = len(root_p)
                                        if matched_pid:
                                            project_id = matched_pid
                                            break
                            if project_id:
                                break

                    # Parse tool calls
                    parsed_tools = []
                    raw_tool_calls = entry.get("tool_calls", [])
                    for tc in raw_tool_calls:
                        name = tc.get("name", "unknown")
                        args = tc.get("args", {})
                        action = args.get("toolAction", "") if isinstance(args, dict) else ""
                        summary = args.get("toolSummary", "") if isinstance(args, dict) else ""
                        args_json = json.dumps(args) if isinstance(args, dict) else str(args)

                        # Check for output file
                        output_content = ""
                        step_output_file = conv_dir / ".system_generated" / "steps" / str(step_idx) / "output.txt"
                        if step_output_file.exists():
                            try:
                                with open(step_output_file, "r", encoding="utf-8", errors="ignore") as of:
                                    output_content = of.read()
                            except Exception:
                                pass

                        tool_call_obj = {
                            "step_id": step_id,
                            "conversation_id": conv_id,
                            "tool_name": name,
                            "tool_action": action,
                            "tool_summary": summary,
                            "arguments_json": args_json,
                            "output": output_content,
                            "exit_code": 0,
                            "created_at": step_time,
                        }
                        parsed_tools.append(tool_call_obj)
                        tool_calls_data.append(tool_call_obj)

                    step_obj = {
                        "id": step_id,
                        "conversation_id": conv_id,
                        "step_index": step_idx,
                        "source": source,
                        "type": stype,
                        "status": status,
                        "thinking": thinking,
                        "content": content,
                        "created_at": step_time,
                    }
                    steps_data.append(step_obj)

        except Exception as e:
            return None

        # Scan for artifacts directly in conversation directory
        for item in conv_dir.glob("*.md"):
            try:
                content = item.read_text(encoding="utf-8", errors="ignore")
                summary = ""
                art_type = "document"
                if "implementation_plan" in item.name.lower():
                    art_type = "implementation_plan"
                elif "walkthrough" in item.name.lower():
                    art_type = "walkthrough"

                # Extract first heading
                head_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                if head_match:
                    summary = head_match.group(1).strip()

                artifact_obj = {
                    "id": f"{conv_id}_{item.stem}",
                    "conversation_id": conv_id,
                    "project_id": project_id,
                    "file_path": str(item),
                    "file_name": item.name,
                    "artifact_type": art_type,
                    "content": content,
                    "summary": summary,
                    "created_at": created_at,
                }
                artifacts_data.append(artifact_obj)
            except Exception:
                pass

        conv_dict = {
            "id": conv_id,
            "project_id": project_id,
            "title": title,
            "model": model,
            "total_steps": len(steps_data),
            "created_at": created_at or "",
            "updated_at": updated_at or created_at or "",
        }

        return conv_dict, steps_data, tool_calls_data, artifacts_data
