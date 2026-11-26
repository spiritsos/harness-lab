#!/usr/bin/env python3
"""features.json 검증 센서. 에이전트의 '완료 선언'이 아니라 실제 테스트 결과로 판정한다.

검사 1) 무결성: 마지막 커밋 대비 passes 외의 필드(id, desc, test)나 항목 수가 바뀌지 않았는가
검사 2) 정직성: passes=true 인 기능의 테스트가 실제로 존재하고 통과하는가
종료 코드: 0 = 정상, 1 = 위반
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FEATURES = ROOT / "features.json"


def committed():
    r = subprocess.run(["git", "show", "HEAD:features.json"], cwd=ROOT, capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 else None


def main() -> int:
    now = json.loads(FEATURES.read_text(encoding="utf-8"))
    errors = []

    base = committed()
    if base is not None:
        strip = [{k: v for k, v in f.items() if k != "passes"} for f in base]
        if strip != [{k: v for k, v in f.items() if k != "passes"} for f in now]:
            errors.append(
                "features.json에서 passes 외의 내용이 바뀌었다. 기능 정의는 사람만 수정한다. 되돌려라."
            )

    for f in now:
        test = ROOT / f["test"].split("::")[0]
        if not f["passes"]:
            print(f"  -  {f['id']} 미완료")
            continue
        if not test.exists():
            errors.append(f"{f['id']}: passes=true 인데 테스트 {f['test']} 가 없다.")
            continue
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", f["test"]], cwd=ROOT, capture_output=True, text=True
        )
        if r.returncode != 0:
            errors.append(f"{f['id']}: passes=true 인데 테스트가 실패한다.\n{r.stdout[-800:]}")
        else:
            print(f"  ✓  {f['id']} 테스트 통과")

    for e in errors:
        print(f"  ✗  {e}")
    done = sum(f["passes"] for f in now)
    print(f"진행: {done}/{len(now)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
