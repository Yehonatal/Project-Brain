"""Knowledge Graph generator connecting Projects, Sessions, Tools, and Artifacts."""

from typing import Any, Dict, List
from brain.db.repository import BrainRepository

class KnowledgeGraphBuilder:
    def __init__(self, repo: BrainRepository):
        self.repo = repo

    def build_graph(self) -> Dict[str, List[Dict[str, Any]]]:
        """Builds a node-edge graph suitable for interactive visualization."""
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        node_ids = set()

        projects = self.repo.get_projects()
        conversations = self.repo.get_conversations(limit=200)

        # Add project nodes
        for p in projects:
            p_node_id = f"proj_{p['id']}"
            if p_node_id not in node_ids:
                nodes.append({
                    "id": p_node_id,
                    "label": p["name"],
                    "type": "project",
                    "path": p.get("root_path", ""),
                })
                node_ids.add(p_node_id)

        # Track tools used
        tool_counts: Dict[str, int] = {}

        # Add conversation nodes and edges to projects
        for c in conversations:
            c_node_id = f"conv_{c['id']}"
            if c_node_id not in node_ids:
                nodes.append({
                    "id": c_node_id,
                    "label": c["title"][:40] + ("..." if len(c["title"]) > 40 else ""),
                    "type": "conversation",
                    "steps": c["total_steps"],
                    "model": c.get("model", ""),
                })
                node_ids.add(c_node_id)

            if c.get("project_id"):
                p_node_id = f"proj_{c['project_id']}"
                if p_node_id in node_ids:
                    edges.append({
                        "source": p_node_id,
                        "target": c_node_id,
                        "label": "contains",
                        "weight": 1,
                    })

            # Fetch tools used in this conversation
            cursor = self.repo.conn.execute(
                "SELECT tool_name, count(*) as cnt FROM tool_calls WHERE conversation_id = ? GROUP BY tool_name",
                (c["id"],),
            )
            for row in cursor.fetchall():
                tname = row["tool_name"]
                t_node_id = f"tool_{tname}"
                if t_node_id not in node_ids:
                    nodes.append({
                        "id": t_node_id,
                        "label": tname,
                        "type": "tool",
                    })
                    node_ids.add(t_node_id)

                edges.append({
                    "source": c_node_id,
                    "target": t_node_id,
                    "label": "executed",
                    "weight": row["cnt"],
                })

        # Add artifact nodes
        artifacts = self.repo.get_artifacts()
        for a in artifacts:
            a_node_id = f"art_{a['id']}"
            if a_node_id not in node_ids:
                nodes.append({
                    "id": a_node_id,
                    "label": a["file_name"],
                    "type": "artifact",
                    "artifact_type": a["artifact_type"],
                })
                node_ids.add(a_node_id)

            c_node_id = f"conv_{a['conversation_id']}"
            if c_node_id in node_ids:
                edges.append({
                    "source": c_node_id,
                    "target": a_node_id,
                    "label": "produced",
                    "weight": 1,
                })

        return {"nodes": nodes, "edges": edges}
