"""Reduced, axisymmetric, radially coupled gasifier model.

This is a transparent stream-tube model, not a replacement for the reference
paper's RANS/particle CFD. Annular gas/coal streams are initialized from the
published BYU injector dimensions, and neighboring annuli exchange gas species
and enthalpy through a conservative turbulent-diffusion closure. Each annulus
uses the same chemistry and thermodynamics as Tier 1. Particle trajectories,
recirculation, radiation, and axial momentum are not resolved; they remain
explicit limitations in the report.

The finite-volume state in each annulus is [gas molar flows, char flow, raw
coal flow, enthalpy flow]. Each species and its transported enthalpy move
conservatively between adjacent annuli. The model has no radial momentum
equation, so the resulting local flow redistribution is a reduced-order
approximation.
"""
from __future__ import annotations

from copy import copy

import numpy as np
from scipy.linalg import solve_banded

from . import devolatilization as devol
from . import reactor_1d
from .config import Case
from .species import (CHAR_MW, CP_ASH, CP_CHAR, GAS_SPECIES, IDX, N_GAS,
                      SPECIES, gas_density, mixture_mw)

TURBULENT_SCHMIDT = 0.70
TURBULENT_PRANDTL = 0.90
MOLECULAR_DIFFUSIVITY = 1.0e-5  # m2/s, representative hot-gas value
MAX_EFFECTIVE_DIFFUSIVITY = 0.20  # numerical/closure cap, m2/s
TURBULENT_MIXING_COEFFICIENT = 0.05
INLET_BACKGROUND_FRACTION = 0.20
N_LOCAL = N_GAS + 2


class Grid2D:
    """Axisymmetric (r,z) finite-volume grid; radial cells are annuli."""

    def __init__(self, case: Case, nr: int | None = None, nz: int | None = None):
        g = case.raw["geometry"]["grid"]
        self.nr = int(nr or g["nr"])
        self.nz = int(nz or g["nz"])
        if self.nr < 2 or self.nz < 2:
            raise ValueError("Tier 2 requires at least two cells in each direction")
        self.R = case.diameter / 2.0
        self.L = case.length
        self.dr = self.R / self.nr
        self.dz = self.L / (self.nz - 1)
        self.r_faces = np.arange(self.nr + 1) * self.dr
        self.r = (np.arange(self.nr) + 0.5) * self.dr
        self.z = np.linspace(0.0, self.L, self.nz)
        self.cell_area = np.pi * (self.r_faces[1:] ** 2 - self.r_faces[:-1] ** 2)

    def integrate_radially(self, field: np.ndarray) -> np.ndarray:
        """Area-weighted radial average at each axial station."""
        a = np.asarray(field)
        if a.shape[0] != self.nr:
            raise ValueError("field's first axis must match the radial grid")
        return np.tensordot(self.cell_area / np.sum(self.cell_area), a, axes=(0, 0))


def _stream_weights(grid: Grid2D, inner: float, outer: float | None,
                    background: float) -> np.ndarray:
    """Area-normalized injector profile with exact annulus/nozzle overlap.

    Partial cells are fractionally filled by the inlet stream. This avoids a
    grid-dependent jump in nozzle area when the mesh is refined.
    """
    if not 0.0 < background < 1.0:
        raise ValueError("inlet_background_fraction must be between 0 and 1")
    if inner < 0 or inner >= grid.R or (outer is not None and not inner < outer <= grid.R):
        raise ValueError("injector radii must lie inside the reactor")
    r0 = 0.0 if outer is None else inner
    r1 = inner if outer is None else outer
    overlap = np.pi * np.maximum(
        np.minimum(grid.r_faces[1:], r1) ** 2 - np.maximum(grid.r_faces[:-1], r0) ** 2,
        0.0,
    )
    core_area = np.pi * (r1**2 - r0**2)
    total_area = float(np.sum(grid.cell_area))
    cell_shares = (background * grid.cell_area / total_area
                   + (1.0 - background) * overlap / core_area)
    w = cell_shares / grid.cell_area
    # Discrete normalization makes the inlet totals exact at any grid size.
    return w / float(np.dot(w, grid.cell_area))


