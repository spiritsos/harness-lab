import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = ROOT / "migrations"


def db_path() -> Path:
    return ROOT / os.environ.get("APP_DB", "data/app.db")


def get_conn() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """migrations/ 의 SQL 파일을 번호 순서대로 한 번씩 적용한다."""
    conn = get_conn()
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)")
    done = {r["name"] for r in conn.execute("SELECT name FROM schema_migrations")}
    for f in sorted(MIGRATIONS.glob("*.sql")):
        if f.name in done:
            continue
        conn.executescript(f.read_text(encoding="utf-8"))
        conn.execute("INSERT INTO schema_migrations (name) VALUES (?)", (f.name,))
    conn.commit()
    conn.close()
