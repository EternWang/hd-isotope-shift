from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HDIsotopeShiftSmokeTest(unittest.TestCase):
    def test_rebuilds_day4_outputs(self) -> None:
        subprocess.run(
            [sys.executable, "analysis/recompute_tables_day4.py"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        summary_path = ROOT / "results" / "day4_summary.json"
        windows_path = ROOT / "analysis" / "windows.json"
        for path in [
            ROOT / "results" / "day4_shift_summary.png",
            ROOT / "results" / "day4_uncertainty_breakdown.png",
            ROOT / "results" / "day4_tableII_compare.csv",
            ROOT / "results" / "day4_tableIII_error_budget.csv",
        ]:
            self.assertGreater(path.stat().st_size, 0, path.as_posix())

        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertIn("Halpha", summary["outputs"])
        self.assertIn("Hbeta", summary["outputs"])
        self.assertLess(summary["outputs"]["Hbeta"]["percent_difference_%"], -4.0)
        self.assertGreater(windows_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
