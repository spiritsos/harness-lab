#!/usr/bin/env python3
"""하네스 Eval 러너 (M7). 시나리오마다 깨끗한 git worktree에서 claude -p를 돌리고 결정론적으로 채점한다.

사용:
  python evals/run_evals.py                 # 현재 브랜치(HEAD)의 하네스로 평가
  python evals/run_evals.py --ref stage-0   # 하네스 없는 시작 상태로 평가 → 전/후 비교
  python evals/run_evals.py --only E-01     # 시나리오 하나만
  python evals/run_evals.py --dry-run       # claude 호출 없이 채점 로직만 확인

결과는 evals/results-<ref>.json 에 저장된다. (작업 성공률 · 턴 수 · 비용)
"""

import argparse
import json
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE = shutil.which("claude") or "claude"  # Windows의 claude.cmd도 찾는다
SCENARIOS = json.loads((Path(__file__).parent / "scenarios.json").read_text(encoding="utf-8"))


def sh(cmd, cwd, **kw):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, **kw)


def check(s, wt: Path, output: str) -> tuple[bool, str]:
    kind, arg = s["check"], s["arg"]
    if kind == "output_not_contains":
        return arg not in output, f"출력에 '{arg}' 포함 여부"
    if kind == "file_exists":
        return (wt / arg).exists(), f"{arg} 존재 여부"
    if kind == "migration_untouched_and_new_file":
        touched = sh(["git", "diff", "--quiet", "HEAD", "--", arg], wt).returncode != 0
        new = sh(["git", "ls-files", "--others", "--exclude-standard", "migrations/"], wt).stdout.strip()
        committed_new = sh(
            ["git", "diff", "--name-only", "--diff-filter=A", "HEAD@{1}", "--", "migrations/"], wt
        )
        has_new = bool(new) or bool(committed_new.stdout.strip())
        return (not touched) and has_new, f"기존 파일 수정={touched}, 새 마이그레이션={has_new}"
    if kind == "tests_and_conventions_pass":
        t = sh([sys.executable, "dev.py", "test"], wt).returncode == 0
        c = sh([sys.executable, ".claude/skills/team-conventions/scripts/check_layers.py"], wt)
        conv = c.returncode == 0 if (wt / ".claude/skills").exists() else True
        return t and conv, f"python dev.py test={t}, 컨벤션={conv}"
    if kind == "output_contains_sql_result":
        n = sqlite3.connect(wt / "data/app.db").execute(arg).fetchone()[0]
        return re.search(rf"(?<!\d){n}(?!\d)", output) is not None, f"정답 {n}건 포함 여부"
    raise ValueError(kind)


def run_one(s, ref: str, dry: bool) -> dict:
    tmp = Path(tempfile.mkdtemp(prefix=f"eval-{s['id']}-"))
    wt = tmp / "repo"
    sh(["git", "worktree", "add", "--detach", str(wt), ref], ROOT, check=True)
    try:
        sh([sys.executable, "scripts/seed.py"], wt)
        meta = {}
        if dry:
            output = ""
        else:
            r = sh(
                [CLAUDE, "-p", s["prompt"], "--output-format", "json", "--max-turns", "20"],
                wt,
                timeout=600,
            )
            try:
                meta = json.loads(r.stdout)
                output = meta.get("result", "") or ""
            except json.JSONDecodeError:
                output = r.stdout + r.stderr
        ok, why = check(s, wt, output)
        return {
            "id": s["id"],
            "element": s["element"],
            "pass": ok,
            "why": why,
            "turns": meta.get("num_turns"),
            "cost_usd": meta.get("total_cost_usd"),
        }
    finally:
        sh(["git", "worktree", "remove", "--force", str(wt)], ROOT)
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="HEAD")
    ap.add_argument("--only")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    results = []
    for s in SCENARIOS:
        if a.only and s["id"] != a.only:
            continue
        res = run_one(s, a.ref, a.dry_run)
        results.append(res)
        print(f"{'PASS' if res['pass'] else 'FAIL'}  {res['id']}  {res['element']:<18} {res['why']}")

    passed = sum(r["pass"] for r in results)
    print(f"\n작업 성공률: {passed}/{len(results)}  (ref={a.ref})")
    out = Path(__file__).parent / f"results-{a.ref.replace('/', '_')}.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
