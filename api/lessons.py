# Vercel serverless: GET /api/lessons, POST /api/lessons
import json
from http.server import BaseHTTPRequestHandler


def read_body(handler):
    length = int(handler.headers.get("Content-Length", 0) or 0)
    if length == 0:
        return b""
    return handler.rfile.read(length)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            from schedule_agent_web.store import get_lessons
            body = json.dumps(get_lessons()).encode("utf-8")
        except Exception:
            body = json.dumps([]).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            raw = read_body(self)
            data = json.loads(raw.decode("utf-8") or "{}") if raw else {}
            from schedule_agent_web.store import append_lesson
            append_lesson(data)
            body = json.dumps({"status": "ok"}).encode("utf-8")
            status = 200
        except Exception as e:
            body = json.dumps({"error": str(e)}).encode("utf-8")
            status = 500
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
