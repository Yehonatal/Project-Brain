# Project Brain

**Project Brain** is a local-first agent intelligence and memory platform built for developers using Google Antigravity (CLI, Agent Manager, IDE) and Gemini agents.

Instead of agent conversations being ephemeral and isolated in `~/.gemini`, Project Brain ingests, redacts, indexes, and synthesizes transcripts, tools, and artifacts into a local intelligence engine that compounds over time.


## Key Capabilities

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. PLUGGABLE INGESTION & INCREMENTAL OFFSET TRACKING                       │
│    • Pluggable source adapters (Antigravity v1/v2, extensible to others)     │
│    • Incremental byte-offset tracking: only scans newly appended JSONL lines │
│    • High-assurance secret redaction (API keys, .env, private keys, tokens) │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. DUAL-TOKENIZER (TRIGRAM + PORTER) FTS5 RETRIEVAL                        │
│    • Episode segmentation: (Problem Intent → Tool Attempts → Resolution)   │
│    • Trigram FTS: paths (/usr/bin/...), error codes (127), code symbols     │
│    • Porter FTS: natural language intent and questions                      │
│    • Outcome-weighted ranking: boosts verified SUCCESS & resolved fixes     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. AGENT-FIRST MCP SERVER (Project-Scoped by Default)                       │
│    • pre-flight resource: brain_get_project_learnings for repo gotchas     │
│    • Compact episode citations [session:step] enforcing token budgets        │
│    • Double secret redaction prior to emitting tool results                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. RULE DISTILLER & CANDIDATE SKILL FORGE                                  │
│    • Synthesizes .agents/rules/*.md from developer steering & corrections    │
│    • Heuristic draft skills from failure-then-fix recipes (human review)    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 5. SECURE TRAJECTORY REPLAYER & WORKBENCH                                   │
│    • Hardened against CSRF/DNS rebinding: bound strictly to 127.0.0.1       │
│    • NO arbitrary command execution: safe 1-click copy-to-clipboard          │
│    • React 19 + Vite + TypeScript + Tailwind UI                             │
└─────────────────────────────────────────────────────────────────────────────┘
```


## Quick Start

### 1. Run with a single command
```bash
./run.sh
```
This automatically runs an incremental scan of `~/.gemini`, distills rules, mines draft skills, extracts Architecture Decision Records (ADRs), and launches the local web workbench on **http://127.0.0.1:8765**.

### 2. Command-Line Interface (CLI)

```bash
# Run incremental scan of ~/.gemini
python3 -m brain.cli scan

# Fast terminal search across problem episodes
python3 -m brain.cli search "sqlite3"
python3 -m brain.cli search "docker container" --project odoo-addons

# List distilled rules from user corrections
python3 -m brain.cli rules

# List mined candidate draft skills
python3 -m brain.cli skills

# Launch the secure web workbench
python3 -m brain.cli serve --port 8765
```


## Connect Project Brain to Antigravity as an MCP Server

Project Brain exposes a Model Context Protocol (MCP) server so your active Antigravity and Gemini CLI agents can query past memory, verified commands, and project learnings during tasks.

Add this entry to your Antigravity MCP settings (e.g. `~/.gemini/antigravity/mcp_servers.json` or `.agents/mcp_servers.json`):

```json
{
  "mcpServers": {
    "project-brain": {
      "command": "python3",
      "args": ["-m", "brain.cli", "mcp"],
      "cwd": "/home/yehonatal/Documents/Tools/Project-Brain"
    }
  }
}
```

### Agent Tools Provided:
1. **`brain_get_project_learnings(project_name)`**:
   Pre-flight check: Run at the start of any task in a repo to retrieve past gotchas, allowed command patterns, and verified workflows.
2. **`brain_search_episodes(query, project_name, only_success=True)`**:
   Searches past problem-solving episodes with compact verified commands and citations (`[session_id:start-end]`).
3. **`brain_get_episode_details(episode_id)`**:
   Inspects step-by-step tool arguments and outputs for a cited episode within a strict token budget.


## Security & Privacy

1. **Local-First**: 100% of transcripts, database records, and searches remain on your machine in `brain.db`.
2. **Secret Redaction at Ingest and MCP**: Credentials (Google Gemini keys, OpenAI keys, GitHub tokens, AWS keys, Bearer tokens, private keys, and `.env` passwords) are automatically redacted with `[REDACTED_*]` placeholders before entering SQLite and before returning over MCP.
3. **No Arbitrary Remote Command Execution**: Unlike naive agent viewers, Project Brain does **not** expose a remote execution endpoint. All commands are strictly copy-to-clipboard.
4. **Host & Origin Validation**: HTTP endpoints validate `Host: 127.0.0.1` and `Origin` headers to prevent CSRF and DNS rebinding attacks.


## Frontend Development (React + Vite + TypeScript + Tailwind)

The frontend source is located in `web/`:
```bash
cd web
npm install
npm run dev     # Starts Vite dev server on http://localhost:5173 with proxy to backend
npm run build   # Compiles to production bundle
```



## Testing & Evaluation Benchmark

Run the automated test suite and retrieval benchmark:
```bash
python3 -m unittest discover tests
```

Output includes **Recall@1**, **Recall@3**, and **Mean Reciprocal Rank (MRR)** across sample queries.
