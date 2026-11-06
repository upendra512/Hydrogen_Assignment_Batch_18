# Validation data

## Axial centerline

`fig09_axial_centerline.csv` contains approximate experimental marker values
digitized from Figure 9 of Mularski and Modlinski (2021). It contains orange
experimental markers only, not the colored model curves. The paper attributes
the CO, H2, and CO2 measurements to Brown et al. (1988), and calculates H2O by
hydrogen balance. Estimated digitization uncertainty is +/-0.3 percentage
point and +/-0.01 m axial distance.

## Radial profiles

`fig12_14_radial_experiment.csv` contains 140 approximate experimental markers
digitized from Figures 12-14 at eight axial stations: 0.13, 0.20, 0.28,
0.34, 0.51, 0.81, 1.12, and 1.73 m. Only orange square markers are retained;
the reference CFD curves are not digitized as experimental data. The radial
coordinate is calibrated from the 0 to 0.1 m horizontal axis and Figure 15's
reactor geometry. Estimated digitization uncertainty is +/-0.001 m in radius
and +/-0.5 mole-fraction percentage point. H2O is included in the CSV but is
not scored because the paper derives it from hydrogen balance and cautions
against using it as experimental reference data.

The attributed 360-dpi source-page renders used for the digitization are in
`source_figures/`. The source is Mularski, J. and Modlinski, N. (2021),
*Energies*, 14(6), 1729, https://doi.org/10.3390/en14061729 (open-access
paper). Rebuild the marker CSV with:

```bash
python scripts/digitize_radial_markers.py
```

## Comparisons

Run Tier 2 first. `scripts/make_validation_plots.py` compares the near-axis
model profile with the digitized centerline measurements.
`scripts/make_radial_validation_plots.py` compares Tier 2 radial profiles at
the same eight axial stations with digitized experimental probes. Both report
absolute composition differences in percentage points. Radial probes are
approximate figure digitizations, so interpret the results at the stated
uncertainty rather than as exact raw data.

| File | Meaning | Status |
|---|---|---|
| `fig09_axial_centerline.csv` | Figure 9 experimental centerline markers | Digitized and compared |
| `fig12_14_radial_experiment.csv` | Figures 12-14 experimental radial markers | Digitized and compared |
| `source_figures/*.png` | Attributed 360-dpi source pages 15-16 | Included for audit |
| `fig09_paper_model.csv` | Figure 9 model curves | Not digitized; not needed for experiment comparison |
