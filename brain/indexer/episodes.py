"""Episode segmentation and outcome labeling engine.

Segments conversation trajectories into cohesive problem-solving episodes:
(Problem Intent → Tool Attempts & Failures → Resolution)
and labels outcomes (SUCCESS, FAILURE, USER_CORRECTED).
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from brain.adapters.base import RawSession, RawStep

@dataclass
class Episode:
    id: str
    conversation_id: str
    project_id: Optional[str]
    episode_index: int
    title: str
    intent: str
    attempts_summary: str
    resolution: str
    outcome: str  # SUCCESS, FAILURE, USER_CORRECTED, IN_PROGRESS
    outcome_score: float
    start_step_index: int
    end_step_index: int
    commands_run: List[str] = field(default_factory=list)
    files_touched: List[str] = field(default_factory=list)
    searchable_text: str = ""
    created_at: str = ""

class EpisodeSegmenter:
    """Segments a RawSession into meaningful episodes and scores outcomes."""

    @classmethod
    def segment_session(cls, session: RawSession) -> List[Episode]:
        steps = session.steps
        if not steps:
            return []

        episodes: List[Episode] = []
        current_user_step: Optional[RawStep] = None
        current_steps: List[RawStep] = []

        # Group steps between USER_INPUT boundaries
        for step in steps:
            if step.step_type == "USER_INPUT":
                if current_user_step and current_steps:
                    ep = cls._build_episode(
                        session=session,
                        user_step=current_user_step,
                        trajectory_steps=current_steps,
                        episode_idx=len(episodes) + 1,
                    )
                    if ep:
                        episodes.append(ep)
                current_user_step = step
                current_steps = [step]
            else:
                current_steps.append(step)

        # Process the final episode
        if current_user_step and current_steps:
            ep = cls._build_episode(
                session=session,
                user_step=current_user_step,
                trajectory_steps=current_steps,
                episode_idx=len(episodes) + 1,
            )
            if ep:
                episodes.append(ep)

        return episodes

    @classmethod
    def _build_episode(
        cls,
        session: RawSession,
        user_step: RawStep,
        trajectory_steps: List[RawStep],
        episode_idx: int,
    ) -> Optional[Episode]:
        # Extract user intent
        raw_intent = user_step.content
        user_req_match = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", raw_intent, re.DOTALL)
        intent = user_req_match.group(1).strip() if user_req_match else raw_intent
        if not intent:
            intent = "User conversation step"

        title = intent.split("\n")[0][:80]

        # Analyze trajectory steps
        commands: List[str] = []
        files: List[str] = []
        tools_used: List[str] = []
        had_error = False
        resolved_after_error = False
        final_response = ""

        for step in trajectory_steps:
            if step.source == "MODEL" and step.content:
                final_response = step.content

            for tc in step.tool_calls:
                tname = tc["tool_name"]
                tools_used.append(tname)
                args = tc.get("arguments", {})

                if tname == "run_command" and isinstance(args, dict):
                    cmd = args.get("CommandLine", "").strip()
                    if cmd:
                        commands.append(cmd)
                    out = tc.get("output", "")
                    if "error" in out.lower() or "failed" in out.lower() or "exit code" in out.lower():
                        had_error = True

                elif tname in ("replace_file_content", "write_to_file", "view_file") and isinstance(args, dict):
                    for path_key in ("TargetFile", "AbsolutePath"):
                        fpath = args.get(path_key, "")
                        if fpath:
                            files.append(fpath.strip('"\''))

        # Check if the subsequent steps resolved an earlier error
        if had_error and final_response and ("error" not in final_response.lower()[:200]):
            resolved_after_error = True

        # Check for user corrections in intent (only on follow-up steps, not initial request)
        correction_cues = ["don't", "do not", "instead", "wrong", "change that", "please avoid", "stop doing"]
        is_user_correction = (user_step.step_index > 0) and any(cue in intent.lower() for cue in correction_cues)

        # Determine outcome and score
        if is_user_correction:
            outcome = "USER_CORRECTED"
            score = 0.8
        elif had_error and not resolved_after_error:
            outcome = "FAILURE"
            score = 0.3
        elif resolved_after_error:
            outcome = "SUCCESS"
            score = 1.2  # Bonus score for fixing an obstacle
        else:
            outcome = "SUCCESS"
            score = 1.0

        # Construct concise summaries
        tools_str = ", ".join(list(dict.fromkeys(tools_used)))
        distinct_cmds = list(dict.fromkeys(commands))[:5]
        distinct_files = list(dict.fromkeys(files))[:5]

        attempts_summary = f"Tools: [{tools_str}]. Commands: {len(distinct_cmds)}. Files touched: {len(distinct_files)}."
        resolution_snippet = final_response[:400] + ("..." if len(final_response) > 400 else "")

        # Rich searchable text for FTS (combining Intent, Commands, Errors, File paths, and Resolution)
        searchable_parts = [
            f"Title: {title}",
            f"Intent: {intent}",
            f"Commands: {' '.join(distinct_cmds)}",
            f"Files: {' '.join(distinct_files)}",
            f"Resolution: {final_response}",
        ]
        searchable_text = "\n".join(searchable_parts)

        return Episode(
            id=f"{session.id}_ep_{episode_idx}",
            conversation_id=session.id,
            project_id=session.project_id,
            episode_index=episode_idx,
            title=title,
            intent=intent,
            attempts_summary=attempts_summary,
            resolution=resolution_snippet,
            outcome=outcome,
            outcome_score=score,
            start_step_index=trajectory_steps[0].step_index,
            end_step_index=trajectory_steps[-1].step_index,
            commands_run=distinct_cmds,
            files_touched=distinct_files,
            searchable_text=searchable_text,
            created_at=user_step.created_at or session.created_at,
        )
