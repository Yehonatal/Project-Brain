"""Command-line interface for Project Brain."""

import argparse
import sys
from pathlib import Path
from brain.config import CONFIG
from brain.db.repository import BrainRepository
from brain.indexer.scanner import IncrementalScanner
from brain.mcp.server import BrainMCPServer
from brain.rules.distiller import RuleDistiller
from brain.skills.candidate_miner import CandidateSkillMiner
from brain.adr.extractor import ADRExtractor
from brain.web.server import start_server

def main():
    parser = argparse.ArgumentParser(
        prog="brain",
        description="Project Brain: Local Agent Intelligence & Memory Platform",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # scan
    scan_parser = subparsers.add_parser("scan", help="Run incremental scan of ~/.gemini data")
    scan_parser.add_argument("--force", action="store_true", help="Force re-indexing all sessions")

    # search
    search_parser = subparsers.add_parser("search", help="Search past problem episodes and solutions")
    search_parser.add_argument("query", help="Search term, error message, or command")
    search_parser.add_argument("--project", "-p", help="Filter by project ID or name")
    search_parser.add_argument("--limit", "-n", type=int, default=5, help="Max results (default 5)")

    # mcp
    subparsers.add_parser("mcp", help="Launch stdio MCP server for Antigravity & Gemini agents")

    # serve
    serve_parser = subparsers.add_parser("serve", help="Launch local web workbench")
    serve_parser.add_argument("--port", type=int, default=CONFIG.port, help=f"Port (default {CONFIG.port})")

    # rules
    subparsers.add_parser("rules", help="List distilled project rules from user corrections")

    # skills
    subparsers.add_parser("skills", help="List candidate draft skills mined across sessions")

    args = parser.parse_args()
    if not args.subcommand:
        parser.print_help()
        sys.exit(0)

    repo = BrainRepository(CONFIG.db_path)

    if args.subcommand == "scan":
        scanner = IncrementalScanner(repo, CONFIG)
        print("[Project Brain] Scanning projects and sessions...")
        res = scanner.scan_all(force=args.force)
        print(f"✓ Indexed {res['projects_indexed']} projects, {res['conversations_indexed']} sessions, {res['episodes_indexed']} episodes, {res['steps_indexed']} steps.")
        
        # Run distillation pipelines
        print("[Project Brain] Distilling rules from user feedback...")
        rd = RuleDistiller(repo)
        rules = rd.distill_rules()
        print(f"✓ Distilled {len(rules)} rules.")

        print("[Project Brain] Mining candidate skills...")
        sm = CandidateSkillMiner(repo)
        skills = sm.mine_draft_skills()
        print(f"✓ Mined {len(skills)} candidate draft skills.")

        print("[Project Brain] Extracting Architecture Decision Records...")
        ae = ADRExtractor(repo)
        adrs = ae.extract_from_artifacts()
        print(f"✓ Extracted {len(adrs)} Architecture Decision Records.")

    elif args.subcommand == "search":
        project_id = None
        if args.project:
            for p in repo.get_projects():
                if p["name"].lower() == args.project.lower() or p["id"] == args.project:
                    project_id = p["id"]
                    break

        results = repo.search_episodes(query=args.query, project_id=project_id, limit=args.limit)
        if not results:
            print(f"No episodes found matching: '{args.query}'")
            return

        print(f"\n--- Found {len(results)} Episode(s) for '{args.query}' ---")
        for ep in results:
            citation = f"[{ep['conversation_id'][:8]}:{ep['start_step_index']}-{ep['end_step_index']}]"
            proj = f"({ep['project_name']})" if ep.get("project_name") else ""
            print(f"\n[{ep['outcome']}] score={ep['score']} {ep['title']} {proj} {citation}")
            if ep["commands_run"]:
                print("Verified Commands:")
                for c in ep["commands_run"][:3]:
                    print(f"  $ {c}")
            print(f"Summary: {ep['resolution'][:160]}...")

    elif args.subcommand == "mcp":
        server = BrainMCPServer(repo, CONFIG)
        server.run_stdio()

    elif args.subcommand == "serve":
        CONFIG.port = args.port
        print(f"[Project Brain] Server starting on http://127.0.0.1:{CONFIG.port}")
        print("Press Ctrl+C to stop.")
        start_server(repo, CONFIG)

    elif args.subcommand == "rules":
        rules = repo.get_rules()
        print(f"\nDistilled Rules ({len(rules)}):")
        for r in rules:
            print(f"- [{r.get('rule_type', 'rule')}] {r['title']} (Project: {r.get('project_name') or 'Global'})")

    elif args.subcommand == "skills":
        skills = repo.get_skills()
        print(f"\nCandidate Draft Skills ({len(skills)}):")
        for s in skills:
            print(f"- [DRAFT] {s['name']}: {s['description']}")

if __name__ == "__main__":
    main()
