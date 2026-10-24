import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("multipart")

from fastapi.testclient import TestClient  # noqa: E402

from app import app  # noqa: E402

client = TestClient(app)
RESUME = "Python developer with SQL, pandas and scikit-learn experience."
JD = "Requirements\n- Python\n- SQL\n- Docker\nNice to have\n- Kubernetes"


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_analyze_json():
    r = client.post("/analyze", json={"resume_text": RESUME, "jd_text": JD})
    assert r.status_code == 200
    body = r.json()
    assert body["analysis"]["missing_required"] == ["docker"]
    assert body["plan"]["steps"]


def test_validation_errors():
    assert client.post("/analyze", json={"resume_text": "x", "jd_text": JD}).status_code == 422
    assert client.post("/analyze", json={"resume_text": RESUME, "jd_text": JD, "method": "bogus"}).status_code == 422
    assert client.post("/analyze", json={"resume_text": RESUME, "jd_text": JD, "hours_per_week": 0}).status_code == 422


def test_upload_txt():
    r = client.post("/analyze/upload", data={"jd_text": JD},
                    files={"resume": ("cv.txt", RESUME.encode(), "text/plain")})
    assert r.status_code == 200 and r.json()["analysis"]["matched_required"]


def test_upload_unsupported_type():
    r = client.post("/analyze/upload", data={"jd_text": JD}, files={"resume": ("cv.exe", b"x" * 50, "application/octet-stream")})
    assert r.status_code == 415


def test_upload_unreadable_text():
    r = client.post("/analyze/upload", data={"jd_text": JD}, files={"resume": ("cv.txt", b"hi", "text/plain")})
    assert r.status_code == 422
