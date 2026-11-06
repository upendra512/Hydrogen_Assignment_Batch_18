#!/usr/bin/env python3
"""
Run the Tier 1 chemistry diagnostic and produce axial plots.

    python scripts/run_tier1.py

This reduced plug-flow model checks chemistry and element bookkeeping. It is
not the reported radial-annulus reactor model, and its full-burnout behavior
limits the particle-size diagnostic.

WHAT TO LOOK AT, IN THIS ORDER
------------------------------
  1. Check C/H/O/N/Ar balance closure.
  2. Check whether temperature recovery reaches a configured ceiling.
  3. Record residual outlet oxygen and carbon conversion; compare them with
     the reported experiment without tuning away discrepancies.
  4. Treat full carbon burnout as a known Tier 1 limitation, not a validated
     prediction.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gasifier import postprocess as pp
from gasifier import reactor_1d
from gasifier.config import load_case, summary


def main() -> int:
    case = load_case()
    print(summary(case))
    print()

    print("integrating Tier 1 ...")
    result = reactor_1d.solve(case)
    print()
    print(pp.summary_table(result))
    print()

    f1 = pp.plot_axial_species(result)
    f2 = pp.plot_axial_temperature(result)
    f3 = pp.plot_conversion(result)
    print("figures written:")
    for f in (f1, f2, f3):
        print(f"   {f}")

    print()
    print("NEXT: compare with the Tier 2 radial-annulus calculation and")
    print("      read docs/04_validation_protocol.md before interpreting fit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
