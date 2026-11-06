"""Case loading and derived quantities.

Nothing in this project hard-codes a case number. Everything comes from
case/byu_case.yaml through this module. If you change reactor or paper later
(the MHI fallback, say), you edit one YAML file and nothing else.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .species import SPECIES

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASE = PROJECT_ROOT / "case" / "byu_case.yaml"


@dataclass
class Case:
    raw: dict
    # geometry
    diameter: float = 0.0
    length: float = 0.0
    area: float = 0.0
    # operating
    pressure: float = 0.0
    # streams
    inlet_moles: dict = field(default_factory=dict)  # species -> mol/s
    inlet_T: float = 0.0
    coal_feed: float = 0.0  # kg/s as received
    # fuel breakdown, kg/s
    m_ash: float = 0.0
    m_moisture: float = 0.0
    m_daf: float = 0.0       # dry ash free coal = VM + FC
    m_fixed_carbon: float = 0.0
    m_volatile: float = 0.0
    # particle
    dp: float = 0.0
    rho_p: float = 0.0
    n_particles: float = 0.0  # particles/s
    # energy
    hhv_daf: float = 0.0      # J/kg
    hf_coal: float = 0.0      # J/kg
    # filled in by reactor_1d.solve — see TODO(ignition)
    ignition_energy_W: float = 0.0
    ignition_T: float = 0.0
    daf_y: dict = field(default_factory=dict)


def channiwala_hhv(C: float, H: float, O: float, N: float, S: float) -> float:
    """HHV in MJ/kg from ultimate analysis in mass %.

    This is the SAME correlation used in your course gasification tutorial
    (Problem 3, the peat problem):

        HHV = 0.3516C + 1.16225H - 0.1109O + 0.0628N + 0.10465S

    Using it here is deliberate: when an examiner asks where your coal heating
    value came from, "the correlation from the course tutorial" is a very good
    answer.

    TODO(hhv): if the paper reports a measured HHV, use that instead and note
    the difference from the correlation. A 2-3% discrepancy is normal and
    worth one sentence.
    """
    return 0.3516 * C + 1.16225 * H - 0.1109 * O + 0.0628 * N + 0.10465 * S


def coal_formation_enthalpy(hhv_J_per_kg: float, yC: float, yH: float) -> float:
    """Enthalpy of formation of the coal [J/kg], back-calculated from its HHV.

    Derivation (write this out in your report appendix — it is the kind of
    thing that shows you understand the thermodynamics rather than copying it):

        coal + O2 -> CO2 + H2O(liquid)          dH = -HHV

        dH = sum(hf_products) - hf_coal
        => hf_coal = sum(hf_products) + HHV

    Per kg of daf coal:
        n_CO2  = yC / M_C
        n_H2O  = yH / (2 * M_H)          because 2 H atoms make one H2O
        hf_H2O(liquid) = -285830 J/mol   (note: LIQUID, because HHV)
    """
    n_co2 = yC / 0.012011
    n_h2o = yH / (2.0 * 0.001008)
    hf_products = n_co2 * (-393522.0) + n_h2o * (-285830.0)
    return hf_products + hhv_J_per_kg


def load_case(path: Path | str | None = None) -> Case:
    path = Path(path) if path else DEFAULT_CASE
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    c = Case(raw=raw)
    g = raw["geometry"]
    c.diameter = float(g["diameter_m"])
    c.length = float(g["length_m"])
    c.area = math.pi * c.diameter ** 2 / 4.0
    c.pressure = float(raw["operating"]["pressure_Pa"])

    # ---- inlet gas: combine primary and secondary into one plug-flow inlet.
    # NOTE(mixing): this is the central Tier-1 approximation. A real
    # entrained-flow gasifier has two coaxial jets that take some distance to
    # mix, and that mixing length is a big part of the flame structure. Tier 1
    # assumes they are perfectly mixed at z=0. Tier 2 resolves it properly.
    # Say this explicitly in the report — it is the honest limitation and the
    # main reason your near-inlet profile will differ from the experiment.
    inl = raw["inlets"]
    moles = {}
    total_mass = 0.0
    T_weighted = 0.0
    for key in ("primary", "secondary"):
        s = inl[key]
        mdot = float(s["mass_flow_g_s"]) / 1000.0  # kg/s
        x = s["composition_mol_frac"]
        mw = sum(x[sp] * SPECIES[sp].mw for sp in x)
        n_total = mdot / mw
        for sp, frac in x.items():
            moles[sp] = moles.get(sp, 0.0) + n_total * frac
        total_mass += mdot
        T_weighted += mdot * float(s["temperature_K"])
    c.inlet_moles = moles
    c.inlet_T = T_weighted / total_mass

    # ---- fuel
    f = raw["fuel"]
    prox = f["proximate_wt_pct"]
    ult = f["ultimate_wt_pct"]

    feed = f.get("feed_rate_kg_s")
    if feed is None:
        raise ValueError(
            "fuel.feed_rate_kg_s must be set from the selected reference case; "
            "do not silently substitute an estimated feed rate."
        )
    c.coal_feed = float(feed)

    c.m_ash = c.coal_feed * prox["ash"] / 100.0
    c.m_moisture = c.coal_feed * prox["moisture"] / 100.0
    c.m_volatile = c.coal_feed * prox["volatile_matter"] / 100.0
    c.m_fixed_carbon = c.coal_feed * prox["fixed_carbon"] / 100.0
    c.m_daf = c.m_volatile + c.m_fixed_carbon

    # moisture evaporates almost immediately — add it to the inlet steam.
    # TODO(drying): model drying as a rate process rather than instantaneous.
    # At 36 um and 1e5 K/s heating it really is nearly instantaneous, so this
    # is a defensible simplification. Say so.
    c.inlet_moles["H2O"] = c.inlet_moles.get("H2O", 0.0) + c.m_moisture / SPECIES["H2O"].mw

    p = f["particles"]
    c.dp = float(p["mean_diameter_um"]) * 1e-6
    c.rho_p = float(p["density_kg_m3"])
    m_particle = c.rho_p * math.pi / 6.0 * c.dp ** 3
    c.n_particles = c.coal_feed / m_particle

    hhv_mj = f.get("hhv_MJ_per_kg")
    if hhv_mj is None:
        hhv_mj = channiwala_hhv(ult["C"], ult["H"], ult["O"], ult["N"], ult["S"])
    c.hhv_daf = float(hhv_mj) * 1e6
    c.hf_coal = coal_formation_enthalpy(
        c.hhv_daf, ult["C"] / 100.0, ult["H"] / 100.0
    )
    return c


def summary(c: Case) -> str:
    lines = [
        "CASE SUMMARY",
        "-" * 60,
        f"  reactor            {c.diameter:.3f} m dia x {c.length:.2f} m  (A = {c.area:.5f} m2)",
        f"  pressure           {c.pressure/1e5:.3f} bar",
        f"  inlet gas T        {c.inlet_T:.1f} K",
        f"  coal feed          {c.coal_feed*1e3:.3f} g/s   ({c.coal_feed*86400:.2f} kg/day)",
        f"    volatile matter  {c.m_volatile*1e3:.3f} g/s",
        f"    fixed carbon     {c.m_fixed_carbon*1e3:.3f} g/s",
        f"    ash              {c.m_ash*1e3:.3f} g/s",
        f"    moisture         {c.m_moisture*1e3:.3f} g/s  (added to inlet steam)",
        f"  particle dp        {c.dp*1e6:.1f} um   ({c.n_particles:.3e} particles/s)",
        f"  HHV (daf)          {c.hhv_daf/1e6:.2f} MJ/kg",
        f"  hf_coal            {c.hf_coal/1e6:.3f} MJ/kg",
        "  inlet moles [mol/s]:",
    ]
    for sp, n in sorted(c.inlet_moles.items()):
        lines.append(f"    {sp:<5s} {n:.5f}")
    return "\n".join(lines)
