# Coding walkthrough

This guide describes the current implementation in the order used to reproduce
the project. The original week-by-week starter schedule is obsolete; current
completion and submission status is in `../checklists/weekly_gates.md`.

## Inputs and case loading

- `case/byu_case.yaml` holds the BYU geometry, Utah coal analysis, feed rates,
  stream compositions, and grid size.
- `src/gasifier/config.py` reads the case and converts the input quantities to
  the SI quantities used by the solvers.
- `src/gasifier/species.py` defines the tracked gas species and molecular
  properties.

## Chemistry and Tier 1

- `devolatilization.py` converts the as-received coal description to the
  dry-ash-free fuel fractions and releases the volatile products.
- `gas_phase.py` applies the homogeneous gas reactions.
- `char.py` computes heterogeneous char reaction rates.
- `thermo.py` and `reactor_1d.py` provide mixture enthalpy, temperature
  recovery, and the axial plug-flow calculation.
- `scripts/run_tier1.py` runs the reduced axial calculation and writes the
  diagnostic species, temperature, and conversion plots.

Tier 1 is useful for chemistry and balance checks. It is not the reported
reactor-field model, and its particle-size sweep reaches complete burnout for
every tested case. That saturation makes the sweep a diagnostic of model
limits, not evidence of particle-size independence.

## Tier 2 transport and fields

`src/gasifier/reactor_2d.py` places annular cells on an axisymmetric radial
grid and marches them downstream. Injector overlap distributes the primary
and secondary feeds across the annuli. Each annulus uses Tier 1 chemistry;
neighboring annuli exchange species and enthalpy through a conservative radial
mixing closure. This reduced model has no momentum equation, particle
trajectories, radiation, or recirculation.

Run `python scripts/run_tier2.py` from the `Batch18` directory. The default is
120 radial by 600 axial stations. It writes contour plots and
`report/tier2_summary.csv`. Area-average values are integrated over annular
areas. `near_axis_*` values are sampled at the first annulus center (r =
0.00083 m); they are a near-axis proxy, not values at r = 0.

## Numerical and experimental comparisons

- `scripts/run_grid_study.py` compares 20x100, 40x200, 80x400, and 120x600
  grids. Small grid changes support numerical stability; they do not establish
  agreement with the experiment.
- `data/validation/fig09_axial_centerline.csv` contains approximate
  experimental markers digitized from Figure 9 of Mularski and Modlinski
  (2021), with provenance and uncertainty notes in the file.
- Run `python scripts/make_validation_plots.py` after Tier 2. It compares the
  near-axis model values with the digitized experimental centerline markers
  and writes an overlay plus `report/validation_errors.csv`. The large errors
  are reported as absolute composition differences in percentage points.
- `scripts/digitize_radial_markers.py` extracts the orange experimental markers
  from the attributed 360-dpi source pages for Figures 12-14. Tier 2 writes
  radial model profiles at those same eight axial stations;
  `scripts/make_radial_validation_plots.py` creates the probe overlays and
  `report/validation_radial_errors.csv`. H2O is excluded from the error score
  because the source paper derives it by hydrogen balance.
- `scripts/sweep_particle_size.py` performs the mass-weighted Tier 1
  Rosin-Rammler diagnostic. It cannot resolve a physical size effect while
  Tier 1 saturates at full conversion.

The model closes tracked element balances closely, but its outlet conversion,
hydrogen fraction, residual oxygen, and axial profile errors show that it does
not reproduce the measured gasifier behavior. See `04_validation_protocol.md`
for sources, comparison bases, and outstanding radial-profile work.

## Rebuild the deliverables

From the `Batch18` directory, run `python scripts/make_submission_pdfs.py` to
rebuild the report and 15-slide presentation, then run
`python scripts/package_source.py` to refresh `Batch18_source.zip`. The package
contains the code, inputs, data, report, presentation, and generated results.
