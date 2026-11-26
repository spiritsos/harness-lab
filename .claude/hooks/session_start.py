"""SessionStart: 새 세션(대화형·headless 모두)에 진행 상태를 자동 주입한다. stdout이 컨텍스트에 추가된다."""

import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

print("## 현재 진행 상태 (SessionStart Hook이 자동 주입)")
try:
    for f in json.loads((ROOT / "features.json").read_text(encoding="utf-8")):
        print(("[x] " if f["passes"] else "[ ] ") + f["id"] + " " + f["desc"][:60])
except (OSError, ValueError):
    pass

print("\n### progress.md 최근 기록")
try:
    print("\n".join((ROOT / "progress.md").read_text(encoding="utf-8").splitlines()[-12:]))
except OSError:
    pass

print("\n### 최근 커밋")
log = subprocess.run(["git", "log", "--oneline", "-5"], cwd=ROOT, capture_output=True, text=True)
print(log.stdout)