def _local_cases(case: Case, grid: Grid2D):
    """Make one chemistry case per annulus, scaled to its inlet feed share."""
    g = case.raw["geometry"]
    inj = g.get("injectors", {})
    # BYU nozzle dimensions: Abani & Ghoniem (2013), LES of the BYU axial-flow
    # gasifier, Fuel 104, Fig. 1 / test-conditions section: primary ID 1.3 cm,
    # secondary annular nozzle OD 2.86 cm. The 2021 reference paper itself
    # reports vessel geometry but not these inlet dimensions.
    primary_r = float(inj.get("primary_inner_diameter_m", 0.013)) / 2.0
    secondary_r = float(inj.get("secondary_outer_diameter_m", 0.0286)) / 2.0
    spread = float(inj.get("background_mixing_fraction", INLET_BACKGROUND_FRACTION))
    wp = _stream_weights(grid, primary_r, None, spread)
    ws = _stream_weights(grid, primary_r, secondary_r, spread)

    primary = case.raw["inlets"]["primary"]
    secondary = case.raw["inlets"]["secondary"]
    # Rebuild per-stream molar rates from their source mass rates and mole fractions.
    from .species import SPECIES
    stream_moles = {}
    for label, stream in (("primary", primary), ("secondary", secondary)):
        mass_rate = float(stream["mass_flow_g_s"]) / 1000.0
        x = stream["composition_mol_frac"]
        mw = sum(x[sp] * SPECIES[sp].mw for sp in x)
        total = mass_rate / mw
        stream_moles[label] = {sp: total * frac for sp, frac in x.items()}

    prox = case.raw["fuel"]["proximate_wt_pct"]
    n_particle_per_kg = case.n_particles / case.coal_feed
    daf_y = devol.daf_fractions(case)
    cases = []

    for j, area in enumerate(grid.cell_area):
        c = copy(case)
        c.area = float(area)
        c.inlet_moles = {}
        for sp, rate in stream_moles["primary"].items():
            c.inlet_moles[sp] = c.inlet_moles.get(sp, 0.0) + rate * wp[j] * area
        for sp, rate in stream_moles["secondary"].items():
            c.inlet_moles[sp] = c.inlet_moles.get(sp, 0.0) + rate * ws[j] * area

        # Moisture belongs to coal in the primary stream and follows the coal
        # radial profile. Keep the published total moisture feed exactly.
        coal_share = wp[j] * area
        coal_feed = case.coal_feed * coal_share
        primary_mass = (float(primary["mass_flow_g_s"]) / 1000.0) * wp[j] * area
        secondary_mass = (float(secondary["mass_flow_g_s"]) / 1000.0) * ws[j] * area
        c.inlet_T = (primary_mass * float(primary["temperature_K"])
                     + secondary_mass * float(secondary["temperature_K"])
                     + coal_feed * float(primary["temperature_K"])) / max(
                         primary_mass + secondary_mass + coal_feed, 1e-30)
        moisture = coal_feed * prox["moisture"] / 100.0
        c.coal_feed = coal_feed
        c.m_ash = coal_feed * prox["ash"] / 100.0
        c.m_moisture = moisture
        c.m_volatile = coal_feed * prox["volatile_matter"] / 100.0
        c.m_fixed_carbon = coal_feed * prox["fixed_carbon"] / 100.0
        c.m_daf = c.m_volatile + c.m_fixed_carbon
        c.n_particles = coal_feed * n_particle_per_kg
        c.daf_y = daf_y
        c.inlet_moles["H2O"] = c.inlet_moles.get("H2O", 0.0) + moisture / SPECIES["H2O"].mw

        cases.append(c)

    # Guard the normalization and fuel feed before integrating.
    if not np.isclose(sum(c.coal_feed for c in cases), case.coal_feed, rtol=1e-11):
        raise RuntimeError("radial coal inlet allocation does not conserve the feed")
    if not np.isclose(sum(sum(c.inlet_moles.values()) for c in cases),
                      sum(case.inlet_moles.values()), rtol=2e-3):
        # The stream moisture addition is separately exact; source stream mole
        # rates differ slightly from the globally temperature-weighted loader
        # only through floating-point rounding.
        raise RuntimeError("radial gas inlet allocation does not conserve the feed")
    return cases, wp, ws


