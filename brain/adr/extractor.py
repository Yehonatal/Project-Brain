"""Extracts Architecture Decision Records (ADRs) from implementation plans and walkthroughs."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from brain.db.repository import BrainRepository

class ADRExtractor:
    def __init__(self, repo: BrainRepository):
        self.repo = repo

    def extract_from_artifacts(self) -> List[Dict[str, Any]]:
        """Parses all implementation plans in the repository into structured ADRs."""
        artifacts = self.repo.get_artifacts()
        adrs = []

        for art in artifacts:
            if art["artifact_type"] not in ("implementation_plan", "walkthrough", "document"):
                continue

            content = art["content"] or ""
            if not content:
                continue

            # Extract Title
            title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else art["file_name"]
            if title.startswith("Implementation Plan:"):
                title = title.replace("Implementation Plan:", "").strip()

            # Extract Context
            context = ""
            ctx_match = re.search(r"(?:##\s*(?:Problem|Background|Context|Goal)[^\n]*\n)(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
            if ctx_match:
                context = ctx_match.group(1).strip()
            else:
                # Grab first paragraph after title
                paras = [p.strip() for p in content.split("\n\n") if p.strip() and not p.strip().startswith("#")]
                if paras:
                    context = paras[0]

            # Extract Decision / Proposed Changes
            decision = ""
            dec_match = re.search(r"(?:##\s*(?:Proposed Changes|Solution|Decision|Approach)[^\n]*\n)(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
            if dec_match:
                decision = dec_match.group(1).strip()

            # Extract Verification / Consequences
            consequences = ""
            ver_match = re.search(r"(?:##\s*(?:Verification|Consequences|Testing)[^\n]*\n)(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
            if ver_match:
                consequences = ver_match.group(1).strip()

            adr_id = f"adr_{art['id']}"
            madr_content = f"""# ADR: {title}

* Status: Accepted
* Date: {art['created_at'] or 'Recent'}
* Source Session: `{art['conversation_id'][:8]}`
* Artifact: `{art['file_name']}`

## Context and Problem Statement
{context or 'Architectural changes initiated during agent session.'}

## Decision Outcome
{decision or 'Approved changes executed according to the implementation plan.'}

## Verification & Consequences
{consequences or 'Verified via build tests and walkthrough validation.'}
"""

            adr_obj = {
                "id": adr_id,
                "title": title,
                "project_id": art["project_id"],
                "conversation_id": art["conversation_id"],
                "status": "accepted",
                "context": context,
                "decision": decision,
                "consequences": consequences,
                "raw_markdown": madr_content,
                "created_at": art["created_at"],
            }
            adrs.append(adr_obj)
            self.repo.upsert_adr(adr_obj)

        return adrs
