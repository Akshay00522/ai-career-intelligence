"""Read resume / JD text from .txt, .md, .pdf and .docx (path or raw bytes)."""
from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

SUPPORTED = (".txt", ".md", ".pdf", ".docx")


class UnsupportedFormat(ValueError):
    pass


def _read_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("PDF support needs `pip install pypdf`") from exc
    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _read_docx(data: bytes) -> str:
    """Extract text from a .docx using only the standard library (no python-docx)."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
    xml = re.sub(r"</w:p>", "\n", xml)          # paragraph ends -> newline
    xml = re.sub(r"<w:tab/>", "\t", xml)
    xml = re.sub(r"<[^>]+>", "", xml)           # drop remaining tags
    for entity, char in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&apos;", "'")):
        xml = xml.replace(entity, char)
    return xml


def read_document(source: str | Path | bytes, filename: str | None = None) -> str:
    """Return plain text. `source` is a path, or bytes together with `filename`."""
    if isinstance(source, (str, Path)):
        path = Path(source)
        data, name = path.read_bytes(), path.name
    else:
        if not filename:
            raise ValueError("filename is required when passing raw bytes")
        data, name = source, filename

    suffix = Path(name).suffix.lower()
    if suffix in (".txt", ".md"):
        return data.decode("utf-8", errors="ignore")
    if suffix == ".pdf":
        return _read_pdf(data)
    if suffix == ".docx":
        return _read_docx(data)
    raise UnsupportedFormat(f"Unsupported file type '{suffix}'. Use one of: {', '.join(SUPPORTED)}")
