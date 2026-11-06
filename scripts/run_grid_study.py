#!/usr/bin/env python3
"""Run the Tier 2 grid-refinement study and save comparable metrics."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np

from gasifier import postprocess as pp
from gasifier import reactor_2d
from gasifier.config import load_case


def main() -> int:
    case = load_case()
    sizes = [(20, 100), (40, 200), (80, 400), (120, 600)]
    rows = []
    previous = None
    for nr, nz in sizes:
        print(f"Running grid {nr} x {nz} ...", flush=True)
        grid = reactor_2d.Grid2D(case, nr=nr, nz=nz)
        result = reactor_2d.march(case, grid)
        avg_t = grid.integrate_radially(result["T"])
        row = {
            "nr": nr, "nz": nz,
            "peak_T_K": float(np.max(result["T"])),
            "outlet_area_average_T_K": float(grid.integrate_radially(result["T"][:, -1])),
            "carbon_conversion": pp.carbon_conversion(result),
            "dry_CO_vol_pct": pp.exit_composition(result)["CO"],
            "dry_H2_vol_pct": pp.exit_composition(result)["H2"],
            "dry_CO2_vol_pct": pp.exit_composition(result)["CO2"],
            "max_abs_element_error_pct": max(abs(v["error_pct"])
                                               for v in pp.element_balance(result).values()),
            "outlet_mean_axial_T_K": float(avg_t[-1]),
        }
        if previous is not None:
            for key in ("outlet_area_average_T_K", "carbon_conversion",
                        "dry_CO_vol_pct", "dry_H2_vol_pct", "dry_CO2_vol_pct"):
                row[f"change_vs_previous_{key}"] = row[key] - previous[key]
        rows.append(row)
        previous = row
        print("  peak T = %.1f K; outlet T = %.1f K; carbon conversion = %.2f%%; max |balance| = %.3g%%"
              % (row["peak_T_K"], row["outlet_area_average_T_K"],
                 100 * row["carbon_conversion"], row["max_abs_element_error_pct"]))

    outdir = Path(__file__).resolve().parents[1] / "report"
    outdir.mkdir(parents=True, exist_ok=True)
    csv_path = outdir / "grid_independence.csv"
    columns = list(dict.fromkeys(k for row in rows for k in row))
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.3))
    labels = [f"{r['nr']}×{r['nz']}" for r in rows]
    axes[0].plot(labels, [100 * r["carbon_conversion"] for r in rows], "o-", label="carbon conversion")
    axes[0].set_ylabel("carbon conversion [%]")
    axes[1].plot(labels, [r["outlet_area_average_T_K"] for r in rows], "o-", color="#a2410f")
    axes[1].set_ylabel("area-average outlet temperature [K]")
    for ax in axes:
        ax.set_xlabel("radial × axial grid")
        ax.grid(alpha=0.25)
    fig.tight_layout()
    png_path = outdir / "fig_grid_independence.png"
    fig.savefig(png_path, dpi=180)
    plt.close(fig)
    print(f"Wrote {csv_path}")
    print(f"Wrote {png_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
