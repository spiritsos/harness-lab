"""DB를 통째로 지우고 다시 만든다. 되돌릴 수 없다."""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
shutil.rmtree(ROOT / "data", ignore_errors=True)
subprocess.run([sys.executable, str(ROOT / "scripts" / "seed.py")], check=True)
