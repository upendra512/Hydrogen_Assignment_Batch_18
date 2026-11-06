#!/usr/bin/env python3
"""Mass-weighted Rosin-Rammler sensitivity using independent Tier 1 bins.

The study is a sensitivity of the current plug-flow chemistry, not a validated
polydisperse CFD prediction. Each diameter bin receives its Rosin-Rammler mass
fraction of the coal feed. Product flows and fuel-based metrics are then
combined by mass fraction.
"""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gasifier import postprocess as pp
from gasifier import reactor_1d
from gasifier.config import load_case

ROOT = Path(__file__).resolve().parents[1]


def rosin_rammler_bins(d_scale_um: float, spread: float, n_bins: int = 6,
                       d_min_um: float = 1.0, d_max_um: float = 85.0):
    """Return truncated mass-bin midpoint diameters and normalized weights.

    The cumulative mass fraction below d is F(d)=1-exp(-(d/d_scale)^n).
    Bin edges are equally spaced in cumulative mass, so each bin has equal
    weight before the small diameter-range truncation is normalized out.
    """
    if d_scale_um <= 0 or spread <= 0 or n_bins < 1:
        raise ValueError("d_scale, spread and n_bins must be positive")
    F_min = 1.0 - math.exp(-((d_min_um / d_scale_um) ** spread))
    F_max = 1.0 - math.exp(-((d_max_um / d_scale_um) ** spread))
    edges = np.linspace(F_min, F_max, n_bins + 1)
    fractions = np.diff(edges)
    q_mid = 0.5 * (edges[:-1] + edges[1:])
    diameters = d_scale_um * (-np.log1p(-q_mid)) ** (1.0 / spread)
    fractions /= fractions.sum()
    return diameters, fractions


def run_diameter(dp_um: float):
    case = load_case()
    case.dp = dp_um * 1e-6
    particle_mass = case.rho_p * math.pi / 6.0 * case.dp ** 3
    case.n_particles = case.coal_feed / particle_mass
    return reactor_1d.solve(case, n_out=120)


def evaluate_distribution(d_scale_um: float, spread: float | None,
                          n_bins: int = 6) -> dict:
    if spread is None:
        diameters = np.array([d_scale_um])
        weights = np.array([1.0])
        label = "monodisperse"
    else:
        diameters, weights = rosin_rammler_bins(d_scale_um, spread, n_bins)
        label = "Rosin-Rammler"

    results = [run_diameter(float(dp)) for dp in diameters]
    conversion = sum(w * pp.carbon_conversion(result)
                     for w, result in zip(weights, results))
    cge = sum(w * pp.cold_gas_efficiency(result)
              for w, result in zip(weights, results))
    species = ("CO", "H2", "CO2", "CH4")
    outlet = {sp: sum(w * result["moles"][sp][-1]
                      for w, result in zip(weights, results))
              for sp in species}
    total_syngas = sum(outlet.values())
    composition = {sp: 100.0 * amount / max(total_syngas, 1e-30)
                   for sp, amount in outlet.items()}
    return {
        "distribution": label,
        "d_scale_um": d_scale_um,
        "spread": "" if spread is None else spread,
        "n_bins": len(diameters),
        "carbon_conversion_pct": 100.0 * conversion,
        "cold_gas_efficiency_pct_course_LHV": 100.0 * cge,
        "dry_inert_free_CO_vol_pct": composition["CO"],
        "dry_inert_free_H2_vol_pct": composition["H2"],
        "dry_inert_free_CO2_vol_pct": composition["CO2"],
        "dry_inert_free_CH4_vol_pct": composition["CH4"],
        "H2_to_CO_molar_ratio": outlet["H2"] / max(outlet["CO"], 1e-30),
    }


def main() -> int:
    conditions = [(d, n) for d in (20.0, 36.0, 60.0)
                  for n in (0.7, 1.033, 1.5)]
    rows = []
    for d_scale, spread in conditions:
        print(f"Running RR d_scale={d_scale:g} um, spread={spread:g} ...", flush=True)
        row = evaluate_distribution(d_scale, spread)
        rows.append(row)
        print("  Xc %.2f%%, CGE %.2f%%, H2/CO %.3f" % (
            row["carbon_conversion_pct"], row["cold_gas_efficiency_pct_course_LHV"],
            row["H2_to_CO_molar_ratio"]))

    print("Running monodisperse 36 um reference ...", flush=True)
    mono = evaluate_distribution(36.0, None)
    rows.append(mono)

    out = ROOT / "report" / "particle_size_sensitivity.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FormatStrFormatter
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.5))
    colors = {0.7: "#1f6fb2", 1.033: "#c1451b", 1.5: "#3f8f5c"}
    for spread in (0.7, 1.033, 1.5):
        selected = [row for row in rows if row["spread"] == spread]
        axes[0].plot([row["d_scale_um"] for row in selected],
                     [row["carbon_conversion_pct"] for row in selected],
                     "o-", color=colors[spread], label=f"spread {spread:g}")
        axes[1].plot([row["d_scale_um"] for row in selected],
                     [row["H2_to_CO_molar_ratio"] for row in selected],
                     "o-", color=colors[spread], label=f"spread {spread:g}")
    axes[0].set_xlabel("Rosin-Rammler scale diameter [um]")
    axes[0].set_ylabel("mass-weighted carbon conversion [%]")
    axes[0].set_ylim(99.5, 100.5)
    axes[0].yaxis.set_major_formatter(FormatStrFormatter("%.1f"))
    axes[1].set_xlabel("Rosin-Rammler scale diameter [um]")
    axes[1].set_ylabel("mass-weighted outlet H2 / CO")
    axes[1].set_ylim(0.44, 0.46)
    axes[1].yaxis.set_major_formatter(FormatStrFormatter("%.3f"))
    for ax in axes:
        ax.grid(alpha=0.25)
    axes[1].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    figure = ROOT / "report" / "fig_particle_size_sensitivity.png"
    fig.savefig(figure, dpi=180)
    plt.close(fig)
    print(f"Wrote {out}")
    print(f"Wrote {figure}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
