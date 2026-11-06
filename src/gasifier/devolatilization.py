"""
Devolatilisation — the competing two-step model (C2SM).

STATUS: uses the C2SM rate constants tabulated by Mularski & Modlinski (2021),
Table 5. The paper fitted these against FG-DVC; this project does not rerun
that fitting procedure or the full CFD coupling.

WHY THIS MODULE MATTERS MORE THAN YOU THINK
-------------------------------------------
The reference coal is 45.6 wt% volatile matter as received. On a dry-ash-free
basis that is about 51.1% of the coal (45.6 / (45.6 + 43.7)). Volatiles leave
the particle early and burn in the flame zone. Get devolatilisation wrong and
the whole temperature field is wrong, which makes every downstream species
wrong.
This is the single highest-leverage sub-model in the project.

THE PHYSICS
-----------
Kobayashi's competing two-step mechanism says a raw coal particle can follow
two parallel paths, one favoured at low temperature and one at high:

    raw coal --k1--> (1 - a1) char + a1 volatiles      (low-T path, low yield)
    raw coal --k2--> (1 - a2) char + a2 volatiles      (high-T path, high yield)

    k_i = A_i * exp(-E_i / (R * T_p))

The mass of volatiles released from an initial dry-ash-free coal mass m0:

    dm_v/dt = (a1*k1 + a2*k2) * (m0 - m_v_released_total)

The point of having two paths is that the SPLIT between them depends on
particle temperature, so the total volatile yield is not a fixed number —
it rises with heating rate. In an entrained-flow gasifier the heating rate is
~1e5 K/s, so the yield exceeds the proximate-analysis volatile matter. This is
the "Q factor" you will see in the literature.

WHAT IS AND IS NOT REPRODUCED
-----------------------------
This code uses the paper's reported C2SM rate constants for this coal. It does
not run the FG-DVC network model or repeat the parameter-fitting procedure.
The volatile species split and its transport through the reduced reactor model
remain separate approximations.
"""
from __future__ import annotations

import math

R = 8.314462618  # J/(mol K)

# ---------------------------------------------------------------------------
# C2SM parameters used in Mularski & Modliński (2021), Table 5. The authors
# tuned these against FG-DVC for the reference coal. Keep the units explicit:
# A is 1/s, E is J/kmol in the table, and alpha is the volatile yield.
# ---------------------------------------------------------------------------
A1 = 4.269e4    # 1/s, Table 5
E1 = 3.71e7     # J/kmol, Table 5
A2 = 9.785e6    # 1/s, Table 5
E2 = 8.993e7    # J/kmol, Table 5
ALPHA1 = 0.246  # volatile yield fraction, low-T path
ALPHA2 = 0.931  # volatile yield fraction, high-T path

# Kobayashi's activation energies are usually quoted per kmol. Convert once.
E1_J_PER_MOL = E1 / 1000.0
E2_J_PER_MOL = E2 / 1000.0


def devol_rate_constants(Tp: float) -> tuple:
    """Return (k1, k2) in 1/s at particle temperature Tp [K]."""
    Tp = max(Tp, 300.0)  # guard: exp() of a silly number kills the integrator
    k1 = A1 * math.exp(-E1_J_PER_MOL / (R * Tp))
    k2 = A2 * math.exp(-E2_J_PER_MOL / (R * Tp))
    return k1, k2


def devol_mass_rate(m_raw_remaining: float, Tp: float) -> tuple:
    """Volatile release rate and char formation rate.

    Parameters
    ----------
    m_raw_remaining : kg/s of un-devolatilised daf coal still in the particles
    Tp : particle temperature [K]

    Returns
    -------
    (dm_volatiles_dt, dm_char_formed_dt) both in kg/s per second of residence,
    i.e. rates to be multiplied by dt (or dz/u) by the caller.
    """
    k1, k2 = devol_rate_constants(Tp)
    total = (k1 + k2) * m_raw_remaining
    volatiles = (ALPHA1 * k1 + ALPHA2 * k2) * m_raw_remaining
    char = total - volatiles
    return volatiles, char


