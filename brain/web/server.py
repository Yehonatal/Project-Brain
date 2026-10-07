"""Secure local HTTP API and asset server for Project Brain.

Hardened against CSRF, DNS rebinding, and cross-origin attacks:
- Binds strictly to 127.0.0.1
- Strictly validates Host and Origin headers
- NO arbitrary shell execution endpoints (commands are copy-only)
- Secret redaction on all outgoing responses
"""

import http.server
import json
import logging
import mimetypes
import socketserver
import urllib.parse
from pathlib import Path
from typing import Any, Dict, Optional
from brain.config import CONFIG, BrainConfig
from brain.db.repository import BrainRepository
from brain.indexer.scanner import IncrementalScanner
from brain.rules.distiller import RuleDistiller
from brain.security.redactor import SecretRedactor
from brain.skills.candidate_miner import CandidateSkillMiner

logger = logging.getLogger("brain.web.server")

class SecureBrainHTTPHandler(http.server.SimpleHTTPRequestHandler):
    repo: BrainRepository
    config: BrainConfig
    scanner: IncrementalScanner
    rule_distiller: RuleDistiller
    skill_miner: CandidateSkillMiner

    def _validate_origin_and_host(self) -> bool:
        """Protects against DNS rebinding and cross-site requests."""
        host = self.headers.get("Host", "").lower().split(":")[0]
        if host not in ("127.0.0.1", "localhost"):
            self.send_error(403, "Forbidden: Invalid Host header.")
            return False

        origin = self.headers.get("Origin")
        if origin:
            parsed_origin = urllib.parse.urlparse(origin)
            origin_host = parsed_origin.hostname or ""
            if origin_host not in ("127.0.0.1", "localhost"):
                self.send_error(403, "Forbidden: Cross-origin request rejected.")
                return False

        return True

    def _send_json(self, data: Any, status: int = 200):
        # Apply secret redaction
        safe_data = SecretRedactor.redact_json_obj(data)
        encoded = json.dumps(safe_data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        origin = self.headers.get("Origin")
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self):
        if not self._validate_origin_and_host():
            return
        self.send_response(204)
        origin = self.headers.get("Origin")
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if not self._validate_origin_and_host():
            return

        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        if path.startswith("/api/"):
            self._handle_api_get(path, query)
        else:
            self._serve_static(path)

    def do_POST(self):
        if not self._validate_origin_and_host():
            return

        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == "/api/scan":
            results = self.scanner.scan_all(force=False)
            self._send_json({"status": "ok", "scan_results": results})
        elif path == "/api/distill-rules":
            rules = self.rule_distiller.distill_rules()
            self._send_json({"status": "ok", "distilled_rules_count": len(rules)})
        elif path == "/api/mine-skills":
            skills = self.skill_miner.mine_draft_skills()
            self._send_json({"status": "ok", "draft_skills_count": len(skills)})
        else:
            self.send_error(404, "Endpoint not found.")

    def _handle_api_get(self, path: str, query: Dict[str, list]):
        if path == "/api/stats":
            self._send_json(self.repo.get_stats())

        elif path == "/api/projects":
            self._send_json(self.repo.get_projects())

        elif path == "/api/conversations":
            project_id = query.get("project_id", [None])[0]
            limit = int(query.get("limit", [50])[0])
            self._send_json(self.repo.get_conversations(project_id=project_id, limit=limit))

        elif path.startswith("/api/conversations/"):
            conv_id = path.replace("/api/conversations/", "").strip()
            conv = self.repo.get_conversation(conv_id)
            if conv:
                self._send_json(conv)
            else:
                self.send_error(404, "Conversation not found.")

        elif path == "/api/search":
            q = query.get("q", [""])[0]
            project_id = query.get("project_id", [None])[0]
            limit = int(query.get("limit", [20])[0])
            results = self.repo.search_episodes(query=q, project_id=project_id, limit=limit)
            self._send_json(results)

        elif path == "/api/rules":
            project_id = query.get("project_id", [None])[0]
            self._send_json(self.repo.get_rules(project_id=project_id))

        elif path == "/api/skills":
            self._send_json(self.repo.get_skills())

        elif path == "/api/adrs":
            project_id = query.get("project_id", [None])[0]
            self._send_json(self.repo.get_adrs(project_id=project_id))

        else:
            self.send_error(404, "API route not found.")

    def _serve_static(self, path: str):
        static_dir = Path(__file__).parent / "static"
        if path == "/" or not path:
            target_file = static_dir / "index.html"
        else:
            rel_path = path.lstrip("/")
            resolved_target = (static_dir / rel_path).resolve()
            if not str(resolved_target).startswith(str(static_dir.resolve())):
                self.send_error(403, "Forbidden.")
                return
            target_file = resolved_target

        if not target_file.exists() or not target_file.is_file():
            # Fallback to SPA index.html
            target_file = static_dir / "index.html"

        if not target_file.exists():
            self.send_error(404, "Static file not found.")
            return

        ctype, _ = mimetypes.guess_type(str(target_file))
        if not ctype:
            ctype = "text/plain"

        try:
            content = target_file.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {e}")

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

def start_server(repo: BrainRepository, config: BrainConfig = CONFIG):
    SecureBrainHTTPHandler.repo = repo
    SecureBrainHTTPHandler.config = config
    SecureBrainHTTPHandler.scanner = IncrementalScanner(repo, config)
    SecureBrainHTTPHandler.rule_distiller = RuleDistiller(repo)
    SecureBrainHTTPHandler.skill_miner = CandidateSkillMiner(repo)

    # Bind strictly to 127.0.0.1
    server_address = ("127.0.0.1", config.port)
    httpd = ThreadedHTTPServer(server_address, SecureBrainHTTPHandler)
    logger.info("Project Brain Web Server running on http://127.0.0.1:%d", config.port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
