# Numerical methods used in Batch 18

This guide describes the implemented calculations. The solver is deliberately
reduced, so do not describe it as a full CFD solution.

## Tier 1: axial plug-flow calculation

Tier 1 represents the reactor with one cross-section and solves the chemistry
downstream. The state contains gas molar flows, char, raw coal, and enthalpy.
The model uses the chemistry modules in `src/gasifier/` and an adaptive
ODE solver. Temperature is recovered from the state enthalpy and composition
rather than advanced as an independent reaction-temperature equation.

Tier 1 is used for chemistry diagnostics and the particle-size sweep. The
current chemistry reaches 100% carbon conversion for all particle-size cases,
so those results cannot establish the physical size sensitivity.

## Tier 2: radial annuli marched downstream

`src/gasifier/reactor_2d.py` divides the reactor into concentric annular cells
and axial stations. The inlet distribution uses the published nozzle sizes
and an assumed background mixing fraction. Each annulus has its own local
chemistry calculation. Species and enthalpy are exchanged between neighboring
annuli using an implicit radial-diffusion step; the radial banded systems are
solved with `scipy.linalg.solve_banded`. Chemistry is coupled through
operator-split downstream steps.

This method is practical for producing approximate fields and conserved
inter-annular exchanges. It omits momentum transport, pressure coupling,
particle trajectories, radiation, and recirculation. The near-axis profile is
sampled at the first annulus center, r = 0.00083 m.

## Numerical checks and their limits

The four-grid study uses 20x100, 40x200, 80x400, and 120x600 radial-by-axial
stations. Refinement from 80x400 to 120x600 changes the outlet mean
temperature by about 9.1 K, carbon conversion by about 1.28 percentage
points, and the main dry-gas species by about 0.65-0.80 percentage points.
The peak reaches the 4000 K recovery ceiling on every grid, so peak-temperature
convergence is not demonstrated.

Tracked C/H/O/N/Ar balances close to approximately 0.0000021% on the finest
grid. This checks conservation in the implementation; it does not demonstrate
physical accuracy. The outlet conversion and axial profiles still differ
substantially from experiment.

## Validation workflow

1. Run `python scripts/run_tier2.py` to generate the model profiles.
2. Run `python scripts/make_validation_plots.py` to compare the near-axis
   profiles with digitized Figure 9 experimental centerline markers.
3. Run `python scripts/digitize_radial_markers.py` and then
   `python scripts/make_radial_validation_plots.py` to compare radial model
   profiles with the digitized experimental probes at eight axial stations.
4. Review `report/validation_errors.csv`,
   `report/validation_radial_errors.csv`, and
   `report/fig_validation_axial_centerline.png`.

The errors are absolute mole-fraction differences reported in percentage
points. Figure 9 and Figures 12-14 points are approximate digitizations, not
exact raw data. A pure-diffusion analytical step test remains open work; do
not describe it as completed verification.
