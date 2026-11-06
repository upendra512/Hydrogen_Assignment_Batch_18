# Batch 18 entrained-flow gasifier project

ME40249, Introduction to Hydrogen Energy and Utilization. Batch 18 uses the
BYU atmospheric entrained-flow Utah-coal case reported by Mularski and
Modlinski (2021), with its underlying experimental data from Brown et al.
(1988). The submission compares a reduced Python model with those published
results; it does not reproduce the reference CFD.

## Run the model

From this directory:

```bash
python -m pip install -r requirements.txt
jupyter notebook notebooks/Batch18_Full_Solver_Live_Demo.ipynb
python scripts/run_tier1.py
python scripts/run_tier2.py
python scripts/digitize_radial_markers.py
python scripts/make_validation_plots.py
python scripts/make_radial_validation_plots.py
python scripts/run_grid_study.py
python scripts/sweep_particle_size.py
python scripts/make_submission_pdfs.py
python scripts/package_source.py
```

The live-demo notebook is self-contained: it presents one solver through a
cross-section-averaged 1-D calculation and a radial 2-D calculation using the
same chemistry. These are two spatial descriptions within one workflow, not
separate project phases. It restates the BYU inputs, explains the equations,
compares results with digitized experiment markers, and includes viva prompts.
Run its cells from top to bottom. Increase `NR` and `NZ` in the radial-model
cell for finer contours.

Create its compatible kernel on a new setup with:

```bash
conda env create -f notebooks/environment.yml
conda activate batch18-notebook
python -m ipykernel install --user --name batch18-notebook --display-name "Batch18 (Python 3.11)"
```

In VS Code, select the `Batch18 (Python 3.11)` kernel for this notebook. The
Anaconda base environment on this computer has incompatible compiled
NumPy/Pandas/Matplotlib packages. The dedicated Batch18 kernel avoids that
binary mismatch. Restart the kernel and run all cells after selecting it.

The radial model can also be run at a custom grid, for example:

```bash
python scripts/run_tier2.py --nr 40 --nz 200
```

The main inputs are in `case/byu_case.yaml`. Figures and numerical summaries
are written under `report/`. The 2-D run writes CO, H2, CH4, CO2, O2, H2O,
temperature and carbon-conversion contours. The grid study writes a CSV and a
comparison figure. The particle-size script runs a six-bin mass-weighted
Rosin-Rammler sensitivity using the 1-D solver. The PDF builder writes the
concise report and class presentation PDFs. A separate, detailed IEEEtran
report and its self-contained Overleaf source are in report/overleaf/.

## Current model scope

| Component | Current state |
|---|---|
| Case inputs | Coal analysis, stream rates and particle distribution transcribed from Mularski & Modlinski (2021); oxygen is by difference. Particle density and reduced-model closures are labeled assumptions. |
| Cross-section-averaged 1-D calculation | Runs and closes elemental balances; adiabatic plug-flow assumptions limit temperature and conversion predictions. |
| Radial 2-D calculation | Runs as radially coupled annular stream tubes with operator-split implicit radial species/heat mixing. It is a reduced model, not RANS/particle CFD. |
| Numerical study | 20x100, 40x200, 80x400 and 120x600 results are in `report/grid_independence.csv`. The 80-to-120 grid change is reported, not hidden. |
| Validation | Outlet values are compared with Brown et al. (1988); digitized Fig. 9 centerline markers and Figures 12-14 radial probes are compared with the radial-model profiles. Digitization sources, uncertainty, plots and pointwise error tables are included. |
| Official record | The user-supplied selection-sheet CSV confirms Batch 18's five members, Mularski (2021), and the BYU case. The six-group topic cap is full; the instructor should confirm no identical operating-condition conflict. |
| Report/presentation | `report/Batch 18.pdf` and `presentation/Batch 18 - Class Presentation.pdf` are generated from the final figures; the roster is recorded in both. |
| Source package | `Batch18_source.zip` contains the source code, inputs, final report, presentation, figures and result CSV files. |

The finest-grid radial-model run closes C/H/O/N/Ar balances to about 0.000003%.
Its 4000 K value is the temperature-recovery ceiling, so the actual peak is
not resolved by the current thermodynamic bracket. Its predicted conversion
also remains below the published experiment. Both gaps are discussed in the
report rather than presented as validation success.

The 1400 K hot-start patch adds 19.35 kW across the radial-model lanes, equal to
9.75% of the coal HHV input rate. The area-average model outlet contains about
4.02 vol% dry O2, and its carbon conversion is 28.48 percentage points below the
experiment. The particle-size sweep is flat because the 1-D calculation saturates at full
conversion; it is a model diagnostic, not a resolved physical size effect.

The detailed IEEE report is report/overleaf/Batch18_IEEE_Report.pdf. Upload
report/overleaf/Batch18_IEEE_Overleaf_Source.zip to Overleaf to edit or
recompile it. The report maps feed, axial and radial species, temperature,
experimental comparisons, numerical checks, and project artifacts to evidence.

## Project layout

```text
case/          BYU case inputs and source notes
src/gasifier/  chemistry, thermodynamics, 1-D and reduced 2-D solvers
scripts/       model runs, grid study, validation plotting
data/          reference and digitized validation data
docs/          theory, numerics, coding and validation notes
notebooks/     self-contained solver walkthrough and live demonstration
report/        submission and detailed IEEE reports, plots, result CSV files, and Overleaf source
presentation/  class presentation material
checklists/    rubric and completion gates
tests/         element-conservation guard rails
```
