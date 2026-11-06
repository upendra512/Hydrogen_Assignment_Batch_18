# Verification and validation protocol

## Case provenance

The 2021 Mularski and Modlinski article supplies the main BYU test case: vessel
size, Utah-coal analysis, feed rates, inlet gas compositions and Rosin-Rammler
parameters. The original Brown et al. (1988) article supplies the experimental
centerline/radial probe data and effluent results. A separate BYU CFD paper
reports the primary and annular injector dimensions used by the reduced Tier 2
inlet profile. Those dimensions are not tabulated in the 2021 article.

| Input | Source or treatment |
|---|---|
| Reactor 0.20 m diameter x 1.80 m | Mularski & Modlinski (2021), reactor section |
| Pressure 1 atm | Mularski & Modlinski (2021) |
| Proximate analysis: VM 45.6, fixed carbon 43.7, ash 8.3, moisture 2.4 wt% | Table 2, as received |
| Ultimate analysis: C 77.6, H 6.56, N 1.42, S 0.55 wt% | Table 2, DAF; oxygen 13.87% is calculated by difference |
| Coal 23.88 kg/h; primary gas 26.24 kg/h; secondary steam 6.62 kg/h | Table 3 |
| Particle range 1-85 um, mean 36 um, spread 1.033 | Table 4 |
| Primary nozzle ID 13 mm; secondary annulus OD 28.6 mm | Abani & Ghoniem (2013), BYU injector geometry |
| Particle density 1300 kg/m3 | Provisional assumption; not reported in the cited BYU case table |
| Inlet background spread and radial mixing coefficient | Reduced-model assumptions varied for sensitivity; not measured values |

## Published comparison targets

Brown et al. (1988), Table 2, report dry inert-free effluent composition for
the Utah bituminous test: CO 51.1%, CO2 23.6%, H2 24.7%, CH4 0.3%, and carbon
conversion 82%. Their composition is rounded and sums to 99.7%. Mularski and
Modlinski (2021), Table 7, report 83% conversion for the mean 36 um particle
and 77% for all 1-85 um fractions, against the same experimental 82% value.

The reference paper's Table 8 reports mean/maximum absolute composition
differences in percentage points for its modified CFD parameters: CO
4.82/18.48 pp, H2 5.47/7.95 pp, CO2 4.72/10.15 pp, and H2O 9.58/20.22 pp.
These values describe the reference model, not the reduced Python model. Its
authors exclude H2O from the quality assessment because the experimental
estimate has about +/-14% uncertainty.

## Digitized profile data

`data/validation/fig09_axial_centerline.csv` contains approximate experimental
markers from Figure 9. The measured CO, H2 and CO2 centerline data are
attributed to Brown et al. (1988); the source paper calculates H2O by hydrogen
balance. The model uses values from its first annulus center at r=0.00083 m,
so the model curve is near-axis, not exactly at r=0. The near-axis mean/max
absolute errors are 12.81/25.72 pp for CO, 10.50/13.03 pp for H2, and
7.27/14.46 pp for CO2. H2O is shown but not scored because the paper gives it
about +/-14% uncertainty.

`data/validation/fig12_14_radial_experiment.csv` contains 140 approximate
experimental markers from Figures 12-14 at the eight axial stations marked in
Figure 15 (0.13 to 1.73 m). At each station, the Tier 2 radial profiles are
interpolated to the digitized marker radii. Across all scored CO, H2 and CO2
markers, the mean/max absolute errors are 8.54/24.22 pp for CO, 7.02/15.33 pp
for H2, and 6.74/20.51 pp for CO2. H2O markers are retained for provenance
but excluded from scoring, as the paper itself cautions against treating
them as experimental references.

The source-page renders, digitization scripts, axis calibration method, and
estimated uncertainties (radial: +/-0.001 m and +/-0.5 pp) are included under
`data/validation/` and `scripts/`. Recreate the profiles with
`python scripts/run_tier2.py`; run `python scripts/make_validation_plots.py`
and `python scripts/make_radial_validation_plots.py` to regenerate both
comparisons. These figure-based digitizations are approximate, not raw probe
files, and should not be interpreted more precisely than their stated
uncertainty.

## Verification distinct from validation

- Tier 1 and Tier 2 global C/H/O/N/Ar balances should stay below 1%.
- The grid study compares 20x100, 40x200, 80x400 and 120x600. The 80-to-120
  change is 0.6-0.8 percentage points for the main dry gas species, around
  2.3% relative for carbon conversion, and under 0.3% for outlet mean
  temperature.
- Numerical grid convergence does not establish physical accuracy. The
  4000 K peak is at the current temperature-recovery ceiling, and the reduced
  model's carbon conversion is below the published experiment.
- A pure-diffusion analytical step test is not yet implemented. Do not mark it
  as passed.
