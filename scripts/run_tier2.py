#!/usr/bin/env python3
"""Run the reduced 2-D model and produce species/temperature contours.

Examples:
    python scripts/run_tier2.py
    python scripts/run_tier2.py --nr 24 --nz 120
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gasifier import postprocess as pp
from gasifier import reactor_2d
from gasifier.config import load_case
from gasifier.devolatilization import daf_fractions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nr", type=int, default=None, help="radial cells")
    parser.add_argument("--nz", type=int, default=None, help="axial stations")
    args = parser.parse_args()

    case = load_case()
    grid = reactor_2d.Grid2D(case, nr=args.nr, nz=args.nz)
    print(f"BYU reduced 2-D model: {grid.nr} radial x {grid.nz} axial stations")
    print("Injector dimensions: primary ID 13 mm; secondary annulus OD 28.6 mm")
    print("Inlet background mixing fraction:",
          case.raw["geometry"]["injectors"]["background_mixing_fraction"])
    result = reactor_2d.march(case, grid)

    balance = pp.element_balance(result)
    print(f"Peak temperature: {np.max(result['T']):.1f} K")
    print(f"Area-weighted outlet temperature: {grid.integrate_radially(result['T'][:, -1]):.1f} K")
    print(f"Carbon conversion: {100 * pp.carbon_conversion(result):.2f}%")
    print("Dry outlet composition (vol %):")
    for sp, value in pp.exit_composition(result).items():
        print(f"  {sp}: {value:.3f}")
    inert_free_species = ("CO", "H2", "CO2", "CH4")
    inert_free_total = sum(result["moles"][sp][-1] for sp in inert_free_species)
    inert_free = {sp: 100.0 * result["moles"][sp][-1] / max(inert_free_total, 1e-30)
                  for sp in inert_free_species}
    print("Dry, inert-free outlet composition (vol %):")
    for sp, value in inert_free.items():
        print(f"  {sp}: {value:.3f}")
    print(f"Cold gas efficiency (course LHV basis): {100 * pp.cold_gas_efficiency(result):.2f}%")
    print("Global element balance (%):")
    for element, values in balance.items():
        print(f"  {element}: {values['error_pct']:+.8f}")

    initial_carbon = case.m_daf * daf_fractions(case)["C"]
    conversion = np.zeros_like(result["T"])
    for j, area in enumerate(grid.cell_area):
        coal_daf = case.m_daf * result["inlet_primary_weights"][j] * area
        char = result["radial_state"][j, :, 8]
        raw = result["radial_state"][j, :, 9]
        conversion[j] = 1.0 - (char + raw * daf_fractions(case)["C"]) / max(
            coal_daf * daf_fractions(case)["C"], 1e-30)
    conversion = np.clip(conversion, 0.0, 1.0)

    contour_files = []
    for name, label, cmap in [
        ("T", "temperature [K]", "inferno"),
        ("CO", "CO mole fraction", "viridis"),
        ("H2", "H2 mole fraction", "plasma"),
        ("CH4", "CH4 mole fraction", "copper"),
        ("CO2", "CO2 mole fraction", "magma"),
        ("O2", "O2 mole fraction", "cividis"),
        ("H2O", "H2O mole fraction", "cool"),
    ]:
        path = pp.plot_contour(result[name] if name == "T" else result["x"][name],
                               grid.r, grid.z, label,
                               f"fig_contour_{name}.png", cmap=cmap)
        contour_files.append(path)
    contour_files.append(pp.plot_contour(conversion, grid.r, grid.z,
                                         "fuel carbon conversion [-]",
                                         "fig_contour_carbon_conversion.png",
                                         cmap="cividis"))

    # Axial averages and innermost-annulus values accompany the contours.
    # The innermost annulus is a near-axis proxy, not a value at r=0.
    center = int(np.argmin(grid.r))
    avg_x = {sp: np.zeros(grid.nz) for sp in result["x"]}
    for sp in avg_x:
        avg_x[sp] = grid.integrate_radially(result["x"][sp])
    axial_path = pp.plot_axial_species(
        {"z": grid.z, "x": avg_x}, filename="fig_tier2_area_average_species.png")
    temp_avg_path = pp.plot_axial_temperature(
        {"z": grid.z, "T": grid.integrate_radially(result["T"])},
        filename="fig_tier2_area_average_temperature.png")

    out = Path(__file__).resolve().parents[1] / "report" / "tier2_summary.csv"
    with out.open("w", encoding="utf-8", newline="") as fh:
        import csv
        writer = csv.writer(fh)
        writer.writerow(["z_m", "area_average_T_K", "near_axis_T_K",
                         *[f"area_average_x_{sp}" for sp in avg_x],
                         *[f"near_axis_x_{sp}" for sp in avg_x]])
        for k, z in enumerate(grid.z):
            writer.writerow([f"{z:.8g}", f"{grid.integrate_radially(result['T'][:, k]):.8g}",
                             f"{result['T'][center, k]:.8g}",
                             *[f"{avg_x[sp][k]:.8g}" for sp in avg_x],
                             *[f"{result['x'][sp][center, k]:.8g}" for sp in avg_x]])

    # Preserve full radial composition profiles at the eight axial stations
    # used in the reference paper's radial probe figures (12-14).
    probe_stations = (0.13, 0.20, 0.28, 0.34, 0.51, 0.81, 1.12, 1.73)
    radial_path = out.with_name("tier2_radial_profiles.csv")
    with radial_path.open("w", encoding="utf-8", newline="") as fh:
        import csv
        writer = csv.writer(fh)
        writer.writerow(["z_m", "r_m", "x_CO", "x_H2", "x_CO2", "x_H2O"])
        for z_probe in probe_stations:
            for j, radius in enumerate(grid.r):
                values = [np.interp(z_probe, grid.z, result["x"][sp][j, :])
                          for sp in ("CO", "H2", "CO2", "H2O")]
                writer.writerow([f"{z_probe:.2f}", f"{radius:.8g}",
                                 *[f"{value:.8g}" for value in values]])
    print(f"Radial comparison profiles: {radial_path}")

    metrics_path = out.with_name("tier2_metrics.csv")
    metrics = {
        "nr": grid.nr,
        "nz": grid.nz,
        "peak_T_K": float(np.max(result["T"])),
        "outlet_area_average_T_K": float(grid.integrate_radially(result["T"][:, -1])),
        "carbon_conversion_pct": 100.0 * pp.carbon_conversion(result),
        "cold_gas_efficiency_pct_course_LHV": 100.0 * pp.cold_gas_efficiency(result),
        "max_abs_element_error_pct": max(abs(v["error_pct"]) for v in balance.values()),
        **{f"dry_inert_free_{sp}_vol_pct": value for sp, value in inert_free.items()},
    }
    with metrics_path.open("w", encoding="utf-8", newline="") as fh:
        import csv
        writer = csv.DictWriter(fh, fieldnames=list(metrics))
        writer.writeheader()
        writer.writerow(metrics)

    print("Figures:")
    for path in contour_files + [axial_path, temp_avg_path, out, metrics_path]:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
