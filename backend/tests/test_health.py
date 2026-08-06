from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_saglik_kontrolu_200_doner() -> None:
    yanit = client.get("/health")
    assert yanit.status_code == 200
    assert yanit.json() == {"durum": "ok"}
