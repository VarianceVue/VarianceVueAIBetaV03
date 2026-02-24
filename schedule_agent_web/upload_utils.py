"""Shared upload handling: PDF text extraction and content normalization."""
import base64


def _extract_with_pypdf(pdf_bytes: bytes) -> str:
    try:
        from pypdf import PdfReader
        from io import BytesIO
        reader = PdfReader(BytesIO(pdf_bytes))
        parts = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                parts.append(t)
        return "\n\n".join(parts) if parts else ""
    except Exception:
        return ""


def _extract_with_pymupdf(pdf_bytes: bytes) -> str:
    """Fallback extractor; often gets text when pypdf does not (e.g. some image+text PDFs)."""
    try:
        import fitz  # pymupdf
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        parts = []
        for page in doc:
            t = page.get_text()
            if t:
                parts.append(t)
        doc.close()
        return "\n\n".join(parts) if parts else ""
    except Exception:
        return ""


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes. Tries pypdf first, then PyMuPDF if result is empty or very short."""
    text = _extract_with_pypdf(pdf_bytes)
    text = (text or "").strip()
    if len(text) < 50:
        fallback = _extract_with_pymupdf(pdf_bytes)
        fallback = (fallback or "").strip()
        if len(fallback) > len(text):
            text = fallback
    return text


def process_upload_content(filename: str, content: str) -> str:
    """
    Return text to store and index.
    For .pdf: content is base64 PDF → decode and extract text.
    Otherwise return content as-is (UTF-8 text).
    """
    if not filename.lower().endswith(".pdf"):
        return content
    raw = (content or "").strip()
    if raw.startswith("data:"):
        raw = raw.split(",", 1)[-1]
    try:
        pdf_bytes = base64.b64decode(raw, validate=True)
    except Exception:
        return ""
    text = extract_text_from_pdf(pdf_bytes)
    text = text.strip()
    if not text:
        return (
            "[This PDF could not be read as text. It may be image-only (scanned). "
            "Re-upload a PDF with selectable text, or use an OCR tool to create a text-based PDF.]"
        )
    return text
