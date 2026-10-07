#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "[Project Brain] Starting..."
python3 -m brain.cli scan
python3 -m brain.cli serve "$@"
