"""PostToolUse 센서: 파이썬 파일을 편집한 직후 포맷 → 린트 → 컨벤션 검사.

문제가 있으면 exit 2로 결과를 Claude에게 돌려줘 바로 고치게 한다. (편집 자체는 이미 반영됨)
"""

import json
import subprocess
import sys
from pathlib import Path

sys.stderr.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / ".claude" / "skills" / "team-conventions" / "scripts" / "check_layers.py"

data = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
file = (data.get("tool_input") or {}).get("file_path", "") or ""
if not file.endswith(".py") or not Path(file).exists():
    sys.exit(0)


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )


run("-m", "ruff", "format", "-q", file)  # 포맷은 조용히 자동 적용

problems = []
r = run("-m", "ruff", "check", file)
if r.returncode != 0:
    problems.append("[ruff]\n" + r.stdout + r.stderr)
if CHECKER.exists():
    r = run(str(CHECKER), file)
    if r.returncode != 0:
        problems.append("[컨벤션]\n" + r.stdout)

if problems:
    msg = f"방금 편집한 {file} 에서 문제가 발견됐다. 아래를 고쳐라:\n" + "\n".join(problems)
    print("\n".join(msg.splitlines()[:40]), file=sys.stderr)
    sys.exit(2)
sys.exit(0)
