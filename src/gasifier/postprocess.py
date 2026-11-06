"""
Post-processing: metrics, element balances, plots, validation overlays.

STATUS: working. Deliberately finished, because plotting is not what you are
being marked on and you should not spend week 6 fighting matplotlib.

The one thing you MUST engage with here is `element_balance`. Run it after
every single solve. A model that loses carbon is not a model, and finding out
in October is too late.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .species import CHAR_MW, GAS_SPECIES, SPECIES, element_flows

FIGDIR = Path(__file__).resolve().parents[2] / "report" / "figures"

# One consistent colour per species across EVERY figure in the report and the
# deck. Examiners notice when CO is blue on one slide and red on the next.
SPECIES_COLOURS = {
    "CO":  "#1f6fb2",
    "H2":  "#c1451b",
    "CO2": "#3f8f5c",
    "H2O": "#7b5ea7",
    "O2":  "#b08a1e",
    "CH4": "#8c6b52",
    "N2":  "#8a969c",
    "Ar":  "#b8c2c7",
}


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
def daf_mass_fractions(case) -> dict:
    """Ultimate analysis renormalised to a dry, ash-free basis.

    The reference reports C/H/N/S on a DAF basis. Oxygen is entered by
    difference, then this normalization removes any rounding drift. Ash and
    moisture belong to the as-received proximate analysis and are not included
    in this elemental vector.
    """
    ult = case.raw["fuel"]["ultimate_wt_pct"]
    total = sum(ult[e] for e in ("C", "H", "N", "S", "O"))
    return {e: ult[e] / total for e in ("C", "H", "N", "S", "O")}


def element_balance(result: dict) -> dict:
    """Compare atomic flows in at z=0 against z=L. Errors should be < 1%.

    Counts atoms in EVERY phase: gas, char, and the un-devolatilised coal.
    Forgetting the solid phases is the classic way to get a balance that looks
    broken when the model is fine (or, worse, one that looks fine when it is
    broken).

    If carbon is off by more than a per cent, stop and find out why before you
    look at any other number. Likely causes, in order:
      1. a char reaction stoichiometry is wrong
      2. build_volatile_split was edited and no longer closes
      3. integrator tolerance too loose (try rtol=1e-8)
    """
    case = result["case"]
    y = daf_mass_fractions(case)
    M = {"C": 0.012011, "H": 0.001008, "O": 0.015999, "N": 0.014007}

    def coal_atoms(mass_kg_s: float) -> dict:
        return {el: mass_kg_s * y[el] / M[el] for el in ("C", "H", "O", "N")}

    gas_in = {sp: result["moles"][sp][0] for sp in GAS_SPECIES}
    gas_out = {sp: result["moles"][sp][-1] for sp in GAS_SPECIES}

    e_in = element_flows(gas_in, 0.0)
    e_out = element_flows(gas_out, result["m_char"][-1] / CHAR_MW)

    for el, n in coal_atoms(case.m_daf).items():
        e_in[el] = e_in.get(el, 0.0) + n
    for el, n in coal_atoms(result["m_raw"][-1]).items():
        e_out[el] = e_out.get(el, 0.0) + n

    return {
        el: {
            "in": e_in[el],
            "out": e_out[el],
            "error_pct": 100.0 * (e_out[el] - e_in[el]) / max(abs(e_in[el]), 1e-12),
        }
        for el in e_in
    }


def carbon_conversion(result: dict) -> float:
    """Fraction of fuel carbon converted to gas. A headline validation number."""
    case = result["case"]
    yC = daf_mass_fractions(case)["C"]
    C_in = case.m_daf * yC
    C_solid_out = result["m_char"][-1] + result["m_raw"][-1] * yC
    return float(1.0 - C_solid_out / max(C_in, 1e-12))


def cold_gas_efficiency(result: dict) -> float:
    """CGE = chemical energy in the syngas / chemical energy in the fuel.

    LHV values in MJ/m3 taken from your own course tutorial (gasification
    deck, Problem 5): H2 10.8, CO 12.6, CH4 35.8. Using the course's own
    numbers is a deliberate choice — cite it.
    """
    case = result["case"]
    lhv_mol = {  # J/mol, converted from MJ/Nm3 at 22.4 L/mol
        "H2": 10.8e6 * 0.0224,
        "CO": 12.6e6 * 0.0224,
        "CH4": 35.8e6 * 0.0224,
    }
    e_gas = sum(result["moles"][sp][-1] * lhv_mol[sp] for sp in lhv_mol)
    e_fuel = case.m_daf * case.hhv_daf
    return float(e_gas / max(e_fuel, 1e-12))


def exit_composition(result: dict, dry: bool = True) -> dict:
    """Exit syngas composition in vol %. Set dry=True to match how papers report."""
    out = {sp: float(result["moles"][sp][-1]) for sp in GAS_SPECIES}
    if dry:
        out.pop("H2O", None)
    total = sum(out.values())
    return {sp: 100.0 * v / max(total, 1e-30) for sp, v in sorted(out.items())}


def summary_table(result: dict) -> str:
    eb = element_balance(result)
    lines = [
        "RESULT SUMMARY",
        "-" * 60,
        f"  peak gas temperature   {result['T'].max():8.1f} K   "
        f"(expect 2500-3000 K; see case yaml sanity_checks)",
        f"  exit temperature       {result['T'][-1]:8.1f} K",
        f"  carbon conversion      {100*carbon_conversion(result):8.2f} %",
        f"  cold gas efficiency    {100*cold_gas_efficiency(result):8.2f} %",
        "",
        "  element balance (should be < 1%):",
    ]
    for el, d in eb.items():
        flag = "  OK" if abs(d["error_pct"]) < 1.0 else "  <-- FIX THIS"
        lines.append(f"    {el:<3s} in {d['in']:.5e}  out {d['out']:.5e}  "
                     f"err {d['error_pct']:+7.3f} %{flag}")
    lines.append("")
    lines.append("  exit composition, dry vol %:")
    for sp, v in exit_composition(result).items():
        if v > 0.005:
            lines.append(f"    {sp:<5s} {v:7.3f}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------
def _style():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.dpi": 150,
        "font.size": 9,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.autolayout": True,
    })
    return plt


def plot_axial_species(result: dict, filename: str = "fig_axial_species.png",
                       species=("CO", "H2", "CO2", "H2O", "O2", "CH4"),
                       experimental: dict | None = None):
    """REQUIRED RESULT 2: species distribution graphs.

    experimental : optional {species: (z_array, x_array)} digitised from the
                   paper's Figure 9. Passing it turns this into REQUIRED
                   RESULT 5 as well.
    """
    plt = _style()
    FIGDIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    for sp in species:
        ax.plot(result["z"], 100.0 * result["x"][sp], lw=1.6,
                color=SPECIES_COLOURS.get(sp), label=sp)
        if experimental and sp in experimental:
            ze, xe = experimental[sp]
            ax.plot(ze, xe, "o", ms=4, mfc="none",
                    color=SPECIES_COLOURS.get(sp), label=f"{sp} (exp.)")
    ax.set_xlabel("axial distance  z  [m]")
    ax.set_ylabel("mole fraction  [%]")
    ax.legend(ncol=3, fontsize=7, frameon=False)
    fig.savefig(FIGDIR / filename)
    plt.close(fig)
    return FIGDIR / filename


def plot_axial_temperature(result: dict, filename: str = "fig_axial_temperature.png",
                           experimental=None):
    """REQUIRED RESULT 4 (the 1-D part of it)."""
    plt = _style()
    FIGDIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    ax.plot(result["z"], result["T"], lw=1.8, color="#a2410f", label="model")
    if experimental is not None:
        ze, Te = experimental
        ax.plot(ze, Te, "o", ms=4, mfc="none", color="#333", label="experiment")
        ax.legend(frameon=False)
    ax.set_xlabel("axial distance  z  [m]")
    ax.set_ylabel("temperature  [K]")
    fig.savefig(FIGDIR / filename)
    plt.close(fig)
    return FIGDIR / filename


def plot_conversion(result: dict, filename: str = "fig_conversion.png"):
    plt = _style()
    FIGDIR.mkdir(parents=True, exist_ok=True)
    case = result["case"]
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    ax.plot(result["z"], result["m_raw"] / case.m_daf, lw=1.6,
            label="un-devolatilised coal")
    ax.plot(result["z"], result["m_char"] / case.m_daf, lw=1.6, label="char")
    ax.set_xlabel("axial distance  z  [m]")
    ax.set_ylabel("mass fraction of initial daf coal")
    ax.legend(frameon=False)
    fig.savefig(FIGDIR / filename)
    plt.close(fig)
    return FIGDIR / filename


def plot_contour(field: np.ndarray, r: np.ndarray, z: np.ndarray, label: str,
                 filename: str, cmap: str = "inferno"):
    """REQUIRED RESULT 3 — the one that decides the grade. Tier 2 only.

    Convention: plot z horizontally, r vertically, and mirror about the axis so
    the reader sees the full reactor rather than half of it. Reviewers find
    half-reactors hard to read.
    """
    plt = _style()
    FIGDIR.mkdir(parents=True, exist_ok=True)
    Z, Rr = np.meshgrid(z, np.concatenate([-r[::-1], r]))
    F = np.vstack([field[::-1, :], field])
    fig, ax = plt.subplots(figsize=(7.0, 2.6))
    pc = ax.pcolormesh(Z, Rr, F, shading="auto", cmap=cmap)
    fig.colorbar(pc, ax=ax, label=label, pad=0.02)
    ax.set_xlabel("z [m]")
    ax.set_ylabel("r [m]")
    ax.set_aspect("auto")
    ax.grid(False)
    fig.savefig(FIGDIR / filename)
    plt.close(fig)
    return FIGDIR / filename


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def errors_against_experiment(model_z, model_x, exp_z, exp_x) -> dict:
    """Interpolate the model and report absolute composition differences.

    Inputs are mole fractions. Multiplying their absolute difference by 100
    reports errors in percentage points, matching the reference paper's
    Table 8 convention (not relative percentage error).
    """
    interp = np.interp(exp_z, model_z, model_x)
    err_pp = 100.0 * np.abs(interp - exp_x)
    return {"average_pp": float(err_pp.mean()), "max_pp": float(err_pp.max()),
            "n_points": int(len(exp_x))}
