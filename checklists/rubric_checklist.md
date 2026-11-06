# Batch 18 rubric and submission checklist

The assignment brief awards 40 group marks for six required results, the
report/source submission, and the class presentation.

## Required results

| # | Required result | Evidence in this project | Status |
|---|---|---|---|
| 1 | Feedstock/feed composition and major species | Corrected case table in the report; proximate basis is as received, ultimate basis is DAF. | Ready |
| 2 | Species distribution graphs | Tier 1 and Tier 2 axial profiles in `report/figures/`. | Ready |
| 3 | Species contours inside the reactor | Tier 2 CO, H2, CH4, CO2, O2 and H2O contours. | Ready, reduced-order model |
| 4 | Reactor temperature and contours | Tier 2 temperature contour and axial profile; peak is flagged at the 4000 K recovery ceiling. | Ready with limitation stated |
| 5 | Comparison with journal results | Outlet composition/conversion, Tier 2 near-axis profile versus Figure 9 centerline markers, and radial profiles versus Figures 12-14 probe markers. | Axial and radial comparisons complete; large errors and digitization uncertainty are disclosed |
| 6 | Conclusion summarizing findings | Report conclusion based on computed, compared and unresolved results. | In report |

## Final submission checks

- [x] Add the group member names and IDs to the report and presentation.
- [x] Confirm the paper and operating conditions are recorded in the user-supplied selection-sheet CSV.
- [ ] Confirm with the instructor that no other Entrained-Flow group uses the same operating conditions; six of six topic slots are taken.
- [x] Digitize axial centerline markers from Figure 9, then regenerate Tier 2 overlays and percentage-point error metrics.
- [x] Digitize radial experimental markers from Figures 12-14, retain attributed source-page renders, and compare against Tier 2 profiles at all eight axial stations.
- [x] Review the final report and presentation PDFs as rendered files.
- [x] Package the Python source, inputs, results and final PDFs in `Batch18_source.zip`.
- [ ] Submit `Batch 18.pdf`, source code, and class presentation to the course Drive folder.

## Quality evidence already available

- Element balances for the finest Tier 2 run close to about 0.000003%.
- Grid results are recorded at 20x100, 40x200, 80x400 and 120x600; the 80x400 to 120x600 change is about 9 K in outlet temperature, 1.3 percentage points in carbon conversion, and 0.6-0.8 percentage points in the main dry gas species.
- The reduced model is distinguished from the paper's RANS/particle CFD.
- Provisional particle density, uniform inlet-spread fraction, radial mixing coefficient, instantaneous coal moisture release, and omitted radiation/recirculation are identified as assumptions.
- The reference paper's H2O validation uncertainty (about +/-14%) is stated wherever water is compared.
- Centerline mean/max absolute errors are calculated against experimental markers: CO 12.81/25.72 pp, H2 10.50/13.03 pp, CO2 7.27/14.46 pp; H2O 25.54/31.34 pp is shown but should not be scored because of uncertainty.
- Radial mean/max absolute errors over the scored markers are CO 8.54/24.22 pp, H2 7.02/15.33 pp, and CO2 6.74/20.51 pp; H2O is not scored because the paper derives it from hydrogen balance.
- A Rosin-Rammler bin sweep is included as a Tier 1 diagnostic. It is explicitly not claimed as a resolved physical particle-size effect because all cases saturate at 100% conversion.

## Official roster (user-supplied selection-sheet CSV)

| Roll number | Student |
|---|---|
| 23ME31035 | Upendra Singh |
| 23ME31025 | Samrudh Nelli |
| 23ME10102 | Arnav Chauhan |
| 23ME3AI34 | Ashutosh Ranjan |
| 23MF10027 | Naveen Saini |
