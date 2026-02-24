# Vercel serverless: GET /api/conversation?session_id=...
import json
from urllib.parse import parse_qs
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(self.path.split("?", 1)[1]) if "?" in self.path else {}
            session_id = (qs.get("session_id") or [""])[0].strip()
            from schedule_agent_web.store import get_conversation
            conv = get_conversation(session_id) if session_id else []
            body = json.dumps(conv).encode("utf-8")
        except Exception as e:
            body = json.dumps([]).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
