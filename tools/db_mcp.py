#!/usr/bin/env python3
"""읽기 전용 SQLite MCP 서버 (표준 라이브러리만 사용).

MCP는 stdio 위의 JSON-RPC 2.0입니다. 이 파일 하나로 프로토콜의 실체를 볼 수 있습니다.
  - initialize  : 서버 정보와 능력(capabilities) 교환
  - tools/list  : 도구 이름 · 설명 · 입력 스키마 공개  ← 설명이 곧 프롬프트
  - tools/call  : 도구 실행 결과 반환

도구 설계 원칙(교재 M3)을 그대로 적용했습니다.
  적고 명확하게(3개) / 설명에 "언제 쓰는지" / 출력은 짧게(최대 50행) /
  오류는 행동 가능하게 / 조회 전용(변경 도구 없음, DB도 read-only로 연다)

실행: python tools/db_mcp.py  (APP_DB 환경 변수로 DB 경로 지정, 기본 data/app.db)
"""

import json
import os
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / os.environ.get("APP_DB", "data/app.db")
MAX_ROWS = 50

TOOLS = [
    {
        "name": "list_tables",
        "description": "주문 DB의 테이블 목록을 반환한다. 어떤 데이터가 있는지 모를 때 가장 먼저 호출하라.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "describe_table",
        "description": "테이블의 컬럼 이름과 타입을 반환한다. SQL을 쓰기 전에 컬럼명을 확인할 때 사용하라.",
        "inputSchema": {
            "type": "object",
            "properties": {"table": {"type": "string", "description": "테이블 이름 (예: orders)"}},
            "required": ["table"],
        },
    },
    {
        "name": "query",
        "description": (
            "읽기 전용 SELECT 문을 실행해 최대 50행을 반환한다. 집계(COUNT, SUM)는 SQL 안에서 하라. "
            "날짜는 ISO 문자열(created_at, cancelled_at)이며 "
            "date('now','-7 day') 같은 SQLite 함수를 쓸 수 있다. "
            "INSERT/UPDATE/DELETE 등 변경 문은 거부된다."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "SELECT 또는 WITH로 시작하는 SQL 한 문장"}
            },
            "required": ["sql"],
        },
    },
]


def _conn() -> sqlite3.Connection:
    if not DB.exists():
        raise RuntimeError(f"DB 파일이 없습니다: {DB}. 사람에게 `python dev.py seed` 실행을 요청하라.")
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)  # 파일 수준에서도 읽기 전용
    conn.row_factory = sqlite3.Row
    return conn


def list_tables(_args):
    with _conn() as c:
        rows = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        return [r["name"] for r in rows]


def describe_table(args):
    table = args.get("table", "")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table):
        raise ValueError("table은 영문·숫자·밑줄만 가능하다. 먼저 list_tables로 이름을 확인하라.")
    with _conn() as c:
        cols = c.execute(f"PRAGMA table_info({table})").fetchall()
    if not cols:
        raise ValueError(f"테이블 '{table}'이 없다. list_tables로 실제 이름을 확인하라.")
    return [{"column": r["name"], "type": r["type"]} for r in cols]


def query(args):
    sql = args.get("sql", "").strip().rstrip(";")
    if not re.match(r"(?is)^(select|with)\b", sql) or ";" in sql:
        raise ValueError("SELECT/WITH로 시작하는 한 문장만 허용된다. 데이터 변경은 이 도구로 할 수 없다.")
    with _conn() as c:
        try:
            cur = c.execute(sql)
        except sqlite3.Error as e:
            raise ValueError(f"SQL 오류: {e}. describe_table로 컬럼명을 확인한 뒤 다시 시도하라.") from e
        rows = cur.fetchmany(MAX_ROWS + 1)
    out = [dict(r) for r in rows[:MAX_ROWS]]
    if len(rows) > MAX_ROWS:
        out.append({"_note": f"{MAX_ROWS}행에서 잘림. 집계하거나 WHERE/LIMIT로 범위를 좁혀라."})
    return out


HANDLERS = {"list_tables": list_tables, "describe_table": describe_table, "query": query}


def handle(msg):
    method, params = msg.get("method"), msg.get("params") or {}
    if method == "initialize":
        return {
            "protocolVersion": params.get("protocolVersion", "2025-06-18"),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "shopdb", "version": "1.0.0"},
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        name = params.get("name")
        fn = HANDLERS.get(name)
        if fn is None:
            return _tool_error(f"알 수 없는 도구 '{name}'. 사용 가능: {', '.join(HANDLERS)}")
        try:
            result = fn(params.get("arguments") or {})
        except Exception as e:  # 오류도 '결과'로 돌려줘야 에이전트가 읽고 고친다
            return _tool_error(str(e))
        return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}
    raise LookupError(method)


def _tool_error(text):
    return {"content": [{"type": "text", "text": text}], "isError": True}


def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        msg = json.loads(line)
        if "id" not in msg:  # notification (예: notifications/initialized) 은 응답하지 않는다
            continue
        try:
            reply = {"jsonrpc": "2.0", "id": msg["id"], "result": handle(msg)}
        except LookupError:
            reply = {
                "jsonrpc": "2.0",
                "id": msg["id"],
                "error": {"code": -32601, "message": "Method not found"},
            }
        sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
