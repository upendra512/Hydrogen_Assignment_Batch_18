"""
Homogeneous gas-phase reactions.

STATUS: working. Four global reactions with literature rates.

THE PHYSICS
-----------
The volatiles and the CO leaving the char surface still have to burn and
shift. Four global reactions cover the chemistry that matters for syngas:

    G1  CO  + 1/2 O2 -> CO2                oxidation, very fast
    G2  H2  + 1/2 O2 -> H2O                oxidation, very fast
    G3  CO  + H2O   <-> CO2 + H2           WATER-GAS SHIFT — reversible
    G4  CH4 + H2O    -> CO + 3 H2          methane reforming

G3 is the one to care about. It is reversible, it is what finally sets your
H2:CO ratio, and it is the reaction your Class 2 and gasification decks both
spend time on. Everything else mostly decides how hot things get.

FINITE RATE vs MIXING
---------------------
In a turbulent flame the chemistry is usually faster than the mixing, so the
true rate is whichever is slower:

    rate = min( Arrhenius rate , eddy-dissipation rate )

The reference paper uses a global mechanism tuned for consistency with
GRI-Mech, inside an eddy-dissipation-concept framework.

For TIER 1 (1-D plug flow) there is no turbulence field, so we use the
Arrhenius rate alone. That is a real limitation: it will make your flame zone
too fast and too hot.

TODO(ed-model) — OWNER: solver lead — DUE: week 4, with Tier 2
    Once you have a 2-D field with a turbulent viscosity, add the
    eddy-dissipation limit:

        rate_ED = A_ED * rho * (eps/k) * min(Y_fuel/s_fuel, Y_ox/s_ox)

    with A_ED ~ 4.0. Then take the min of the two. Report the change in peak
    temperature — it will be large, and that is a result worth showing.
"""
from __future__ import annotations

import math

R = 8.314462618  # J/(mol K)
R_KCAL = 1.987e-3  # kcal/(mol K), for literature rates quoted in kcal


# ---------------------------------------------------------------------------
# Global reaction set.
#
# `A` and `E` follow the common Westbrook-Dryer style form
#     rate = A * exp(-E/RT) * [X1]^a * [X2]^b        [kmol/(m3 s)]
# with concentrations in kmol/m3.
#
# TODO(gas-rates) — OWNER: chemistry lead — DUE: week 3
#   Verify each of these against a citable source and put the citation in the
#   comment beside it. An examiner asking "where did this number come from?"
#   is the single most predictable question you will get in October.
# ---------------------------------------------------------------------------
REACTIONS = [
    {
        "name": "G1_CO_oxidation",
        "equation": "CO + 0.5 O2 -> CO2",
        "A": 2.239e12, "E": 1.7e5,          # J/mol
        "orders": {"CO": 1.0, "O2": 0.25, "H2O": 0.5},
        "stoich": {"CO": -1.0, "O2": -0.5, "CO2": +1.0},
        "dH": -282990.0,                     # J/mol of CO
        "reversible": False,
    },
    {
        "name": "G2_H2_oxidation",
        "equation": "H2 + 0.5 O2 -> H2O",
        "A": 1.0e14, "E": 1.7e5,
        "orders": {"H2": 1.0, "O2": 0.5},
        "stoich": {"H2": -1.0, "O2": -0.5, "H2O": +1.0},
        "dH": -241826.0,
        "reversible": False,
    },
    {
        "name": "G3_water_gas_shift",
        "equation": "CO + H2O <-> CO2 + H2",
        "A": 2.75e9, "E": 8.4e4,
        "orders": {"CO": 1.0, "H2O": 1.0},
        "stoich": {"CO": -1.0, "H2O": -1.0, "CO2": +1.0, "H2": +1.0},
        "dH": -41200.0,                      # matches your SMR tutorial: +41.2 kJ/mol released
        "reversible": True,
    },
    {
        "name": "G4_CH4_reforming",
        "equation": "CH4 + H2O -> CO + 3 H2",
        "A": 3.0e8, "E": 1.26e5,
        "orders": {"CH4": 1.0, "H2O": 1.0},
        "stoich": {"CH4": -1.0, "H2O": -1.0, "CO": +1.0, "H2": +3.0},
        "dH": +206000.0,
        "reversible": False,
    },
]


def wgs_equilibrium_constant(T: float) -> float:
    """Kp for CO + H2O <-> CO2 + H2.

    Standard correlation. Used to compute the reverse rate of G3 so the shift
    cannot run past equilibrium — which it will happily do if you forget.

    SANITY CHECK you can do by hand: Kp should be about 1 near 1100 K, large
    (favouring products) at low T, and below 1 above ~1200 K. If your model
    produces more H2 than equilibrium allows at 1500 K, this function is why.
    """
    return math.exp(4577.8 / max(T, 300.0) - 4.33)


def reaction_rates(concentrations: dict, T: float) -> list:
    """Net rate of each global reaction [kmol/(m3 s)].

    concentrations : species -> kmol/m3
    """
    rates = []
    for rx in REACTIONS:
        k = rx["A"] * math.exp(-rx["E"] / (R * max(T, 300.0)))
        rate = k
        for sp, order in rx["orders"].items():
            c = max(concentrations.get(sp, 0.0), 0.0)
            rate *= c ** order

        if rx["reversible"] and rx["name"] == "G3_water_gas_shift":
            Kp = wgs_equilibrium_constant(T)
            c_co = max(concentrations.get("CO", 0.0), 1e-30)
            c_h2o = max(concentrations.get("H2O", 0.0), 1e-30)
            c_co2 = max(concentrations.get("CO2", 0.0), 0.0)
            c_h2 = max(concentrations.get("H2", 0.0), 0.0)
            # net = forward * (1 - Q/Kp)
            Q = (c_co2 * c_h2) / (c_co * c_h2o)
            rate *= (1.0 - Q / Kp)

        rates.append(rate)
    return rates


def species_source_terms(concentrations: dict, T: float) -> tuple:
    """Return (dict of species -> kmol/(m3 s), heat release W/m3)."""
    rates = reaction_rates(concentrations, T)
    src = {}
    q = 0.0
    for rx, rate in zip(REACTIONS, rates):
        for sp, nu in rx["stoich"].items():
            src[sp] = src.get(sp, 0.0) + nu * rate
        # dH is per mol of the reaction's reference species; rate is kmol/m3/s
        q += -rx["dH"] * rate * 1000.0
    return src, q
