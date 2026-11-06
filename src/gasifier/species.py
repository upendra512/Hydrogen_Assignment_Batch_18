"""
Species data and thermodynamics.

STATUS: working, but deliberately crude. See TODO(thermo).

WHAT THIS MODULE IS FOR
-----------------------
Everything downstream needs three things about each gas species:
its molar mass, its enthalpy of formation, and how its enthalpy varies
with temperature. That is all this file provides.

THE SIMPLIFICATION WE HAVE MADE
-------------------------------
We use a CONSTANT specific heat for each species:

    h_i(T) = hf298_i + cp_i * (T - 298.15)          [J/mol]

Real codes use NASA 7- or 9-coefficient polynomials, where cp itself is a
function of T. Over 300-3000 K a constant cp is wrong by roughly 10-20% at
the hot end, which will show up as an error in your peak flame temperature.

TODO(thermo) — a good week-3 upgrade, owned by the chemistry lead:
    Replace the `cp` column with NASA polynomials. Sources: the CHEMKIN
    thermodynamic database, Burcat's tables, or Cantera's `nasa_gas.yaml`.
    Then h_i(T) becomes the polynomial integral. When you do this, note the
    change in peak temperature in your report — it is a legitimate
    sensitivity result and costs you nothing to report.
"""
from __future__ import annotations

from dataclasses import dataclass

R_UNIVERSAL = 8.314462618  # J/(mol K)
T_REF = 298.15  # K


@dataclass(frozen=True)
class Species:
    name: str
    mw: float  # kg/mol
    hf298: float  # J/mol, enthalpy of formation at 298.15 K, 1 atm
    cp: float  # J/(mol K), CONSTANT — see TODO(thermo)
    atoms: dict  # element -> count, used for the element balance


# ---------------------------------------------------------------------------
# Gas-phase species carried by the model.
#
# Ar is inert but must be carried: it is 16.77 mol% of the primary stream and
# it dilutes everything. Dropping it is a classic way to get the wrong
# temperature.
#
# TODO(chemistry): the paper models tar explicitly as a CxHyOz molecule with a
# C7 backbone. We lump tar into CH4 (see devolatilization.volatile_split).
# If you have time in week 5, add a TAR species here with a C7 formula and a
# cracking reaction TAR -> CO + H2 + CH4. That is a genuine model improvement
# and a good thing to show a sensitivity for.
# ---------------------------------------------------------------------------
SPECIES = {
    "O2":  Species("O2",  0.031998,       0.0, 34.0, {"O": 2}),
    "N2":  Species("N2",  0.028014,       0.0, 32.0, {"N": 2}),
    "Ar":  Species("Ar",  0.039948,       0.0, 20.8, {"Ar": 1}),
    "H2":  Species("H2",  0.0020159,      0.0, 30.0, {"H": 2}),
    "H2O": Species("H2O", 0.0180153, -241826.0, 43.0, {"H": 2, "O": 1}),
    "CO":  Species("CO",  0.0280101, -110525.0, 33.0, {"C": 1, "O": 1}),
    "CO2": Species("CO2", 0.0440095, -393522.0, 52.0, {"C": 1, "O": 2}),
    "CH4": Species("CH4", 0.0160425,  -74873.0, 60.0, {"C": 1, "H": 4}),
}

GAS_SPECIES = list(SPECIES.keys())
N_GAS = len(GAS_SPECIES)
IDX = {name: i for i, name in enumerate(GAS_SPECIES)}

# Solid phase. Char is treated as pure carbon (graphite): hf = 0 by definition.
# TODO(chemistry): real char retains H, N and S. The paper's ultimate analysis
# lets you build a CH_xO_y char instead. Worth one paragraph in the report
# explaining why we neglected it and what it would change.
CHAR_MW = 0.012011  # kg/mol, as carbon
CP_CHAR = 21.0      # J/(mol K)
CP_ASH = 900.0      # J/(kg K)


def h_species(name: str, T: float) -> float:
    """Molar enthalpy [J/mol] of a gas species at temperature T [K]."""
    s = SPECIES[name]
    return s.hf298 + s.cp * (T - T_REF)


def h_gas_mixture(n: dict, T: float) -> float:
    """Total enthalpy [J/s] of a gas stream given molar flows n [mol/s]."""
    return sum(n_i * h_species(name, T) for name, n_i in n.items() if n_i > 0.0)


def mixture_mw(x: dict) -> float:
    """Mixture molar mass [kg/mol] from mole fractions x."""
    return sum(x[name] * SPECIES[name].mw for name in x)


def gas_density(p: float, T: float, mw: float) -> float:
    """Ideal-gas density [kg/m3].

    Justified here: at 1 atm and >400 K, hydrogen and the rest are close to
    ideal. Your Properties of Hydrogen deck makes the same point. If you ever
    move to a pressurised case (the MHI fallback), revisit this.
    """
    return p * mw / (R_UNIVERSAL * T)


def element_flows(n: dict, char_mol_s: float = 0.0) -> dict:
    """Atomic flow rates [mol/s] of C, H, O, N, Ar in a stream.

    Used by postprocess.element_balance to prove your solution conserves
    atoms. RUN THIS EVERY TIME. A model that loses carbon is not a model.
    """
    out = {"C": 0.0, "H": 0.0, "O": 0.0, "N": 0.0, "Ar": 0.0}
    for name, n_i in n.items():
        for el, count in SPECIES[name].atoms.items():
            out[el] += n_i * count
    out["C"] += char_mol_s
    return out
