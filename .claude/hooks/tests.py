"""Stop 센서(백프레셔): 테스트가 통과하기 전에는 "완료"하고 끝낼 수 없다."""

import json
import subprocess
import sys
from pathlib import Path

sys.stderr.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
data = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")

# 무한 루프 방지: 이미 Stop Hook 때문에 한 번 재개된 상태면 통과시킨다
if data.get("stop_hook_active"):
    sys.exit(0)


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


# 코드 변경이 없으면(질문·설명만 한 턴) 테스트를 돌리지 않는다
changed = git("diff", "--quiet", "HEAD", "--", "app", "tests").returncode != 0
untracked = git("ls-files", "--others", "--exclude-standard", "app", "tests").stdout.strip()
if not changed and not untracked:
    sys.exit(0)

r = subprocess.run(
    [sys.executable, "dev.py", "test"],
    cwd=ROOT,
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
)
if r.returncode != 0:
    tail = "\n".join((r.stdout + r.stderr).splitlines()[-30:])
    print("테스트 실패. 원인을 고친 뒤 다시 완료하라 (테스트를 지우거나 skip 하지 말 것):", file=sys.stderr)
    print(tail, file=sys.stderr)
    sys.exit(2)
sys.exit(0)
