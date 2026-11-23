"""Every number in CLAIMS.md must still match the committed results."""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_verify_claims_passes() -> None:
    run = subprocess.run(
        [sys.executable, "eval/verify_claims.py"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert "FAIL" not in run.stdout
