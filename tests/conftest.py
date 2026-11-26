import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DB", str(tmp_path / "test.db"))
    from app.db import get_conn, init_db

    init_db()
    conn = get_conn()
    conn.executemany(
        "INSERT INTO products (name, price) VALUES (?, ?)",
        [("무선 마우스", 25900), ("모니터 받침대", 9990)],
    )
    conn.commit()
    conn.close()

    from app.main import app

    return TestClient(app)
