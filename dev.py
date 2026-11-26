"""프로젝트 작업 명령 (Windows · macOS · Linux 공통).

사용: python dev.py <작업>
  test        빠른 테스트 (slow 제외). 평소에는 이것만 돌린다
  test-all    느린 통합 테스트까지 전부 (30초 이상, CI용)
  test-hooks  Hook 스크립트 단독 테스트 (Claude 없이)
  lint        ruff 린트
  fmt         ruff 포맷
  run         개발 서버 실행
  seed        샘플 데이터 넣기
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable
CODE = [
    p
    for p in ("app", "tests", "scripts", "tools", ".claude", "evals", "dev.py", "run_agent.py")
    if (ROOT / p).exists()
]

TASKS = {
    "test": [PY, "-m", "pytest", "-m", "not slow", "-q"],
    "test-all": [PY, "-m", "pytest", "-q"],
    "test-hooks": [PY, "-m", "pytest", "-q", "tests/test_hooks.py"],
    "lint": [PY, "-m", "ruff", "check", *CODE],
    "fmt": [PY, "-m", "ruff", "format", *CODE],
    "run": [PY, "-m", "uvicorn", "app.main:app", "--reload"],
    "seed": [PY, "scripts/seed.py"],
}


def main() -> int:
    task = sys.argv[1] if len(sys.argv) > 1 else ""
    if task not in TASKS:
        print(__doc__)
        return 1
    if task == "test-hooks" and not (ROOT / "tests" / "test_hooks.py").exists():
        print("tests/test_hooks.py 가 없습니다.")
        return 1
    return subprocess.call(TASKS[task], cwd=ROOT)


if __name__ == "__main__":
    sys.exit(main())
