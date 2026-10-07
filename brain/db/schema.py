"""SQLite Database Schema with Dual FTS5 (Trigram + Porter) and Episode support."""

import sqlite3
from pathlib import Path

SCHEMA_SQL = """
-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    root_path TEXT,
    default_branch TEXT,
    raw_config TEXT,
    updated_at TEXT
);

-- Conversations / Sessions table
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    title TEXT,
    model TEXT,
    total_steps INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT,
    FOREIGN KEY(project_id) REFERENCES projects(id)
);

-- Episodes (Problem → Attempts → Resolution)
CREATE TABLE IF NOT EXISTS episodes (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    project_id TEXT,
    episode_index INTEGER NOT NULL,
    title TEXT NOT NULL,
    intent TEXT NOT NULL,
    attempts_summary TEXT,
    resolution TEXT,
    outcome TEXT NOT NULL, -- SUCCESS, FAILURE, USER_CORRECTED, IN_PROGRESS
    outcome_score REAL DEFAULT 1.0,
    start_step_index INTEGER,
    end_step_index INTEGER,
    commands_json TEXT,
    files_json TEXT,
    created_at TEXT,
    FOREIGN KEY(conversation_id) REFERENCES conversations(id),
    FOREIGN KEY(project_id) REFERENCES projects(id)
);

-- Raw steps for trajectory replay
CREATE TABLE IF NOT EXISTS steps (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    step_index INTEGER NOT NULL,
    source TEXT,
    type TEXT,
    status TEXT,
    thinking TEXT,
    content TEXT,
    created_at TEXT,
    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);

-- Tool calls inside planner responses
CREATE TABLE IF NOT EXISTS tool_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    step_id TEXT NOT NULL,
    conversation_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    tool_action TEXT,
    tool_summary TEXT,
    arguments_json TEXT,
    output TEXT,
    exit_code INTEGER,
    created_at TEXT,
    FOREIGN KEY(step_id) REFERENCES steps(id),
    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);

-- Artifacts produced during conversations
CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    project_id TEXT,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    artifact_type TEXT,
    content TEXT,
    summary TEXT,
    created_at TEXT,
    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);

-- Synthesized Skills (Drafts requiring human review)
CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    instructions TEXT,
    trigger_pattern TEXT,
    source_sessions TEXT,
    status TEXT DEFAULT 'draft', -- draft, installed, ignored
    installed_path TEXT,
    created_at TEXT,
    updated_at TEXT
);

-- Rules distilled from user corrections
CREATE TABLE IF NOT EXISTS rules (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    project_id TEXT,
    conversation_id TEXT,
    rule_type TEXT DEFAULT 'negative_constraint',
    content TEXT NOT NULL,
    created_at TEXT,
    FOREIGN KEY(project_id) REFERENCES projects(id)
);

-- Architecture Decision Records (ADRs)
CREATE TABLE IF NOT EXISTS adrs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    project_id TEXT,
    conversation_id TEXT,
    status TEXT DEFAULT 'accepted',
    context TEXT,
    decision TEXT,
    consequences TEXT,
    raw_markdown TEXT,
    created_at TEXT,
    FOREIGN KEY(project_id) REFERENCES projects(id),
    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);

-- Ingestion tracking offsets
CREATE TABLE IF NOT EXISTS ingestion_offsets (
    file_path TEXT PRIMARY KEY,
    mtime REAL NOT NULL,
    file_size INTEGER NOT NULL,
    byte_offset INTEGER NOT NULL,
    updated_at TEXT NOT NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_episodes_conv ON episodes(conversation_id);
CREATE INDEX IF NOT EXISTS idx_episodes_proj ON episodes(project_id);
CREATE INDEX IF NOT EXISTS idx_episodes_outcome ON episodes(outcome);
CREATE INDEX IF NOT EXISTS idx_steps_conv ON steps(conversation_id, step_index);
CREATE INDEX IF NOT EXISTS idx_tool_calls_conv ON tool_calls(conversation_id);
"""

# Dual FTS5 tables: Trigram for code/symbols/paths, Porter for natural language
FTS_SQL = """
-- Trigram tokenizer for paths, identifiers, and error strings
CREATE VIRTUAL TABLE IF NOT EXISTS fts_episodes_trigram USING fts5(
    episode_id UNINDEXED,
    conversation_id UNINDEXED,
    project_id UNINDEXED,
    searchable_text,
    tokenize = 'trigram'
);

-- Porter stemmer for natural language intent and questions
CREATE VIRTUAL TABLE IF NOT EXISTS fts_episodes_porter USING fts5(
    episode_id UNINDEXED,
    conversation_id UNINDEXED,
    project_id UNINDEXED,
    title,
    intent,
    resolution,
    tokenize = 'porter unicode61'
);
"""

def init_db(db_path: Path) -> sqlite3.Connection:
    """Initialize SQLite database with dual FTS5 and episode schema."""
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA_SQL)

    try:
        conn.executescript(FTS_SQL)
    except sqlite3.OperationalError:
        pass

    conn.commit()
    return conn