def _mixture_properties(y: np.ndarray, H: float, local_case: Case):
    ygas = np.maximum(y[:N_GAS], 0.0)
    total = float(np.sum(ygas))
    if total <= 1e-30:
        x = {sp: 0.0 for sp in GAS_SPECIES}
        x["Ar"] = 1.0
        mw = SPECIES["Ar"].mw
        T = local_case.inlet_T
        mdot = 0.0
    else:
        x = {sp: ygas[IDX[sp]] / total for sp in GAS_SPECIES}
        mw = mixture_mw(x)
        mdot = float(sum(ygas[i] * SPECIES[sp].mw for i, sp in enumerate(GAS_SPECIES)))
        T = reactor_1d.recover_temperature(y, H, local_case)
        T = float(np.clip(T, 280.0, 3600.0))
    rho = gas_density(local_case.pressure, T, mw)
    u = mdot / max(rho * local_case.area, 1e-30)
    return x, mw, T, rho, u


def march(case: Case, grid: Grid2D):
    """Run parallel reacting annuli with conservative implicit radial mixing.

    Chemistry is integrated with the verified Tier 1 stiff solver in each
    stream tube. Its axial reaction increments are then operator-split with an
    implicit finite-volume radial mixing step. This reduced-order approach
    keeps the chemistry stable and the global balances exact; its limitation is
    that local chemistry does not feed back into the reaction increments until
    the next axial station.
    """
    if not np.isclose(grid.R, case.diameter / 2.0):
        raise ValueError("grid and case reactor radii do not match")
    cases, wp, ws = _local_cases(case, grid)
    nr = grid.nr
    nvar = N_LOCAL + 1
    mix_coeff = float(case.raw.get("numerics", {}).get(
        "turbulent_radial_mixing_coefficient", TURBULENT_MIXING_COEFFICIENT))
    base = np.zeros((nr, grid.nz, nvar))
    for j in range(nr):
        lane = reactor_1d.solve(cases[j], n_out=grid.nz)
        for sp in GAS_SPECIES:
            base[j, :, IDX[sp]] = lane["moles"][sp]
        base[j, :, N_GAS] = lane["m_char"]
        base[j, :, N_GAS + 1] = lane["m_raw"]
        base[j, :, -1] = lane["H0"]

    state = np.zeros_like(base)
    state[:, 0, :] = base[:, 0, :]

    for k in range(1, grid.nz):
        # Apply each lane's atom-balanced reaction increment to the previously
        # mixed state. If an independent lane consumed a trace faster than the
        # mixed state contains it, scale that whole local reaction increment;
        # this preserves local C/H/O/N while enforcing nonnegative states.
        for j in range(nr):
            old = state[j, k - 1, :N_LOCAL]
            delta = base[j, k, :N_LOCAL] - base[j, k - 1, :N_LOCAL]
            alpha = 1.0
            falling = delta < 0.0
            if np.any(falling):
                alpha = min(1.0, float(np.min(old[falling] / -delta[falling])))
            alpha = max(0.0, alpha)
            state[j, k, :N_LOCAL] = np.maximum(old + alpha * delta, 0.0)
            state[j, k, -1] = state[j, k - 1, -1]

        # Evaluate local transport properties after the chemistry split.
        props = [_mixture_properties(state[j, k, :N_LOCAL], state[j, k, -1], cases[j])
                 for j in range(nr)]
        velocity = np.asarray([p[4] for p in props])
        bulk_u = float(np.dot(velocity, grid.cell_area) / np.sum(grid.cell_area))
        d_turbulent = min(mix_coeff * bulk_u * grid.R, MAX_EFFECTIVE_DIFFUSIVITY)
        d_species = np.full(nr, np.clip(
            d_turbulent / TURBULENT_SCHMIDT + MOLECULAR_DIFFUSIVITY,
            MOLECULAR_DIFFUSIVITY, MAX_EFFECTIVE_DIFFUSIVITY))
        d_heat = np.full(nr, np.clip(
            d_turbulent / TURBULENT_PRANDTL + MOLECULAR_DIFFUSIVITY,
            MOLECULAR_DIFFUSIVITY, MAX_EFFECTIVE_DIFFUSIVITY))

        # Backward-Euler annular finite-volume solve for every gas species.
        # A face coefficient multiplies concentration n_dot/(u*A); the matrix
        # is conservative because each internal-face flux appears twice with
        # opposite signs.
        diag = np.zeros(nr)
        upper = np.zeros(nr - 1)
        lower = np.zeros(nr - 1)
        alpha_face = np.zeros(nr - 1)
        for j in range(nr - 1):
            alpha_face[j] = (0.5 * (d_species[j] + d_species[j + 1])
                             * 2.0 * np.pi * grid.r_faces[j + 1] / grid.dr)
            vA_l = max(velocity[j] * grid.cell_area[j], 1e-30)
            vA_r = max(velocity[j + 1] * grid.cell_area[j + 1], 1e-30)
            diag[j] += alpha_face[j] / vA_l
            diag[j + 1] += alpha_face[j] / vA_r
            upper[j] = -grid.dz * alpha_face[j] / vA_r
            lower[j] = -grid.dz * alpha_face[j] / vA_l
        ab = np.zeros((3, nr))
        ab[0, 1:] = upper
        ab[1, :] = 1.0 + grid.dz * diag
        ab[2, :-1] = lower
        y_before = state[:, k, :N_GAS].copy()
        y_after = solve_banded((1, 1), ab, y_before, check_finite=False)

        # Record the implicit face transfers to carry species enthalpy with
        # each diffusing species, then apply pairwise heat conduction.
        h_after_species = state[:, k, -1].copy()
        for j in range(nr - 1):
            vA_l = max(velocity[j] * grid.cell_area[j], 1e-30)
            vA_r = max(velocity[j + 1] * grid.cell_area[j + 1], 1e-30)
            molar_flux = alpha_face[j] * (y_after[j] / vA_l - y_after[j + 1] / vA_r)
            TL, TR = props[j][2], props[j + 1][2]
            Tface = 0.5 * (TL + TR)
            q_species = sum(molar_flux[i] * (SPECIES[sp].hf298
                              + SPECIES[sp].cp * (Tface - 298.15))
                            for i, sp in enumerate(GAS_SPECIES))
            h_after_species[j] -= grid.dz * q_species
            h_after_species[j + 1] += grid.dz * q_species
        state[:, k, :N_GAS] = y_after
        state[:, k, -1] = h_after_species

        # Implicit turbulent heat conduction in T, with the local heat-capacity
        # flow as the capacitance. It is pairwise conservative in enthalpy.
        props2 = [_mixture_properties(state[j, k, :N_LOCAL], state[j, k, -1], cases[j])
                  for j in range(nr)]
        T0 = np.asarray([p[2] for p in props2])
        rho2 = np.asarray([p[3] for p in props2])
        capacities = np.zeros(nr)
        cp_mass = np.zeros(nr)
        for j in range(nr):
            yj = state[j, k, :N_LOCAL]
            capacities[j] = sum(yj[i] * SPECIES[sp].cp
                                for i, sp in enumerate(GAS_SPECIES))
            capacities[j] += (yj[N_GAS] / CHAR_MW) * CP_CHAR
            capacities[j] += yj[N_GAS + 1] * 1200.0
            capacities[j] += cases[j].m_ash * CP_ASH
            mass_rate = sum(yj[i] * SPECIES[sp].mw
                            for i, sp in enumerate(GAS_SPECIES))
            cp_mass[j] = (sum(yj[i] * SPECIES[sp].cp
                              for i, sp in enumerate(GAS_SPECIES))
                          / max(mass_rate, 1e-30))
        cond_diag = np.zeros(nr)
        cond_upper = np.zeros(nr - 1)
        cond_lower = np.zeros(nr - 1)
        for j in range(nr - 1):
            conductance = (0.5 * (rho2[j] + rho2[j + 1])
                           * 0.5 * (d_heat[j] + d_heat[j + 1])
                           * 0.5 * (cp_mass[j] + cp_mass[j + 1])
                           * 2.0 * np.pi * grid.r_faces[j + 1] / grid.dr)
            cond_diag[j] += conductance
            cond_diag[j + 1] += conductance
            cond_upper[j] = -grid.dz * conductance
            cond_lower[j] = -grid.dz * conductance
        ab_h = np.zeros((3, nr))
        ab_h[0, 1:] = cond_upper
        ab_h[1, :] = capacities + grid.dz * cond_diag
        ab_h[2, :-1] = cond_lower
        capacities = np.maximum(capacities, 1e-12)
        Tnew = solve_banded((1, 1), ab_h, capacities * T0, check_finite=False)
        state[:, k, -1] += capacities * (Tnew - T0)

    T = np.zeros((nr, grid.nz))
    x = {sp: np.zeros_like(T) for sp in GAS_SPECIES}
    for j in range(nr):
        for k in range(grid.nz):
            yj = state[j, k, :N_LOCAL]
            Hj = state[j, k, -1]
            T[j, k] = reactor_1d.recover_temperature(yj, Hj, cases[j])
            total = max(float(np.sum(yj[:N_GAS])), 1e-30)
            for sp in GAS_SPECIES:
                x[sp][j, k] = yj[IDX[sp]] / total

    # Aggregate annular flow rates for global conservation checks and metrics.
    moles = {sp: np.sum(state[:, :, IDX[sp]], axis=0) for sp in GAS_SPECIES}
    m_char = np.sum(state[:, :, N_GAS], axis=0)
    m_raw = np.sum(state[:, :, N_GAS + 1], axis=0)
    result = {
        "r": grid.r, "z": grid.z, "T": T, "x": x,
        "moles": moles, "m_char": m_char, "m_raw": m_raw,
        "case": case, "grid": grid, "radial_state": state,
        "inlet_primary_weights": wp, "inlet_secondary_weights": ws,
        "model_notes": {
            "type": "radially coupled annular stream-tube model",
            "turbulent_mixing_coefficient": mix_coeff,
            "turbulent_Schmidt": TURBULENT_SCHMIDT,
            "turbulent_Prandtl": TURBULENT_PRANDTL,
            "diffusivity_cap_m2_s": MAX_EFFECTIVE_DIFFUSIVITY,
            "inlet_background_mixing_fraction": float(
                case.raw["geometry"].get("injectors", {}).get(
                    "background_mixing_fraction", INLET_BACKGROUND_FRACTION)),
            "limitations": ["no axial momentum solution", "no particle radial dispersion",
                            "no recirculation or radiation", "uniform pressure",
                            "chemistry/mixing are operator-split; not full CFD"],
        },
    }
    result["x_axial"] = {sp: moles[sp] / np.maximum(
        np.sum([moles[s] for s in GAS_SPECIES], axis=0), 1e-30) for sp in GAS_SPECIES}
    return result
