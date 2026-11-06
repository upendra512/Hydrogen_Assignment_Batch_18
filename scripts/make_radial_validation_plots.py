#!/usr/bin/env python3
"""Compare radial-model profiles with digitized experimental markers.

Run `scripts/run_tier2.py` first so report/tier2_radial_profiles.csv exists.
H2O is plotted only as context and omitted from error scoring because the
reference paper derives its plotted values from hydrogen balance.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "validation" / "fig12_14_radial_experiment.csv"
MODEL = ROOT / "report" / "tier2_radial_profiles.csv"
ERRORS = ROOT / "report" / "validation_radial_errors.csv"
PLOT = ROOT / "report" / "fig_validation_radial_profiles.png"
ERROR_PLOT = ROOT / "report" / "fig_validation_radial_errors.png"
STATIONS = (0.13, 0.20, 0.28, 0.34, 0.51, 0.81, 1.12, 1.73)
SPECIES = ("CO", "H2", "CO2")
COLORS = {"CO": "#1f6fb2", "H2": "#c1451b", "CO2": "#3f8f5c"}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(line for line in stream if not line.startswith("#")))


def main() -> int:
    if not DATA.exists() or not MODEL.exists():
        raise SystemExit("Missing radial experiment or model data; digitize markers and run the radial calculation first.")
    exp_rows = read_rows(DATA)
    model_rows = read_rows(MODEL)
    profiles: dict[float, dict[str, np.ndarray]] = {}
    for station in STATIONS:
        rows = [row for row in model_rows if abs(float(row["z_m"]) - station) < 1e-9]
        rows.sort(key=lambda row: float(row["r_m"]))
        if not rows:
            raise SystemExit(f"No model radial profile at z={station:.2f} m")
        profiles[station] = {
            "r": np.array([float(row["r_m"]) for row in rows]),
            **{sp: 100.0 * np.array([float(row[f"x_{sp}"]) for row in rows])
               for sp in (*SPECIES, "H2O")},
        }

    errors: dict[tuple[str, float], list[float]] = defaultdict(list)
    for row in exp_rows:
        sp = row["species"]
        station = float(row["axial_station_m"])
        if sp not in SPECIES:
            continue
        profile = profiles[station]
        radius = float(row["radius_m"])
        predicted = float(np.interp(radius, profile["r"], profile[sp]))
        measured = float(row["mole_fraction_pct"])
        errors[(sp, station)].append(abs(predicted - measured))

    with ERRORS.open("w", newline="", encoding="utf-8") as stream:
        fields = ["species", "axial_station_m", "n_points", "mean_abs_error_pp", "max_abs_error_pp"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for sp in SPECIES:
            pooled = [value for station in STATIONS for value in errors[(sp, station)]]
            writer.writerow({"species": sp, "axial_station_m": "all",
                             "n_points": len(pooled),
                             "mean_abs_error_pp": f"{np.mean(pooled):.3f}",
                             "max_abs_error_pp": f"{np.max(pooled):.3f}"})
            for station in STATIONS:
                values = errors[(sp, station)]
                writer.writerow({"species": sp, "axial_station_m": f"{station:.2f}",
                                 "n_points": len(values),
                                 "mean_abs_error_pp": f"{np.mean(values):.3f}",
                                 "max_abs_error_pp": f"{np.max(values):.3f}"})

    # Four representative stations show the radial shape from flame zone to outlet.
    selected = (0.13, 0.28, 0.51, 1.73)
    fig, axes = plt.subplots(3, 4, figsize=(10.0, 6.6), sharex=True)
    for i, sp in enumerate(SPECIES):
        for j, station in enumerate(selected):
            ax = axes[i, j]
            profile = profiles[station]
            ax.plot(profile["r"], profile[sp], color=COLORS[sp], lw=1.5,
                    label="Batch 18 radial model")
            rows = [row for row in exp_rows
                    if row["species"] == sp and abs(float(row["axial_station_m"]) - station) < 1e-9]
            ax.scatter([float(row["radius_m"]) for row in rows],
                       [float(row["mole_fraction_pct"]) for row in rows],
                       color="#ed7d31", edgecolor="white", linewidth=0.35,
                       marker="s", s=22, zorder=3, label="Digitized experiment")
            ax.set_title(f"z = {station:.2f} m", fontsize=8)
            ax.grid(alpha=0.22)
            ax.set_xlim(0, 0.1)
            ax.set_ylim(bottom=0)
            if j == 0:
                ax.set_ylabel(f"{sp} mole fraction (%)")
            if i == 2:
                ax.set_xlabel("Radius r (m)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False,
               bbox_to_anchor=(0.5, 1.015), fontsize=8)
    fig.suptitle("Radial model profiles against digitized experimental probes", y=1.06)
    fig.tight_layout()
    fig.savefig(PLOT, dpi=220, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(9.0, 3.1), sharex=True)
    for ax, sp in zip(axes, SPECIES):
        means = [float(np.mean(errors[(sp, station)])) for station in STATIONS]
        ax.plot(STATIONS, means, "o-", color=COLORS[sp], lw=1.5)
        ax.set_title(sp)
        display_ticks = (0.13, 0.34, 0.81, 1.73)
        ax.set_xticks(display_ticks, [f"{z:.2f}" for z in display_ticks],
                      rotation=35, ha="right")
        ax.set_xlabel("Axial station z (m)")
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("Mean absolute error (percentage points)")
    fig.suptitle("Radial probe error by axial station")
    fig.tight_layout()
    fig.savefig(ERROR_PLOT, dpi=220)
    plt.close(fig)

    print("Pooled radial errors (absolute mole-fraction differences, pp)")
    for sp in SPECIES:
        pooled = [value for station in STATIONS for value in errors[(sp, station)]]
        print(f"{sp}: n={len(pooled)}, mean={np.mean(pooled):.3f}, max={np.max(pooled):.3f}")
    print(f"Wrote {PLOT}")
    print(f"Wrote {ERROR_PLOT}")
    print(f"Wrote {ERRORS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
