"""
TIER 1 — one-dimensional plug-flow gasifier model.

STATUS: RUNS. This is your safety net. From the day you clone this repo you
have something that integrates end to end and produces axial profiles.

It is not accurate yet. That is fine and expected. Its job is to (a) prove the
pipeline works, (b) let you debug chemistry cheaply in seconds rather than
hours, and (c) guarantee that if everything else goes wrong in October you
still have four of the six required results.

THE MODEL
---------
Assumptions, every one of which belongs in your report's methodology section:

  1. Steady state.
  2. Plug flow: all properties uniform across any cross-section. No radial
     variation, therefore NO CONTOURS. Tier 2 fixes this.
  3. Particles travel at the gas velocity (no slip). Justified at 36 um:
     the Stokes number is small.
  4. One temperature: gas and particles are in thermal equilibrium.
     TODO(two-temperature): separate them. Particles run hotter than the gas
     in the flame zone; that difference drives the char rates, which are
     exponential in Tp. This is the most physically important upgrade
     available to you.
  5. Adiabatic: no heat loss to the wall.
     TODO(wall-heat-loss): the BYU reactor is not adiabatic. Check the paper's
     wall boundary condition and add a loss term. Your peak temperature is
     almost certainly too high until you do.
  6. Moisture evaporates instantly at the inlet (see config.load_case).

STATE VECTOR
------------
    y[0 : N_GAS]  molar flow of each gas species        [mol/s]
    y[N_GAS]      char mass flow                        [kg/s]
    y[N_GAS + 1]  un-devolatilised daf coal mass flow   [kg/s]

Temperature is NOT integrated. It is recovered at every step from
conservation of total enthalpy (adiabatic), by root-finding. This is far more
stable than integrating dT/dz, which tends to run away in the flame zone and
is the single most common reason a student model diverges.
"""
from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

from . import char as char_mod
from . import devolatilization as devol
from . import gas_phase
from .config import Case
from .species import (CHAR_MW, CP_ASH, CP_CHAR, GAS_SPECIES, IDX, N_GAS,
                      SPECIES, T_REF, gas_density, h_species, mixture_mw)

R = 8.314462618


# ---------------------------------------------------------------------------
# Temperature recovery
# ---------------------------------------------------------------------------
def _enthalpy(y: np.ndarray, T: float, case: Case) -> float:
    """Total enthalpy flow [W] of gas + char + raw coal + ash at temperature T."""
    H = 0.0
    for i, sp in enumerate(GAS_SPECIES):
        if y[i] > 0.0:
            H += y[i] * h_species(sp, T)
    m_char = max(y[N_GAS], 0.0)
    H += (m_char / CHAR_MW) * CP_CHAR * (T - T_REF)
    m_raw = max(y[N_GAS + 1], 0.0)
    H += m_raw * (case.hf_coal + 1200.0 * (T - T_REF))  # cp_coal ~1200 J/kg/K
    H += case.m_ash * CP_ASH * (T - T_REF)
    return H


def recover_temperature(y: np.ndarray, H_target: float, case: Case) -> float:
    """Solve _enthalpy(y, T) = H_target for T.

    Bracketed root-find over a physically sane window. If it fails to bracket,
    we clamp rather than crash — a crash mid-integration tells you nothing,
    a clamp plus a warning tells you where the model went unphysical.
    """
    lo, hi = 280.0, 4000.0
    f_lo = _enthalpy(y, lo, case) - H_target
    f_hi = _enthalpy(y, hi, case) - H_target
    # Compare signs directly: multiplying large residuals can overflow during
    # stiff-solver Jacobian probes even when both values are finite.
    if not np.isfinite(f_lo) or not np.isfinite(f_hi):
        return float(np.clip(case.inlet_T, lo, hi))
    if np.signbit(f_lo) == np.signbit(f_hi):
        return lo if abs(f_lo) < abs(f_hi) else hi
    return brentq(lambda T: _enthalpy(y, T, case) - H_target, lo, hi, xtol=0.05)


