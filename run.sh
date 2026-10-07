#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "[Project Brain] Starting..."

# If database doesn't exist yet, run initial scan
if [ ! -f "brain.db" ]; then
    echo "[Project Brain] Initializing database from ~/.gemini..."
    python3 -m brain.cli scan
fi

# Allow passing subcommands like ./run.sh scan, ./run.sh mcp, etc.
if [ "$1" = "scan" ] || [ "$1" = "mcp" ] || [ "$1" = "search" ] || [ "$1" = "rules" ] || [ "$1" = "skills" ]; then
    python3 -m brain.cli "$@"
else
    python3 -m brain.cli serve "$@"
fi
