"""장기 실행 루프: 한 세션 = 기능 하나. 사람 없이 features.json이 모두 true가 될 때까지 반복.

저장소의 CLAUDE.md · settings.json · Hooks는 headless(-p)에서도 그대로 적용된다.
사용: python run_agent.py            (기본 3세션)
      MAX_SESSIONS=1 python run_agent.py   / PowerShell: $env:MAX_SESSIONS=1; python run_agent.py
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAX_SESSIONS = int(os.environ.get("MAX_SESSIONS", "3"))
PROMPT = """progress.md, git log --oneline -10, features.json 을 읽어 상태를 파악하라.
passes가 false인 기능 중 가장 앞의 것 '하나만' 구현하라.
1) features.json의 test 경로에 테스트를 먼저 작성 2) 구현 3) python dev.py test 통과
4) python scripts/check_features.py 로 확인한 뒤에만 그 기능의 passes를 true로 바꾼다
5) progress.md 맨 아래에 세션 기록 추가 6) git add -A && git commit -m 'F-xx: 요약'
features.json의 passes 외 필드는 절대 수정하지 마라. 다른 기능에는 손대지 마라."""
ALLOWED = ",".join(
    [
        "Read",
        "Edit",
        "Write",
        "Glob",
        "Grep",
        "Bash(python dev.py test)",
        "Bash(python dev.py lint)",
        "Bash(python scripts/check_features.py)",
        "Bash(git status)",
        "Bash(git diff:*)",
        "Bash(git log:*)",
        "Bash(git add:*)",
        "Bash(git commit:*)",
    ]
)


def all_done() -> bool:
    return all(f["passes"] for f in json.loads((ROOT / "features.json").read_text(encoding="utf-8")))


def main() -> int:
    claude = shutil.which("claude")  # Windows의 claude.cmd / claude.exe 도 찾는다
    if claude is None:
        print("claude 명령을 찾을 수 없습니다. Claude Code 설치와 PATH를 확인하세요.")
        return 1
    (ROOT / "logs").mkdir(exist_ok=True)
    for i in range(1, MAX_SESSIONS + 1):
        if all_done():
            print("모든 기능 완료")
            break
        print(f"=== 세션 {i} 시작 ===")
        with open(ROOT / "logs" / f"run-{i}.json", "w", encoding="utf-8") as log:
            subprocess.run(
                [
                    claude,
                    "-p",
                    PROMPT,
                    "--allowedTools",
                    ALLOWED,
                    "--max-turns",
                    "40",
                    "--output-format",
                    "json",
                ],
                cwd=ROOT,
                stdout=log,
            )
        print(f"세션 {i} 종료 (로그: logs/run-{i}.json)")
        if subprocess.call([sys.executable, "scripts/check_features.py"], cwd=ROOT) != 0:
            print("검증 실패 — 루프 중단, 사람이 확인하라")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
