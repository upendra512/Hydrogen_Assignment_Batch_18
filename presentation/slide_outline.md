# Batch 18 presentation outline

The 16-slide PDF is `presentation/Batch 18 - Class Presentation.pdf`. It uses the report's final figures and the official five-person roster.

| # | Slide | Main content |
|---|---|---|
| 1 | Title and roster | Entrained-flow gasifier, selected paper and all five members |
| 2 | Assigned case | BYU geometry, operating pressure, stream rates and particle distribution |
| 3 | Utah coal | Proximate as-received and ultimate DAF composition |
| 4 | Reduced model and reference CFD | One solver workflow: axial reacting-lane chemistry coupled across radial annuli; model differences and the 1400 K hot-start energy input |
| 5 | Temperature field | Contour, 4000 K recovery ceiling and outlet temperature |
| 6 | CO and H2 contours | Radial and axial fields |
| 7 | CO2 and H2O contours | Fields and water-measurement uncertainty |
| 8 | O2 and CH4 contours | Fields and residual outlet oxygen |
| 9 | Carbon conversion field | Annular carbon-conversion contour |
| 10 | Axial profiles | Area-average species and temperature profiles |
| 11 | Numerical verification | Grid refinement, balance closure and unresolved peak convergence |
| 12 | BYU outlet comparison | Outlet composition and carbon-conversion differences |
| 13 | Near-axis comparison with centerline data | Digitized experimental markers versus near-axis profiles from the radial calculation and absolute errors in percentage points |
| 14 | Radial profile comparison | Digitized Figures 12-14 probe markers versus the radial calculation at eight axial stations |
| 15 | Particle-size diagnostic | Mass-weighted Rosin-Rammler sweep and saturation in the cross-section-averaged calculation |
| 16 | Conclusions | Quantitative findings, limits and condition-uniqueness follow-up |

## Speaking plan

All five members should speak. Divide the material based on who can explain each part: case and feed, chemistry and assumptions, numerical method, results and validation, then conclusions and limitations. Keep the explanation tied to the figures and numbers in the report.

## Questions to prepare for

- Why is the temperature peak unresolved? The energy closure stops at 4000 K, and every grid reaches that ceiling.
- What does the ignition patch do? It starts each reacting stream tube at 1400 K; summed across the radial annuli, the patch is 19.35 kW, or 9.75% of coal HHV input.
- Why is conservation not validation? The balances track implementation bookkeeping; the outlet and near-axis profiles still differ from measurements.
- What does the profile comparison show? Against digitized centerline measurements, near-axis mean / maximum absolute errors are 12.81 / 25.72 percentage points for CO, 10.50 / 13.03 for H2, and 7.27 / 14.46 for CO2. H2O errors are shown but its roughly +/-14% measurement uncertainty is too large for the paper's score.
- What do the radial probes add? At eight axial stations, mean absolute differences are 8.54 pp for CO, 7.02 for H2, and 6.74 for CO2; local maxima are 24.22, 15.33, and 20.51 pp. Values are approximate figure digitizations. H2O is excluded because the paper derives it by hydrogen balance.
- What does the particle-size sweep show? The cross-section-averaged calculation saturates at 100% conversion for every tested distribution, so it cannot resolve a physical size effect.
- What remains administratively? Confirm with the instructor that no other Entrained-Flow group uses identical operating conditions, and confirm the class presentation slot.
