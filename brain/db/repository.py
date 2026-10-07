"""Repository and data access layer with dual FTS5 retrieval and outcome-weighted scoring."""

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional
from brain.db.schema import init_db
from brain.indexer.episodes import Episode

class BrainRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._local = threading.local()
        # Ensure schema and FTS tables are initialized
        init_conn = init_db(db_path)
        init_conn.close()

    @property
    def conn(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=30.0)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA foreign_keys = ON;")
            self._local.conn = conn
        return conn

    # -------------------------------------------------------------
    # Projects
    # -------------------------------------------------------------
    def upsert_project(self, project: Dict[str, Any]):
        sql = """
        INSERT INTO projects (id, name, root_path, default_branch, raw_config, updated_at)
        VALUES (:id, :name, :root_path, :default_branch, :raw_config, :updated_at)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            root_path = excluded.root_path,
            default_branch = excluded.default_branch,
            raw_config = excluded.raw_config,
            updated_at = excluded.updated_at
        """
        self.conn.execute(sql, project)
        self.conn.commit()

    def get_projects(self) -> List[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM projects ORDER BY name ASC")
        return [dict(row) for row in cursor.fetchall()]

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # -------------------------------------------------------------
    # Conversations
    # -------------------------------------------------------------
    def upsert_conversation(self, conv: Dict[str, Any]):
        sql = """
        INSERT INTO conversations (id, project_id, title, model, total_steps, created_at, updated_at)
        VALUES (:id, :project_id, :title, :model, :total_steps, :created_at, :updated_at)
        ON CONFLICT(id) DO UPDATE SET
            project_id = coalesce(excluded.project_id, conversations.project_id),
            title = coalesce(excluded.title, conversations.title),
            model = coalesce(excluded.model, conversations.model),
            total_steps = excluded.total_steps,
            updated_at = excluded.updated_at
        """
        self.conn.execute(sql, conv)
        self.conn.commit()

    def get_conversations(self, project_id: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        if project_id:
            sql = """
            SELECT c.*, p.name as project_name
            FROM conversations c
            LEFT JOIN projects p ON c.project_id = p.id
            WHERE c.project_id = ?
            ORDER BY c.created_at DESC LIMIT ? OFFSET ?
            """
            cursor = self.conn.execute(sql, (project_id, limit, offset))
        else:
            sql = """
            SELECT c.*, p.name as project_name
            FROM conversations c
            LEFT JOIN projects p ON c.project_id = p.id
            ORDER BY c.created_at DESC LIMIT ? OFFSET ?
            """
            cursor = self.conn.execute(sql, (limit, offset))
        return [dict(row) for row in cursor.fetchall()]

    def get_conversation(self, conv_id: str) -> Optional[Dict[str, Any]]:
        sql = """
        SELECT c.*, p.name as project_name, p.root_path as project_root
        FROM conversations c
        LEFT JOIN projects p ON c.project_id = p.id
        WHERE c.id = ?
        """
        cursor = self.conn.execute(sql, (conv_id,))
        row = cursor.fetchone()
        if not row:
            return None
        res = dict(row)
        res["steps"] = self.get_steps(conv_id)
        res["episodes"] = self.get_episodes_for_conversation(conv_id)
        res["artifacts"] = self.get_artifacts(conv_id)
        return res

    # -------------------------------------------------------------
    # Steps & Tool Calls
    # -------------------------------------------------------------
    def upsert_step(self, step: Dict[str, Any], tool_calls: Optional[List[Dict[str, Any]]] = None):
        step_sql = """
        INSERT INTO steps (id, conversation_id, step_index, source, type, status, thinking, content, created_at)
        VALUES (:id, :conversation_id, :step_index, :source, :type, :status, :thinking, :content, :created_at)
        ON CONFLICT(id) DO UPDATE SET
            status = excluded.status,
            thinking = excluded.thinking,
            content = excluded.content
        """
        self.conn.execute(step_sql, step)

        if tool_calls:
            self.conn.execute("DELETE FROM tool_calls WHERE step_id = ?", (step["id"],))
            for tc in tool_calls:
                tc_sql = """
                INSERT INTO tool_calls (step_id, conversation_id, tool_name, tool_action, tool_summary, arguments_json, output, exit_code, created_at)
                VALUES (:step_id, :conversation_id, :tool_name, :tool_action, :tool_summary, :arguments_json, :output, :exit_code, :created_at)
                """
                self.conn.execute(tc_sql, tc)

        self.conn.commit()

    def get_steps(self, conv_id: str) -> List[Dict[str, Any]]:
        cursor = self.conn.execute(
            "SELECT * FROM steps WHERE conversation_id = ? ORDER BY step_index ASC", (conv_id,)
        )
        steps = [dict(row) for row in cursor.fetchall()]
        if not steps:
            return []

        # Batch fetch all tool calls for this session
        tc_cursor = self.conn.execute(
            "SELECT * FROM tool_calls WHERE conversation_id = ? ORDER BY id ASC", (conv_id,)
        )
        tc_by_step: Dict[str, List[Dict[str, Any]]] = {}
        for tr in tc_cursor.fetchall():
            tc_dict = dict(tr)
            sid = str(tc_dict["step_id"])
            if sid not in tc_by_step:
                tc_by_step[sid] = []
            tc_by_step[sid].append(tc_dict)

        for step in steps:
            step["tool_calls"] = tc_by_step.get(str(step["id"]), [])
        return steps

    # -------------------------------------------------------------
    # Episodes (Problem → Attempts → Resolution)
    # -------------------------------------------------------------
    def upsert_episode(self, ep: Episode):
        sql = """
        INSERT INTO episodes (
            id, conversation_id, project_id, episode_index, title, intent,
            attempts_summary, resolution, outcome, outcome_score,
            start_step_index, end_step_index, commands_json, files_json, created_at
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        ON CONFLICT(id) DO UPDATE SET
            title = excluded.title,
            intent = excluded.intent,
            attempts_summary = excluded.attempts_summary,
            resolution = excluded.resolution,
            outcome = excluded.outcome,
            outcome_score = excluded.outcome_score,
            commands_json = excluded.commands_json,
            files_json = excluded.files_json
        """
        self.conn.execute(
            sql,
            (
                ep.id,
                ep.conversation_id,
                ep.project_id,
                ep.episode_index,
                ep.title,
                ep.intent,
                ep.attempts_summary,
                ep.resolution,
                ep.outcome,
                ep.outcome_score,
                ep.start_step_index,
                ep.end_step_index,
                json.dumps(ep.commands_run),
                json.dumps(ep.files_touched),
                ep.created_at,
            ),
        )

        # Index into FTS Trigram
        self.conn.execute("DELETE FROM fts_episodes_trigram WHERE episode_id = ?", (ep.id,))
        self.conn.execute(
            "INSERT INTO fts_episodes_trigram (episode_id, conversation_id, project_id, searchable_text) VALUES (?, ?, ?, ?)",
            (ep.id, ep.conversation_id, ep.project_id or "", ep.searchable_text),
        )

        # Index into FTS Porter
        self.conn.execute("DELETE FROM fts_episodes_porter WHERE episode_id = ?", (ep.id,))
        self.conn.execute(
            "INSERT INTO fts_episodes_porter (episode_id, conversation_id, project_id, title, intent, resolution) VALUES (?, ?, ?, ?, ?, ?)",
            (ep.id, ep.conversation_id, ep.project_id or "", ep.title, ep.intent, ep.resolution),
        )
        self.conn.commit()

    def get_episodes_for_conversation(self, conv_id: str) -> List[Dict[str, Any]]:
        cursor = self.conn.execute(
            "SELECT * FROM episodes WHERE conversation_id = ? ORDER BY episode_index ASC", (conv_id,)
        )
        rows = [dict(r) for r in cursor.fetchall()]
        for r in rows:
            r["commands_run"] = json.loads(r["commands_json"]) if r["commands_json"] else []
            r["files_touched"] = json.loads(r["files_json"]) if r["files_json"] else []
        return rows

    # -------------------------------------------------------------
    # Dual FTS5 Search with Reciprocal Rank Fusion & Outcome Weighting
    # -------------------------------------------------------------
    def search_episodes(
        self,
        query: str,
        project_id: Optional[str] = None,
        limit: int = 15,
        min_outcome: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Searches episodes using dual-tokenizer FTS5:
        - Trigram FTS for paths, code symbols, error codes
        - Porter FTS for natural language intent
        Fuses ranks and multiplies by outcome score (favoring SUCCESS and fixes).
        """
        clean_q = "".join(c if c.isalnum() or c in (" ", "-", "_", "/", ".") else " " for c in query).strip()
        if not clean_q:
            return []

        scores: Dict[str, float] = {}

        # 1. Porter search (natural language)
        porter_tokens = " ".join(f'"{w}"*' for w in clean_q.split() if len(w) > 1)
        if porter_tokens:
            try:
                porter_sql = "SELECT episode_id, bm25(fts_episodes_porter) as rank FROM fts_episodes_porter WHERE fts_episodes_porter MATCH ? LIMIT 30"
                cursor = self.conn.execute(porter_sql, (porter_tokens,))
                for i, row in enumerate(cursor.fetchall()):
                    # Reciprocal Rank Fusion (RRF): 1 / (60 + rank)
                    scores[row["episode_id"]] = scores.get(row["episode_id"], 0.0) + (1.0 / (60.0 + i))
            except Exception:
                pass

        # 2. Trigram search (identifiers, commands, paths, error strings)
        trigram_tokens = " ".join(f'"{w}"' for w in clean_q.split() if len(w) >= 3)
        if trigram_tokens:
            try:
                trigram_sql = "SELECT episode_id, bm25(fts_episodes_trigram) as rank FROM fts_episodes_trigram WHERE fts_episodes_trigram MATCH ? LIMIT 30"
                cursor = self.conn.execute(trigram_sql, (trigram_tokens,))
                for i, row in enumerate(cursor.fetchall()):
                    scores[row["episode_id"]] = scores.get(row["episode_id"], 0.0) + (1.2 / (60.0 + i))
            except Exception:
                pass

        if not scores:
            # Fallback to LIKE
            like_sql = "SELECT id as episode_id FROM episodes WHERE title LIKE ? OR intent LIKE ? LIMIT 20"
            term = f"%{clean_q}%"
            for r in self.conn.execute(like_sql, (term, term)).fetchall():
                scores[r["episode_id"]] = 0.5

        # Fetch episode details and apply outcome weighting
        ranked_episodes = []
        for ep_id, rrf_score in scores.items():
            ep_cursor = self.conn.execute(
                """
                SELECT e.*, c.title as conv_title, p.name as project_name
                FROM episodes e
                JOIN conversations c ON e.conversation_id = c.id
                LEFT JOIN projects p ON e.project_id = p.id
                WHERE e.id = ?
                """,
                (ep_id,),
            )
            row = ep_cursor.fetchone()
            if not row:
                continue

            ep_data = dict(row)

            # Apply project scoping if requested
            if project_id and ep_data["project_id"] != project_id:
                continue

            # Apply min_outcome filter
            if min_outcome and ep_data["outcome"] != min_outcome:
                continue

            # Multiplier: Outcome weighting! Rank "what worked" > "what was tried"
            final_score = rrf_score * float(ep_data.get("outcome_score", 1.0))
            ep_data["score"] = round(final_score, 4)
            ep_data["commands_run"] = json.loads(ep_data["commands_json"]) if ep_data.get("commands_json") else []
            ep_data["files_touched"] = json.loads(ep_data["files_json"]) if ep_data.get("files_json") else []
            ranked_episodes.append(ep_data)

        # Sort by final score descending
        ranked_episodes.sort(key=lambda x: x["score"], reverse=True)
        return ranked_episodes[:limit]

    # -------------------------------------------------------------
    # Rules (Distilled from corrections)
    # -------------------------------------------------------------
    def upsert_rule(self, rule: Dict[str, Any]):
        sql = """
        INSERT INTO rules (id, title, project_id, conversation_id, rule_type, content, created_at)
        VALUES (:id, :title, :project_id, :conversation_id, :rule_type, :content, :created_at)
        ON CONFLICT(id) DO UPDATE SET
            title = excluded.title,
            content = excluded.content
        """
        self.conn.execute(sql, rule)
        self.conn.commit()

    def get_rules(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if project_id:
            sql = "SELECT r.*, p.name as project_name FROM rules r LEFT JOIN projects p ON r.project_id = p.id WHERE r.project_id = ? ORDER BY r.created_at DESC"
            cursor = self.conn.execute(sql, (project_id,))
        else:
            sql = "SELECT r.*, p.name as project_name FROM rules r LEFT JOIN projects p ON r.project_id = p.id ORDER BY r.created_at DESC"
            cursor = self.conn.execute(sql)
        return [dict(row) for row in cursor.fetchall()]

    # -------------------------------------------------------------
    # Artifacts & ADRs & Skills
    # -------------------------------------------------------------
    def upsert_artifact(self, artifact: Dict[str, Any]):
        sql = """
        INSERT INTO artifacts (id, conversation_id, project_id, file_path, file_name, artifact_type, content, summary, created_at)
        VALUES (:id, :conversation_id, :project_id, :file_path, :file_name, :artifact_type, :content, :summary, :created_at)
        ON CONFLICT(id) DO UPDATE SET
            content = excluded.content,
            summary = excluded.summary
        """
        self.conn.execute(sql, artifact)
        self.conn.commit()

    def get_artifacts(self, conv_id: Optional[str] = None, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if conv_id:
            cursor = self.conn.execute("SELECT * FROM artifacts WHERE conversation_id = ? ORDER BY created_at DESC", (conv_id,))
        elif project_id:
            cursor = self.conn.execute("SELECT * FROM artifacts WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
        else:
            cursor = self.conn.execute("SELECT * FROM artifacts ORDER BY created_at DESC LIMIT 100")
        return [dict(row) for row in cursor.fetchall()]

    def upsert_adr(self, adr: Dict[str, Any]):
        sql = """
        INSERT INTO adrs (id, title, project_id, conversation_id, status, context, decision, consequences, raw_markdown, created_at)
        VALUES (:id, :title, :project_id, :conversation_id, :status, :context, :decision, :consequences, :raw_markdown, :created_at)
        ON CONFLICT(id) DO UPDATE SET
            title = excluded.title,
            decision = excluded.decision
        """
        self.conn.execute(sql, adr)
        self.conn.commit()

    def get_adrs(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if project_id:
            cursor = self.conn.execute("SELECT a.*, p.name as project_name FROM adrs a LEFT JOIN projects p ON a.project_id = p.id WHERE a.project_id = ?", (project_id,))
        else:
            cursor = self.conn.execute("SELECT a.*, p.name as project_name FROM adrs a LEFT JOIN projects p ON a.project_id = p.id")
        return [dict(row) for row in cursor.fetchall()]

    def upsert_skill(self, skill: Dict[str, Any]):
        sql = """
        INSERT INTO skills (id, name, description, instructions, trigger_pattern, source_sessions, status, installed_path, created_at, updated_at)
        VALUES (:id, :name, :description, :instructions, :trigger_pattern, :source_sessions, :status, :installed_path, :created_at, :updated_at)
        ON CONFLICT(name) DO UPDATE SET
            description = excluded.description,
            instructions = excluded.instructions,
            status = excluded.status,
            updated_at = excluded.updated_at
        """
        self.conn.execute(sql, skill)
        self.conn.commit()

    def get_skills(self) -> List[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM skills ORDER BY updated_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    # -------------------------------------------------------------
    # Overall System Stats
    # -------------------------------------------------------------
    def get_stats(self) -> Dict[str, Any]:
        return {
            "projects_count": self.conn.execute("SELECT count(*) FROM projects").fetchone()[0],
            "conversations_count": self.conn.execute("SELECT count(*) FROM conversations").fetchone()[0],
            "episodes_count": self.conn.execute("SELECT count(*) FROM episodes").fetchone()[0],
            "successful_episodes": self.conn.execute("SELECT count(*) FROM episodes WHERE outcome = 'SUCCESS'").fetchone()[0],
            "steps_count": self.conn.execute("SELECT count(*) FROM steps").fetchone()[0],
            "tools_count": self.conn.execute("SELECT count(*) FROM tool_calls").fetchone()[0],
            "rules_count": self.conn.execute("SELECT count(*) FROM rules").fetchone()[0],
            "adrs_count": self.conn.execute("SELECT count(*) FROM adrs").fetchone()[0],
            "skills_count": self.conn.execute("SELECT count(*) FROM skills").fetchone()[0],
        }
