from importlib import reload

from fastapi.testclient import TestClient

import backend.app.database as db
from backend.app.main import create_app


def test_duplicate_upload_prevention(tmp_path, monkeypatch) -> None:
    # Set a temporary database URL
    monkeypatch.setenv("KNOWLEDGE_VAULT_DATABASE_URL", str(tmp_path / "test_upload.db"))
    monkeypatch.setenv("KNOWLEDGE_VAULT_DATA_DIR", str(tmp_path / "data"))

    # Reload database module to apply environment variables
    reload(db)
    db.init_db()

    # Mock heavy pipeline dependencies to prevent downloading external models
    # (HuggingFace, spaCy) during tests
    from backend.app.pipeline import TextChunk

    dummy_chunk = TextChunk(index=0, content="dummy", char_start=0, char_end=5, token_estimate=1)
    monkeypatch.setattr("backend.app.main.parse_document", lambda x: "dummy text")
    monkeypatch.setattr("backend.app.main.chunk_text", lambda x: [dummy_chunk])
    monkeypatch.setattr("backend.app.main.extract_concepts", lambda x: ([], []))

    app = create_app()
    client = TestClient(app)

    # First upload
    file_content = b"This is a test document about python coding and programming."
    files = {"file": ("test_doc.txt", file_content, "text/plain")}
    response1 = client.post("/api/upload", files=files)
    assert response1.status_code == 200
    res_data1 = response1.json()
    assert res_data1["document"]["filename"] == "test_doc.txt"
    assert res_data1["chunk_count"] > 0

    # Second upload of identical content should be blocked
    files2 = {"file": ("test_doc.txt", file_content, "text/plain")}
    response2 = client.post("/api/upload", files=files2)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]
