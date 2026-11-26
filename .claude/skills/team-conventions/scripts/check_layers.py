#!/usr/bin/env python3
"""팀 컨벤션 검사기. 규칙을 '지시'가 아니라 '실행 가능한 코드'로 만든 것.

사용: python .claude/skills/team-conventions/scripts/check_layers.py [파일...]
      (파일을 주지 않으면 app/ 전체 검사)
종료 코드: 0 = 위반 없음, 1 = 위반 있음
"""

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
MONEY_FIELDS = {"price", "unit_price", "total", "amount", "discount"}


def check_file(path: Path) -> list[str]:
    rel = path.resolve().relative_to(ROOT).as_posix()
    if not rel.startswith("app/") or path.suffix != ".py":
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
    out = []
    in_api = rel.startswith("app/api/")
    in_money_code = rel.startswith(("app/api/", "app/services/", "app/models.py"))

    for node in ast.walk(tree):
        # 규칙 1: API 계층에서 DB 직접 접근 금지
        if in_api and isinstance(node, ast.ImportFrom) and node.module in ("app.db", "sqlite3"):
            out.append(
                f"{rel}:{node.lineno}: [LAYER] API 계층에서 {node.module} 를 import 했다. "
                "DB 접근은 app/services/ 의 함수로 옮기고 그 함수를 호출하라."
            )
        if in_api and isinstance(node, ast.Import) and any(a.name == "sqlite3" for a in node.names):
            out.append(
                f"{rel}:{node.lineno}: [LAYER] API 계층에서 sqlite3 를 import 했다. services/ 로 옮겨라."
            )

        # 규칙 2: 금액 필드에 float 타입 금지
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id in MONEY_FIELDS and "float" in ast.unparse(node.annotation):
                out.append(
                    f"{rel}:{node.lineno}: [MONEY] 금액 필드 '{node.target.id}'가 float 이다. "
                    "원 단위 int 로 바꿔라 (docs/domain.md)."
                )

        # 규칙 3: 금액 계산 코드에 float 리터럴 금지 (할인율 0.1 등)
        if in_money_code and isinstance(node, ast.Constant) and type(node.value) is float:
            out.append(
                f"{rel}:{node.lineno}: [MONEY] float 리터럴 {node.value!r} 발견. "
                "할인은 정수 연산으로: total * (100 - 할인%) // 100"
            )
    return out


def check_migrations() -> list[str]:
    """규칙 4: 이미 커밋된 마이그레이션 파일 수정 금지."""
    try:
        res = subprocess.run(
            ["git", "diff", "--name-status", "HEAD", "--", "migrations/"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return []
    out = []
    for line in res.stdout.splitlines():
        status, _, name = line.partition("\t")
        if status.startswith(("M", "D", "R")):
            out.append(
                f"{name}: [MIGRATION] 기존 마이그레이션을 수정/삭제했다. "
                "git checkout 으로 되돌리고 새 번호 파일(00N_...sql)을 만들어라."
            )
    return out


def main(argv: list[str]) -> int:
    files = [Path(a) for a in argv] if argv else sorted((ROOT / "app").rglob("*.py"))
    problems = []
    for f in files:
        if f.exists():
            problems += check_file(f)
    problems += check_migrations()
    for p in problems:
        print(p)
    if problems:
        print(f"\n컨벤션 위반 {len(problems)}건")
        return 1
    print("컨벤션 위반 없음")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
