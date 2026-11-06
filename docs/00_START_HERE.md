# Batch 18: start here

This project models the BYU atmospheric entrained-flow gasifier case using
Utah bituminous coal. The selected reference is Mularski and Modlinski (2021),
and the measured gasifier results come from Brown et al. (1988). The assignment
asks for feed composition, species profiles and contours, temperature,
comparison with the reference, conclusions, source code, and a presentation.

## The project in one minute

Coal is heated and partly oxidized with oxygen and steam. The model estimates
how that chemistry changes gas composition and temperature along the reactor.
The full reference study uses more detailed process and CFD models. This
project uses Tier 1 plug flow for chemistry diagnostics and Tier 2 annular
stream tubes with radial mixing for approximate reactor fields. Tier 2 is a
reduced model; it does not solve momentum or track particle trajectories.

The validation comparison finds large differences from the experiment. That
is a project result to discuss and explain, not a reason to present the model
as validated.

## Reproduce the deliverables

From the `Batch18` directory, use:

```bash
python scripts/run_tier1.py
python scripts/run_tier2.py
python scripts/run_grid_study.py
python scripts/sweep_particle_size.py
python scripts/digitize_radial_markers.py
python scripts/make_validation_plots.py
python scripts/make_radial_validation_plots.py
python scripts/make_submission_pdfs.py
python scripts/package_source.py
```

The main inputs are in `case/byu_case.yaml`. Results and figures are written
under `report/`; the PDFs are written to `report/` and `presentation/`.

## Where to look

| Need | File |
|---|---|
| Assignment requirements and current completion status | `../Batch18_project_plan.html` and `../Batch18/checklists/rubric_checklist.md` |
| Case inputs and assumptions | `case/byu_case.yaml`, `docs/04_validation_protocol.md` |
| Simple physics explanation | `docs/01_theory_primer.md` |
| Numerical method actually implemented | `docs/02_numerics_guide.md` |
| Code walkthrough | `docs/03_coding_walkthrough.md` |
| Results and known limitations | `README.md` and the report PDF |
| Presentation order and viva questions | `presentation/slide_outline.md` |
| Remaining external actions | `checklists/weekly_gates.md`, `admin/instructor_followup.md` |

## Main findings to explain

- The finest Tier 2 run closes tracked element balances to about 0.0000021%.
- The model predicts 53.52% carbon conversion, compared with 82% measured.
- Near-axis mean absolute errors against digitized centerline data are 12.81
  percentage points for CO, 10.50 for H2, and 7.27 for CO2.
- Across eight radial probe stations, mean absolute errors are 8.54 pp for CO,
  7.02 for H2, and 6.74 for CO2. The source figures and digitization method
  are included so these approximate values can be checked.
- Every grid reaches the 4000 K temperature-recovery ceiling, so the peak is
  unresolved. The model also leaves 3.88 vol% dry oxygen at the outlet.
- The Tier 1 particle-size sweep saturates at 100% conversion and therefore
  does not establish a physical particle-size effect.

The report identifies these discrepancies and the model's reduced scope. Use
the presentation outline to divide the explanation across all five members.
