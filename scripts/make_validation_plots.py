#!/usr/bin/env python3
"""Compare digitized Fig. 9 centerline measurements with radial-model near-axis values.

Run scripts/run_tier2.py first, then:
    python scripts/make_validation_plots.py

Errors are reported as absolute composition differences in percentage points,
matching the paper's Table 8 convention. H2O is shown but not scored in the
interpretation because the reference reports about +/-14% uncertainty.
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "validation" / "fig09_axial_centerline.csv"
MODEL = ROOT / "report" / "tier2_summary.csv"
PLOT = ROOT / "report" / "fig_validation_axial_centerline.png"
ERRORS = ROOT / "report" / "validation_errors.csv"

# Table 8, modified/optimized parameters, mean then maximum absolute error (%).
# Since the paper defines delta-e as |x_exp - x_num|, these are composition
# differences in percentage points, not relative percentage errors.
PAPER_TABLE8 = {
    "CO": (4.82, 18.48),
    "H2": (5.47, 7.95),
    "CO2": (4.72, 10.15),
    "H2O": (9.58, 20.22),
}
EXP_COLUMNS = {"CO": "CO_molfrac_pct", "H2": "H2_molfrac_pct",
               "CO2": "CO2_molfrac_pct", "H2O": "H2O_molfrac_pct"}
COLORS = {"CO": "#1f6fb2", "H2": "#c1451b", "CO2": "#3f8f5c", "H2O": "#7b5ea7"}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(line for line in fh if not line.startswith("#")))


def main() -> int:
    if not DATA.exists():
        raise SystemExit(f"Missing digitized measurements: {DATA}")
    if not MODEL.exists():
        raise SystemExit(f"Missing radial-model profile: {MODEL}; run the radial calculation first")

    exp_rows = read_rows(DATA)
    model_rows = read_rows(MODEL)
    z_model = np.array([float(row["z_m"]) for row in model_rows])
    results: dict[str, dict[str, np.ndarray | float]] = {}

    for sp, exp_col in EXP_COLUMNS.items():
        z_exp, y_exp = [], []
        for row in exp_rows:
            value = row.get(exp_col, "")
            if value not in (None, ""):
                z_exp.append(float(row["z_m"]))
                y_exp.append(float(value))
        if not z_exp:
            continue
        model_col = f"near_axis_x_{sp}"
        if model_col not in model_rows[0]:
            raise SystemExit(f"{MODEL} lacks {model_col}; rerun scripts/run_tier2.py")
        y_model = 100.0 * np.array([float(row[model_col]) for row in model_rows])
        z_exp_a, y_exp_a = np.asarray(z_exp), np.asarray(y_exp)
        y_at_points = np.interp(z_exp_a, z_model, y_model)
        abs_pp = np.abs(y_at_points - y_exp_a)
        paper_mean, paper_max = PAPER_TABLE8[sp]
        results[sp] = {
            "z_exp": z_exp_a, "y_exp": y_exp_a, "y_model": y_model,
            "mean": float(abs_pp.mean()), "max": float(abs_pp.max()),
            "n": len(abs_pp), "paper_mean": paper_mean, "paper_max": paper_max,
        }

    with ERRORS.open("w", newline="", encoding="utf-8") as fh:
        fields = ["species", "n_points", "mean_abs_error_pp", "max_abs_error_pp",
                  "paper_table8_mean_abs_error_pp", "paper_table8_max_abs_error_pp"]
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for sp, row in results.items():
            writer.writerow({"species": sp, "n_points": row["n"],
                             "mean_abs_error_pp": f"{row['mean']:.3f}",
                             "max_abs_error_pp": f"{row['max']:.3f}",
                             "paper_table8_mean_abs_error_pp": f"{row['paper_mean']:.2f}",
                             "paper_table8_max_abs_error_pp": f"{row['paper_max']:.2f}"})

    fig, axes = plt.subplots(2, 2, figsize=(9.2, 6.2), sharex=True)
    for ax, sp in zip(axes.flat, EXP_COLUMNS):
        if sp not in results:
            ax.set_visible(False)
            continue
        row = results[sp]
        ax.plot(z_model, row["y_model"], color=COLORS[sp], lw=1.8,
                label="Batch 18 radial-model near-axis (r=0.83 mm)")
        ax.scatter(row["z_exp"], row["y_exp"], marker="s", s=28,
                   color="#ed7d31", edgecolor="white", linewidth=0.4,
                   zorder=3, label="Digitized experiment")
        ax.text(0.98, 0.96,
                f"n={row['n']}  mean |error|={row['mean']:.1f} pp  max={row['max']:.1f} pp",
                transform=ax.transAxes, ha="right", va="top", fontsize=8,
                bbox={"facecolor": "white", "edgecolor": "#d6e0e6", "alpha": 0.9})
        ax.set_title(sp)
        ax.set_xlim(0, 1.8)
        ax.set_ylim(bottom=0)
        ax.grid(alpha=0.25)
        ax.set_ylabel("Mole fraction (%)")
        ax.legend(fontsize=7, frameon=False, loc="lower right")
    for ax in axes[-1, :]:
        ax.set_xlabel("Axial distance z (m)")
    fig.suptitle("Near-axis model profile versus centerline markers from Figure 9")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(PLOT, dpi=220)
    plt.close(fig)

    print("Absolute composition errors (percentage points)")
    print(f"{'species':<6} {'n':>3} {'Batch18 mean':>14} {'Batch18 max':>12} {'paper mean':>12} {'paper max':>11}")
    for sp, row in results.items():
        print(f"{sp:<6} {row['n']:>3} {row['mean']:>14.3f} {row['max']:>12.3f} "
              f"{row['paper_mean']:>12.2f} {row['paper_max']:>11.2f}")
    print(f"Plot: {PLOT}")
    print(f"Errors: {ERRORS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
