"""PreToolUse 가드: 위험 명령 · 비밀 파일 · 기존 마이그레이션 수정을 차단한다.

exit 2 + stderr 메시지 → 도구 실행이 막히고, 메시지가 Claude에게 전달된다.
bash 대신 python으로 작성해 Windows · macOS · Linux에서 똑같이 동작한다.
"""

import json
import re
import sys
from pathlib import Path

sys.stderr.reconfigure(encoding="utf-8")
data = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
tool = data.get("tool_name", "")
tool_input = data.get("tool_input") or {}
cmd = tool_input.get("command", "") or ""
file = tool_input.get("file_path", "") or ""


def block(why: str, alternative: str) -> None:
    print(f"차단: {why}\n대안: {alternative}", file=sys.stderr)
    sys.exit(2)


if tool in ("Bash", "PowerShell"):
    if re.search(r"\brm\s+-[a-zA-Z]*(rf|fr)|Remove-Item\b.*-Recurse", cmd, re.IGNORECASE):
        block(f"재귀 삭제 명령입니다: {cmd}", "삭제할 파일을 하나씩 지정하거나 사람에게 요청하라.")
    if re.search(r"git\s+push\b.*(--force|\s-f(\s|$))", cmd):
        block(
            f"force push 입니다: {cmd}",
            "일반 push 또는 새 브랜치로 push 하라. 이력 덮어쓰기는 사람이 결정한다.",
        )
    if re.search(r"(^|[^\w])\.env([^\w]|$)", cmd):
        block(
            ".env 파일에 접근하는 명령입니다.",
            "설정 값이 필요하면 사람에게 물어라. 비밀 값은 읽거나 출력하지 않는다.",
        )
    if re.search(r"drop\s+table|reset_db", cmd, re.IGNORECASE):
        block(
            f"DB를 파괴하는 명령입니다: {cmd}",
            "테스트는 임시 DB(client fixture)를 쓴다. 초기화는 사람에게 요청하라.",
        )

if file:
    path = "/" + file.replace("\\", "/")
    name = path.rsplit("/", 1)[-1]
    if name == ".env" or name.startswith(".env.") or "/secrets/" in path:
        block(
            f"비밀 파일 접근입니다: {file}", "이 파일은 읽거나 수정하지 않는다. 필요한 값은 사람에게 물어라."
        )
    if tool in ("Edit", "Write") and "/migrations/" in path and path.endswith(".sql") and Path(file).exists():
        block(
            f"기존 마이그레이션 파일 수정입니다: {file}",
            "migrations/ 에 다음 번호의 새 파일(예: 003_xxx.sql)을 만들어라.",
        )

sys.exit(0)
