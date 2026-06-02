from pathlib import Path

from .models import CandidateDocument


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024


def is_supported_document(filename):
    return Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS


def extract_candidate_document_text(document):
    try:
        suffix = Path(document.original_filename).suffix.lower()
        if suffix == ".txt":
            return _success(_extract_txt(document.file.path))
        if suffix == ".pdf":
            text = _extract_pdf(document.file.path)
            return _success(text) if text.strip() else _unsupported()
        if suffix == ".docx":
            text = _extract_docx(document.file.path)
            return _success(text) if text.strip() else _unsupported()
        return CandidateDocument.ExtractionStatus.UNSUPPORTED, ""
    except Exception:
        return CandidateDocument.ExtractionStatus.FAILED, ""


def _extract_txt(path):
    raw = Path(path).read_bytes()
    try:
        return raw.decode("utf-8").strip()
    except UnicodeDecodeError:
        return raw.decode("latin-1", errors="ignore").strip()


def _extract_pdf(path):
    from pypdf import PdfReader

    reader = PdfReader(path)
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n\n".join(part.strip() for part in parts if part.strip()).strip()


def _extract_docx(path):
    from docx import Document

    document = Document(path)
    parts = [paragraph.text.strip() for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    return "\n".join(part for part in parts if part).strip()


def _success(text):
    return CandidateDocument.ExtractionStatus.SUCCESS, text


def _unsupported():
    return CandidateDocument.ExtractionStatus.UNSUPPORTED, ""
