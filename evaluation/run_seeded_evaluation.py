"""Run every seeded case through the checker and write the outcome table."""

import csv
from pathlib import Path

from evaluation.seeded_cases import CASES
from researchaudit.rule_checker import check_source

ROOT = Path(__file__).resolve().parents[1]


def run():
    rows = []
    for rule, name, source, should_fire in CASES:
        fired = any(f.rule_id == rule for f in check_source(source, "case.py"))
        rows.append({"rule": rule, "case": name, "should_fire": should_fire, "fired": fired,
                     "correct": should_fire == fired})
    out = ROOT / "results" / "seeded_case_results.csv"
    with out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows


if __name__ == "__main__":
    rows = run()
    print(f"{sum(r['correct'] for r in rows)} of {len(rows)} seeded cases behaved as designed")
