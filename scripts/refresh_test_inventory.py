"""Refresh README/Makefile collection counts from a clean committed checkout."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from controlplane.report.test_inventory import refresh_test_inventory  # noqa: E402


if __name__ == "__main__":
    result = refresh_test_inventory(PROJECT_ROOT)
    print(f"Recorded {result['n_collected']} collected tests from {result['git_commit']}.")
    print("Collection does not claim that execution passed.")
