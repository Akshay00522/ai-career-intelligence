import io
import zipfile

import pytest

from analyzer.parsers import UnsupportedFormat, read_document


def make_docx(paragraphs):
    body = "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs)
    xml = ('<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
           f"<w:body>{body}</w:body></w:document>")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", xml)
    return buf.getvalue()


def make_pdf(text):
    content = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET"
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        "/Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(content)} >>\nstream\n{content}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = b"%PDF-1.4\n", []
    for i, obj in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{obj}\nendobj\n".encode()
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    return out


def test_txt_bytes():
    assert "Python" in read_document(b"Skills: Python", "cv.txt")


def test_txt_path(tmp_path):
    p = tmp_path / "cv.md"
    p.write_text("Skills: SQL", encoding="utf-8")
    assert read_document(p) == "Skills: SQL"


def test_docx_stdlib_reader_handles_paragraphs_and_entities():
    text = read_document(make_docx(["Skills: Python &amp; SQL", "Docker"]), "cv.docx")
    assert "Python & SQL" in text and "Docker" in text
    assert text.count("\n") >= 2


def test_docx_written_by_python_docx():
    docx = pytest.importorskip("docx")
    doc = docx.Document()
    doc.add_paragraph("Experienced with Kubernetes and Terraform")
    buf = io.BytesIO()
    doc.save(buf)
    assert "Kubernetes and Terraform" in read_document(buf.getvalue(), "cv.docx")


def test_pdf():
    pytest.importorskip("pypdf")
    assert "Python" in read_document(make_pdf("Skills Python SQL Docker"), "cv.pdf")


def test_unsupported_format():
    with pytest.raises(UnsupportedFormat):
        read_document(b"x", "cv.exe")


def test_bytes_need_filename():
    with pytest.raises(ValueError):
        read_document(b"x")