# ---------------------------------------------------------------------------
# VOLATILE COMPOSITION
#
# The model releases a MASS of volatiles. Before that mass can burn, you must
# say WHAT it is chemically. This is settled by an element balance: whatever
# C, H and O sits in the coal but not in the char and not in the ash has to
# come out in the volatile gases.
#
# WHY THIS IS NOT A FREE CHOICE
# -----------------------------
# You have three equations (C, H, O) and five unknowns (CH4, CO, CO2, H2,
# H2O). The system is underdetermined, so you MUST add two assumptions. There
# is no way round it and every code makes this choice somewhere; most of them
# hide it. Ours is explicit, in `SPLIT_ASSUMPTIONS` below.
#
# WHAT THIS COAL FORCES ON YOU — work through this, it is instructive
# -------------------------------------------------------------------
# From the reference DAF ultimate analysis, each kg of daf coal contains about
# 64.6 mol C, 65.1 mol H, and 8.67 mol O. If the proximate fixed-carbon share
# is treated as pure-carbon char, the remaining volatile stream is roughly
# 46.7 mol C, 127.5 mol H, and 17.0 mol O per kg of volatile matter. These are
# bookkeeping estimates; the competing two-step model changes the char yield.
#
# Now try to place that carbon. Oxygen can bind at most one carbon atom per
# oxygen atom as CO; hydrogen can bind at most one carbon per four H atoms as
# CH4. Depending on the two split assumptions, residual carbon may remain for
# the soot/tar approximation below.
#
# That surplus carbon is TAR — heavy, hydrogen-poor aromatic material. It is
# why the reference paper models tar explicitly as a CxHyOz molecule with a C7
# backbone. We do not carry a tar species, so we retain the surplus carbon in
# the particle as soot, which then gasifies through the normal char reactions.
# This conserves atoms exactly and is physically defensible (tar does crack to
# soot), but it is an approximation and it belongs in your report.
#
# TODO(tar) — OWNER: chemistry lead — DUE: week 5, optional but high value
#   Add a TAR species to species.py with a C7HxOy formula, release it here
#   instead of routing surplus carbon to soot, and add a cracking reaction
#   TAR -> CO + H2 + soot. Then compare the two treatments. This is a real
#   model improvement, it directly mirrors what the reference paper does, and
#   it is exactly the kind of thing that makes a presentation memorable.
# ---------------------------------------------------------------------------

SPLIT_ASSUMPTIONS = {
    # TODO(volatile-split) — OWNER: chemistry lead — DUE: week 3
    #   These two numbers are the assumptions that close the underdetermined
    #   system. Vary them, see what they do to the exit H2:CO ratio, and
    #   justify your final choice with a citation. A sensitivity plot on
    #   `h_fraction_to_CH4` is a cheap, honest figure for the report.
    "oxygen_to_CO_fraction": 1.0,   # of volatile O: 1.0 -> all CO, 0.0 -> all CO2/H2O
    "h_fraction_to_CH4": 0.5,       # of volatile H: rest leaves as H2
}


def daf_fractions(case) -> dict:
    """Ultimate analysis renormalised to dry, ash-free mass fractions."""
    ult = case.raw["fuel"]["ultimate_wt_pct"]
    total = sum(ult[e] for e in ("C", "H", "N", "S", "O"))
    return {e: ult[e] / total for e in ("C", "H", "N", "S", "O")}


M_C, M_H, M_O, M_N = 0.012011, 0.001008, 0.015999, 0.014007