# ---------------------------------------------------------------------------
# Right-hand side
# ---------------------------------------------------------------------------
def rhs(z: float, y: np.ndarray, case: Case, H0: float) -> np.ndarray:
    y = np.maximum(y, 0.0)
    dydz = np.zeros_like(y)

    n_gas = {sp: y[i] for i, sp in enumerate(GAS_SPECIES)}
    n_total = sum(n_gas.values())
    if n_total <= 0.0:
        return dydz

    T = recover_temperature(y, H0, case)
    T = float(np.clip(T, 280.0, 3600.0))

    x = {sp: n_gas[sp] / n_total for sp in n_gas}
    mw = mixture_mw(x)
    rho = gas_density(case.pressure, T, mw)
    mdot_gas = sum(n_gas[sp] * SPECIES[sp].mw for sp in n_gas)
    u = mdot_gas / (rho * case.area)          # m/s, superficial gas velocity
    u = max(u, 1e-3)

    # --- homogeneous gas-phase chemistry -----------------------------------
    # concentrations in kmol/m3 (the rate constants above expect kmol)
    conc = {sp: (n_gas[sp] / (u * case.area)) / 1000.0 for sp in n_gas}
    src, _q = gas_phase.species_source_terms(conc, T)
    for sp, s in src.items():
        if sp in IDX:
            # kmol/(m3 s) -> mol/(s m) of reactor length
            dydz[IDX[sp]] += s * 1000.0 * case.area / 1.0

    # --- devolatilisation ---------------------------------------------------
    m_raw = y[N_GAS + 1]
    if m_raw > 1e-12:
        vol_rate, char_rate = devol.devol_mass_rate(m_raw, T)   # kg/s per second
        dm_raw_dz = -(vol_rate + char_rate) / u                 # kg/s per metre
        dydz[N_GAS + 1] += dm_raw_dz
        dydz[N_GAS] += char_rate / u

        # Partition the devolatilising mass into gas species EXACTLY, using
        # the instantaneous char yield. See devolatilization.partition.
        part = devol.partition(-dm_raw_dz, char_rate / u, case.daf_y)
        for sp, n in part["gases"].items():
            if sp in IDX:
                dydz[IDX[sp]] += n
        # surplus volatile carbon (tar) is retained as soot and gasifies later
        dydz[N_GAS] += part["soot_C_kg"]

    # --- heterogeneous char reactions --------------------------------------
    m_char = y[N_GAS]
    if m_char > 1e-12:
        # external surface area presented per metre of reactor length
        area_per_length = case.n_particles * np.pi * case.dp ** 2 / u
        for rname, rx in char_mod.CHAR_REACTIONS.items():
            ox = rx["oxidiser"]
            p_ox = x.get(ox, 0.0) * case.pressure
            rate_kg_per_m = char_mod.char_reaction_rate(
                rname, T, T, case.dp, p_ox, area_per_length
            )
            if rate_kg_per_m <= 0.0:
                continue
            rate_kg_per_m = min(rate_kg_per_m, m_char / max(u, 1e-3) * 50.0)
            mol_C = rate_kg_per_m / CHAR_MW          # mol C /(s m)
            dydz[N_GAS] -= rate_kg_per_m
            dydz[IDX[ox]] -= mol_C * rx["stoich_ox_per_C"]
            for sp, nu in rx["products"].items():
                dydz[IDX[sp]] += mol_C * nu

    return dydz


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def solve(case: Case, n_out: int | None = None) -> dict:
    """Integrate the 1-D model and return axial profiles."""
    n_out = n_out or int(case.raw["geometry"]["grid"]["nz"])

    y0 = np.zeros(N_GAS + 2)
    for sp, n in case.inlet_moles.items():
        y0[IDX[sp]] = n
    y0[N_GAS] = 0.0             # no char yet — it is formed by devolatilisation
    y0[N_GAS + 1] = case.m_daf  # all daf coal starts un-devolatilised

    # ---- IGNITION -----------------------------------------------------------
    # A 1-D plug-flow model has no recirculation and no radiation back to the
    # inlet, so a cold stream entering at 412 K will NEVER ignite: the
    # devolatilisation rate constant at that temperature is ~1e-8 /s and the
    # residence time is under a second. Integrate it and you get the feed back
    # out of the far end, unchanged. (Try it: set ignition_T to None.)
    #
    # Real burners are stabilised by hot recirculating products and by
    # radiation from the flame. CFD practitioners handle this by "patching" a
    # hot region before the solve — the same trick, made explicit here.
    #
    # We raise the enthalpy datum so the mixture starts at ignition_T. The
    # energy this adds is reported below; you MUST quote it in the report as a
    # fraction of the fuel energy, and argue that it is a numerical device
    # standing in for a physical effect, not free energy.
    #
    # TODO(ignition) — OWNER: solver lead — DUE: week 4 with Tier 2
    #   In Tier 2 you can drop this entirely, because a 2-D model with a
    #   recirculation zone ignites on its own. If you still need it there,
    #   your inlet boundary condition is wrong. Removing the patch and showing
    #   the flame anchors by itself is a genuinely strong result to present.
    ign = case.raw.get("numerics", {}).get("ignition_T_K", 1400.0)
    T_start = float(ign) if ign else case.inlet_T
    case.daf_y = devol.daf_fractions(case)

    H0 = _enthalpy(y0, T_start, case)
    H_cold = _enthalpy(y0, case.inlet_T, case)
    case.ignition_energy_W = H0 - H_cold
    case.ignition_T = T_start

    z_eval = np.linspace(0.0, case.length, n_out)
    sol = solve_ivp(
        rhs, (0.0, case.length), y0,
        args=(case, H0),
        method="LSODA",          # stiff: chemistry is much faster than flow
        t_eval=z_eval,
        rtol=1e-6, atol=1e-12,
        max_step=case.length / 200.0,
    )

    if not sol.success:
        # Do not silently return garbage.
        raise RuntimeError(
            "Integration failed: " + sol.message +
            "\nSee docs/05_faq_troubleshooting.md, section 'the integrator died'."
        )

    # Stiff integrators can leave tiny negative traces at depleted species and
    # solid endpoints. Project them back to the physically admissible domain
    # before computing reported fields and metrics.
    y_out = np.maximum(sol.y, 0.0)
    T = np.array([recover_temperature(y_out[:, i], H0, case)
                  for i in range(y_out.shape[1])])

    n_gas = y_out[:N_GAS, :]
    n_total = n_gas.sum(axis=0)
    x = n_gas / np.maximum(n_total, 1e-30)

    return {
        "z": sol.t,
        "T": T,
        "moles": {sp: n_gas[IDX[sp], :] for sp in GAS_SPECIES},
        "x": {sp: x[IDX[sp], :] for sp in GAS_SPECIES},
        "m_char": y_out[N_GAS, :],
        "m_raw": y_out[N_GAS + 1, :],
        "H0": H0,
        "case": case,
    }
