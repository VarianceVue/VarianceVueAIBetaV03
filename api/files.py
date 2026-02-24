# Vercel serverless: GET /api/files, POST /api/upload, DELETE /api/files
import json
from urllib.parse import parse_qs
from http.server import BaseHTTPRequestHandler


def read_body(handler):
    length = int(handler.headers.get("Content-Length", 0) or 0)
    if length == 0:
        return b""
    return handler.rfile.read(length)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(self.path.split("?", 1)[1]) if "?" in self.path else {}
            session_id = (qs.get("session_id") or [""])[0].strip()
            from schedule_agent_web.store import get_files
            files = get_files(session_id) if session_id else []
            body = json.dumps(files).encode("utf-8")
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
            session_id = (data.get("session_id") or "").strip()
            filename = (data.get("filename") or "").strip()
            content = data.get("content") or ""
            if not session_id or not filename:
                raise ValueError("session_id and filename required")
            from schedule_agent_web.upload_utils import process_upload_content
            is_pdf = filename.lower().endswith(".pdf")
            if is_pdf:
                import base64
                raw_b64 = (content or "").strip()
                if raw_b64.startswith("data:"):
                    raw_b64 = raw_b64.split(",", 1)[-1]
                try:
                    pdf_bytes = base64.b64decode(raw_b64, validate=True)
                except Exception:
                    raise ValueError("Invalid base64 for PDF")
                if len(pdf_bytes) > 500 * 1024 * 1024:
                    raise ValueError("File too large (max 500MB)")
                content_to_store = process_upload_content(filename, content)
            else:
                if len(content.encode("utf-8")) > 500 * 1024 * 1024:
                    raise ValueError("File too large (max 500MB)")
                content_to_store = content
            from schedule_agent_web.store import save_file
            result = save_file(session_id, filename, content_to_store)
            if not result:
                raise ValueError("Failed to save")
            try:
                from schedule_agent_web.vector_store import index_file
                index_file(session_id, filename, content_to_store)
            except Exception:
                pass
            body = json.dumps(result).encode("utf-8")
            status = 200
        except Exception as e:
            body = json.dumps({"error": str(e)}).encode("utf-8")
            status = 400
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_DELETE(self):
        try:
            qs = parse_qs(self.path.split("?", 1)[1]) if "?" in self.path else {}
            session_id = (qs.get("session_id") or [""])[0].strip()
            filename = (qs.get("filename") or [""])[0].strip()
            if not session_id or not filename:
                raise ValueError("session_id and filename required")
            from schedule_agent_web.store import delete_file
            if delete_file(session_id, filename):
                body = json.dumps({"status": "ok"}).encode("utf-8")
            else:
                body = json.dumps({"error": "not found"}).encode("utf-8")
            status = 200
        except Exception as e:
            body = json.dumps({"error": str(e)}).encode("utf-8")
            status = 400
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