def partition(dm_daf: float, dm_char: float, y: dict) -> dict:
    """Split a devolatilising mass of coal into gas species, exactly.

    THIS IS THE HEART OF THE ELEMENT BOOKKEEPING. Read it before you change
    anything upstream of it.

    Parameters
    ----------
    dm_daf  : mass rate of daf coal leaving the raw state   [kg/s per m]
    dm_char : mass rate of that going to char (from C2SM)   [kg/s per m]
    y       : daf mass fractions, from daf_fractions()

    Returns
    -------
    {"gases": {species: mol/s per m}, "soot_C_kg": kg/s per m of extra char}

    WHY IT IS WRITTEN THIS WAY
    --------------------------
    An earlier version pre-computed a fixed "mol per kg of volatile matter"
    table from the proximate analysis. That is wrong, and subtly so: the C2SM
    char yield depends on particle temperature, so the volatile mass is NOT
    the proximate volatile matter. Pre-computing the split therefore leaks
    carbon at some temperatures and invents hydrogen at others — we saw -13% C
    and +17% H before fixing it. Deriving the split from the instantaneous
    char yield makes the balance exact at every temperature.

    Moral, worth a line in your report: element conservation is a property you
    design into the discretisation, not something you check at the end and
    hope for.
    """
    if dm_daf <= 0.0:
        return {"gases": {}, "soot_C_kg": 0.0}

    # elements leaving the raw coal
    nC = dm_daf * y["C"] / M_C
    nH = dm_daf * y["H"] / M_H
    nO = dm_daf * y["O"] / M_O
    nN = dm_daf * y["N"] / M_N

    # char is modelled as pure carbon and takes its share first
    nC_char = min(dm_char / M_C, nC)
    nC_vol = nC - nC_char

    a = SPLIT_ASSUMPTIONS
    fo = a["oxygen_to_CO_fraction"]
    fh = a["h_fraction_to_CH4"]

    # ORDER MATTERS. Allocate in order of scarcity, and never let an
    # allocation exceed what the element inventory can support. Getting this
    # order wrong is how you silently create or destroy oxygen.
    #
    # 1. carbon monoxide, limited by whichever of C or O runs out first
    n_CO = min(fo * nO, nC_vol)
    # 2. carbon dioxide from any oxygen left, again carbon-limited
    nO_left = nO - n_CO
    n_CO2 = min((1.0 - fo) * nO_left / 2.0 if fo < 1.0 else 0.0,
                max(nC_vol - n_CO, 0.0))
    # 3. whatever oxygen still remains must leave as water
    nO_left = nO - n_CO - 2.0 * n_CO2
    n_H2O = max(nO_left, 0.0)
    # 4. hydrogen: water first (it is already committed), then CH4, then H2
    nH_left = max(nH - 2.0 * n_H2O, 0.0)
    C_left = max(nC_vol - n_CO - n_CO2, 0.0)
    n_CH4 = min(fh * nH_left / 4.0, C_left)
    n_H2 = max((nH_left - 4.0 * n_CH4) / 2.0, 0.0)
    # 5. surplus carbon has nowhere to go: it is tar, retained as soot
    soot_C = max(C_left - n_CH4, 0.0)

    return {
        "gases": {"CO": n_CO, "CO2": n_CO2, "CH4": n_CH4,
                  "H2": n_H2, "H2O": n_H2O, "N2": nN / 2.0},
        "soot_C_kg": soot_C * M_C,
    }


def describe_split(case, T: float = 1800.0) -> str:
    """Print the split for 1 kg/s of daf coal at a representative temperature.

    Use it as a sanity check and quote the table in your report's methodology.
    """
    y = daf_fractions(case)
    vol, char = devol_mass_rate(1.0, T)
    tot = vol + char
    p = partition(1.0, char / max(tot, 1e-30), y)
    lines = [f"  volatile split at Tp = {T:.0f} K, per kg of daf coal devolatilised:",
             f"    char yield from C2SM : {char/max(tot,1e-30):.4f} kg/kg"]
    for sp, n in sorted(p["gases"].items()):
        if n > 1e-9:
            lines.append(f"    {sp:<5s} {n:9.4f} mol")
    lines.append(f"    soot  {p['soot_C_kg']:9.4f} kg  (surplus volatile carbon)")
    return "\n".join(lines)
