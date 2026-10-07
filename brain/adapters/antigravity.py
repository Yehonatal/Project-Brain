"""Pluggable Source Adapter for Google Antigravity and Gemini CLI / Agent Manager."""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from brain.adapters.base import BaseSourceAdapter, RawProject, RawSession, RawStep
from brain.security.redactor import SecretRedactor

logger = logging.getLogger("brain.adapters.antigravity")

class AntigravityAdapter(BaseSourceAdapter):
    """Adapter for ~/.gemini directory structure."""

    def __init__(self, gemini_dir: Path):
        self.gemini_dir = Path(gemini_dir)
        self.antigravity_dir = self.gemini_dir / "antigravity"
        self.brain_dir = self.antigravity_dir / "brain"
        self.projects_dir = self.gemini_dir / "config" / "projects"

    def discover_projects(self) -> List[RawProject]:
        projects: List[RawProject] = []
        if not self.projects_dir.exists():
            return projects

        for pfile in self.projects_dir.glob("*.json"):
            try:
                with open(pfile, "r", encoding="utf-8") as f:
                    data = json.load(f)

                pid = data.get("id", pfile.stem)
                name = data.get("name", pid)
                root_path = None
                default_branch = None

                resources = data.get("projectResources", {}).get("resources", [])
                if resources:
                    res = resources[0]
                    if "folderUri" in res:
                        uri = res["folderUri"]
                        root_path = uri[7:] if uri.startswith("file://") else uri
                    elif "gitFolder" in res:
                        git_f = res["gitFolder"]
                        uri = git_f.get("folderUri", "")
                        root_path = uri[7:] if uri.startswith("file://") else uri
                        default_branch = git_f.get("defaultBranch", "main")

                permissions = data.get("permissionGrants", {})
                projects.append(
                    RawProject(
                        id=pid,
                        name=name,
                        root_path=root_path,
                        default_branch=default_branch,
                        permissions=permissions,
                        raw_config=json.dumps(data),
                        updated_at=data.get("updatedAt", ""),
                    )
                )
            except Exception as e:
                logger.warning("Error reading project file %s: %s", pfile, e)

        return projects

    def discover_sessions(self) -> List[Path]:
        if not self.brain_dir.exists():
            return []
        return [d for d in self.brain_dir.iterdir() if d.is_dir()]

    def parse_session(self, path: Path, projects_by_path: Dict[str, str]) -> Optional[RawSession]:
        conv_id = path.name
        transcript_file = path / ".system_generated" / "logs" / "transcript.jsonl"
        transcript_full = path / ".system_generated" / "logs" / "transcript_full.jsonl"

        active_file = transcript_full if transcript_full.exists() else transcript_file
        if not active_file.exists():
            return None

        steps: List[RawStep] = []
        artifacts: List[Dict[str, Any]] = []
        title = f"Session {conv_id[:8]}"
        model = "Gemini"
        created_at = ""
        updated_at = ""
        project_id = None

        try:
            with open(active_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except Exception:
                        continue

                    step_idx = entry.get("step_index", len(steps))
                    source = entry.get("source", "")
                    stype = entry.get("type", "")
                    status = entry.get("status", "DONE")
                    thinking = SecretRedactor.redact_text(entry.get("thinking", "") or "")
                    content = SecretRedactor.redact_text(entry.get("content", "") or "")
                    step_time = entry.get("created_at", "")

                    if not created_at and step_time:
                        created_at = step_time
                    if step_time:
                        updated_at = step_time

                    # Extract title from initial user prompt
                    if stype == "USER_INPUT" and content and title.startswith("Session "):
                        user_req_match = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", content, re.DOTALL)
                        if user_req_match:
                            clean_prompt = user_req_match.group(1).strip().replace("\n", " ")
                            if clean_prompt:
                                title = clean_prompt[:80] + ("..." if len(clean_prompt) > 80 else "")

                    # Detect model
                    if "Gemini" in content:
                        model_match = re.search(r"Gemini [0-9.]+(?: [A-Za-z]+)?", content)
                        if model_match:
                            model = model_match.group(0)

                    # Extract project from tool arguments
                    if not project_id:
                        for tc in entry.get("tool_calls", []):
                            tc_args = tc.get("args", {})
                            if isinstance(tc_args, dict):
                                for path_key in ("Cwd", "DirectoryPath", "SearchDirectory", "TargetFile", "AbsolutePath"):
                                    raw_val = str(tc_args.get(path_key, "")).strip().strip('"\'')
                                    if raw_val:
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

                    # Parse tool calls with output extraction and secret redaction
                    parsed_tool_calls = []
                    for tc in entry.get("tool_calls", []):
                        name = tc.get("name", "unknown")
                        raw_args = tc.get("args", {})
                        redacted_args = SecretRedactor.redact_json_obj(raw_args)

                        # Check for output file
                        output_content = ""
                        step_output_file = path / ".system_generated" / "steps" / str(step_idx) / "output.txt"
                        if step_output_file.exists():
                            try:
                                with open(step_output_file, "r", encoding="utf-8", errors="ignore") as of:
                                    output_content = SecretRedactor.redact_text(of.read())
                            except Exception:
                                pass

                        action = redacted_args.get("toolAction", "") if isinstance(redacted_args, dict) else ""
                        summary = redacted_args.get("toolSummary", "") if isinstance(redacted_args, dict) else ""

                        parsed_tool_calls.append({
                            "tool_name": name,
                            "tool_action": action,
                            "tool_summary": summary,
                            "arguments": redacted_args,
                            "output": output_content,
                            "created_at": step_time,
                        })

                    steps.append(
                        RawStep(
                            step_index=step_idx,
                            source=source,
                            step_type=stype,
                            status=status,
                            thinking=thinking,
                            content=content,
                            tool_calls=parsed_tool_calls,
                            created_at=step_time,
                        )
                    )

        except Exception as e:
            logger.warning("Error parsing transcript for %s: %s", conv_id, e)
            return None

        # Scan artifacts
        for item in path.glob("*.md"):
            try:
                content = SecretRedactor.redact_text(item.read_text(encoding="utf-8", errors="ignore"))
                art_type = "document"
                if "implementation_plan" in item.name.lower():
                    art_type = "implementation_plan"
                elif "walkthrough" in item.name.lower():
                    art_type = "walkthrough"

                summary = ""
                head_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                if head_match:
                    summary = head_match.group(1).strip()

                artifacts.append({
                    "id": f"{conv_id}_{item.stem}",
                    "conversation_id": conv_id,
                    "project_id": project_id,
                    "file_path": str(item),
                    "file_name": item.name,
                    "artifact_type": art_type,
                    "content": content,
                    "summary": summary,
                    "created_at": created_at,
                })
            except Exception:
                pass

        return RawSession(
            id=conv_id,
            title=title,
            project_id=project_id,
            model=model,
            steps=steps,
            artifacts=artifacts,
            created_at=created_at or "",
            updated_at=updated_at or created_at or "",
        )
