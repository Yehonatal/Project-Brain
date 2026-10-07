"""Memex search engine leveraging SQLite FTS5 for sub-millisecond retrieval."""

from typing import Any, Dict, List, Optional
from brain.db.repository import BrainRepository

class MemexSearchEngine:
    def __init__(self, repo: BrainRepository):
        self.repo = repo

    def query(
        self,
        text: str,
        project_id: Optional[str] = None,
        tool_filter: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search across conversations, thoughts, tool inputs, and outputs.
        Supports project scoping and tool filtering.
        """
        results = self.repo.search(text, project_id=project_id, limit=limit)
        
        # Additional in-memory tool filtering if requested
        if tool_filter:
            tool_filter_lower = tool_filter.lower()
            filtered = []
            for r in results:
                tool_snippet = (r.get("tool_snippet") or "").lower()
                if tool_filter_lower in tool_snippet:
                    filtered.append(r)
            return filtered
            
        return results
