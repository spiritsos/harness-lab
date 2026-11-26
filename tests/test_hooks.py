"""Hook 단독 테스트: Claude 없이 stdin JSON을 직접 넣어 기대한 종료 코드가 나오는지 확인한다.

실행: python dev.py test-hooks   (python dev.py test 에도 포함된다)
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / ".claude" / "hooks"


def run_hook(hook: str, payload: dict) -> int:
    r = subprocess.run(
        [sys.executable, str(HOOKS / hook)],
        input=json.dumps(payload).encode("utf-8"),
        capture_output=True,
        cwd=ROOT,
    )
    return r.returncode


def bash(command: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": command}}


GUARD_CASES = [
    (2, bash("rm -rf /"), "rm -rf 차단"),
    (2, bash("rm -fr data"), "rm -fr 차단"),
    (
        2,
        {"tool_name": "PowerShell", "tool_input": {"command": "Remove-Item data -Recurse -Force"}},
        "PS 재귀 삭제 차단",
    ),
    (2, bash("git push --force"), "force push 차단"),
    (2, bash("git push -f origin main"), "push -f 차단"),
    (2, bash("cat .env"), "cat .env 차단"),
    (2, {"tool_name": "PowerShell", "tool_input": {"command": "Get-Content .env"}}, "PS .env 차단"),
    (2, bash("python scripts/reset_db.py"), "reset_db 차단"),
    (2, {"tool_name": "Read", "tool_input": {"file_path": "/repo/.env"}}, "Read .env 차단"),
    (2, {"tool_name": "Read", "tool_input": {"file_path": "C:\\repo\\.env"}}, "Windows 경로 .env 차단"),
    (
        2,
        {"tool_name": "Edit", "tool_input": {"file_path": str(ROOT / "migrations" / "001_init.sql")}},
        "기존 마이그레이션 수정 차단",
    ),
    (
        0,
        {"tool_name": "Write", "tool_input": {"file_path": str(ROOT / "migrations" / "009_new.sql")}},
        "새 마이그레이션 허용",
    ),
    (0, bash("python dev.py test"), "테스트 명령 허용"),
    (0, bash("git push origin feat"), "일반 push 통과 (권한 ask로 확인)"),
    (
        0,
        {"tool_name": "Read", "tool_input": {"file_path": "/repo/app/env_utils.py"}},
        "비슷한 이름 오탐 없음",
    ),
]


@pytest.mark.parametrize("expected,payload,desc", GUARD_CASES, ids=[c[2] for c in GUARD_CASES])
def test_guard(expected, payload, desc):
    assert run_hook("guard.py", payload) == expected


def test_lint_skips_non_python():
    assert run_hook("lint.py", {"tool_name": "Edit", "tool_input": {"file_path": "README.md"}}) == 0


def test_lint_passes_clean_file():
    assert (
        run_hook("lint.py", {"tool_name": "Edit", "tool_input": {"file_path": str(ROOT / "app" / "db.py")}})
        == 0
    )


def test_lint_reports_layer_violation():
    tmp = ROOT / "app" / "api" / "_hooktest_tmp.py"
    tmp.write_text("from app.db import get_conn\n", encoding="utf-8")
    try:
        assert run_hook("lint.py", {"tool_name": "Write", "tool_input": {"file_path": str(tmp)}}) == 2
    finally:
        tmp.unlink()
