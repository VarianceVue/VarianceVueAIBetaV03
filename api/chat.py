# Vercel serverless: POST /api/chat
import json
from http.server import BaseHTTPRequestHandler


def read_body(handler):
    length = int(handler.headers.get("Content-Length", 0) or 0)
    if length == 0:
        return b""
    return handler.rfile.read(length)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            raw = read_body(self)
            data = json.loads(raw.decode("utf-8") or "{}") if raw else {}
            message = (data.get("message") or "").strip()
            history = data.get("history") or []
            session_id = (data.get("session_id") or "").strip() or None
            from schedule_agent_web.main import handle_chat_json
            out = handle_chat_json(message, history, session_id)
            body = json.dumps(out).encode("utf-8")
            status = 200
        except Exception as e:
            body = json.dumps({"reply": "", "error": str(e)}).encode("utf-8")
            status = 500
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
