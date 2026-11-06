"""
Char conversion — the kinetic/diffusion-limited model (Baum & Street).

STATUS: uses the BYU-fitted kinetic-diffusion parameters reported in the
reference paper. The complete CFD and standalone CBK/E-CBK/G fitting workflow
are not implemented here.

THE PHYSICS
-----------
Once the volatiles have gone, what is left is char: essentially carbon plus
ash. It is consumed by three surface reactions.

    R1  C + 1/2 O2 -> CO          exothermic, fast. Sets the peak temperature.
    R2  C + CO2    -> 2 CO        Boudouard. Endothermic, slow.
    R3  C + H2O    -> CO + H2     Steam gasification. Endothermic.
                                  THIS IS YOUR MAIN HYDROGEN SOURCE.

Each is limited by two things in series: how fast the gas can diffuse to the
particle surface (k_d), and how fast the chemistry proceeds once it gets there
(k_s). Combining them like two resistances in series:

    rate = ( k_d * k_s / (k_d + k_s) ) * A_p * p_ox            [kg/s per particle]

At low temperature k_s is tiny and the reaction is kinetically controlled. At
high temperature k_s explodes and the reaction becomes diffusion controlled —
the particle burns as fast as oxidiser can reach it. In an entrained-flow
gasifier you pass through both regimes along the reactor, which is exactly why
a single-rate model fails and why the reference paper spends its whole length
optimising these parameters.

    k_d = C1 * [ (T_p + T_g)/2 ]^0.75 / d_p          diffusion rate coefficient
    k_s = A * exp(-E / (R * T_p))                     kinetic rate coefficient

WHAT THE PAPER FOUND — READ THIS BEFORE YOU TUNE ANYTHING
---------------------------------------------------------
Mularski & Modlinski report that the char kinetic parameters have an "extreme
impact" on the overall gas composition: different parameter sets change the
slope of the reforming zone and therefore the final CO and H2. Their whole
contribution is a procedure for optimising these numbers against the CBK/E and
CBK/G models.

So: do not be surprised when your first run is badly off. Being off here is
the expected result, and the report section explaining it is worth marks.
"""
from __future__ import annotations

import math

R = 8.314462618  # J/(mol K)


# ---------------------------------------------------------------------------
# Optimized kinetic-diffusion parameters from Mularski & Modliński (2021),
# Table 6, fitted against CBK/E and CBK/G for the BYU case. Their rate law is
# k_s = A * T**beta * exp(-E/(R*T)); E is converted from J/kmol to J/mol.
# These are reference-case parameters, not universal coal constants.
# ---------------------------------------------------------------------------
CHAR_REACTIONS = {
    "C_O2": {
        "A": 1.298e-3,
        "E": 1.324e8 / 1000.0,   # J/mol
        "beta": 1.233,
        "oxidiser": "O2",
        "dH_J_per_mol_C": -110525.0,   # C + 1/2 O2 -> CO
        "stoich_ox_per_C": 0.5,
        "products": {"CO": 1.0},
    },
    "C_CO2": {
        "A": 0.066,
        "E": 1.385e8 / 1000.0,
        "beta": -0.263,
        "oxidiser": "CO2",
        "dH_J_per_mol_C": +172459.0,   # Boudouard, endothermic
        "stoich_ox_per_C": 1.0,
        "products": {"CO": 2.0},
    },
    "C_H2O": {
        "A": 1.877e-3,
        "E": 1.588e8 / 1000.0,
        "beta": -0.124,
        "oxidiser": "H2O",
        "dH_J_per_mol_C": +131293.0,   # steam gasification, endothermic
        "stoich_ox_per_C": 1.0,
        "products": {"CO": 1.0, "H2": 1.0},
    },
}

C_DIFFUSION = 5.0e-12  # Mularski & Modlinski (2021), Equation (3), C_i.


def diffusion_coefficient(Tg: float, Tp: float, dp: float) -> float:
    """k_d — the diffusion rate coefficient [kg/(m2 s Pa)]."""
    T_film = 0.5 * (Tg + Tp)
    return C_DIFFUSION * (T_film ** 0.75) / max(dp, 1e-9)


def kinetic_coefficient(reaction: str, Tp: float) -> float:
    """k_s — the surface kinetic rate coefficient [kg/(m2 s Pa)]."""
    rx = CHAR_REACTIONS[reaction]
    Tp = max(Tp, 300.0)
    return rx["A"] * (Tp ** rx["beta"]) * math.exp(-rx["E"] / (R * Tp))


def char_reaction_rate(reaction: str, Tg: float, Tp: float, dp: float,
                       p_ox: float, area_m2: float) -> float:
    """Carbon consumption rate for one reaction [kg C /s].

    Parameters
    ----------
    p_ox : partial pressure of the oxidising species [Pa]
    area_m2 : total external particle surface area available [m2]

    NOTE(shrinking particle): we hold the external area fixed as the particle
    burns. Real particles shrink, and their internal pore area changes too.
    TODO(char-area): implement a shrinking-core or constant-density model and
    show the difference. Cheap to do, easy to defend, good report material.
    """
    if p_ox <= 0.0 or area_m2 <= 0.0:
        return 0.0
    k_d = diffusion_coefficient(Tg, Tp, dp)
    k_s = kinetic_coefficient(reaction, Tp)
    k_eff = (k_d * k_s) / (k_d + k_s + 1e-30)
    return k_eff * area_m2 * p_ox


def limiting_regime(reaction: str, Tg: float, Tp: float, dp: float) -> str:
    """Diagnostic: is this reaction kinetically or diffusion limited here?

    Use it to colour your axial plots. Showing where the transition happens
    along the reactor is a genuinely good figure and almost nobody does it.
    """
    k_d = diffusion_coefficient(Tg, Tp, dp)
    k_s = kinetic_coefficient(reaction, Tp)
    if k_s < 0.1 * k_d:
        return "kinetic"
    if k_d < 0.1 * k_s:
        return "diffusion"
    return "mixed"
