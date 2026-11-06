#!/usr/bin/env python3
"""Build the Batch 18 report and a classroom-ready slide PDF."""
from __future__ import annotations

import csv
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether,
                                PageBreak, PageTemplate, Paragraph, Spacer,
                                Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "report"
FIG = REPORT / "figures"
PRESENTATION = ROOT / "presentation"
NAVY = colors.HexColor("#13283F")
TEAL = colors.HexColor("#187E83")
PALE = colors.HexColor("#E9F1F3")
MID = colors.HexColor("#516271")
INK = colors.HexColor("#19242D")
WHITE = colors.white

ROSTER = [
    ("23ME31035", "Upendra Singh"),
    ("23ME31025", "Samrudh Nelli"),
    ("23ME10102", "Arnav Chauhan"),
    ("23ME3AI34", "Ashutosh Ranjan"),
    ("23MF10027", "Naveen Saini"),
]


def styles():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle("TitleCustom", parent=base["Title"], fontName="Helvetica-Bold",
                            fontSize=25, leading=30, textColor=NAVY, alignment=TA_LEFT,
                            spaceAfter=10))
    base.add(ParagraphStyle("SubtitleCustom", parent=base["Normal"], fontName="Helvetica",
                            fontSize=12, leading=16, textColor=MID, spaceAfter=8))
    base.add(ParagraphStyle("H1Custom", parent=base["Heading1"], fontName="Helvetica-Bold",
                            fontSize=17, leading=21, textColor=NAVY, spaceBefore=4, spaceAfter=8))
    base.add(ParagraphStyle("H2Custom", parent=base["Heading2"], fontName="Helvetica-Bold",
                            fontSize=11.5, leading=14, textColor=TEAL, spaceBefore=5, spaceAfter=4))
    base.add(ParagraphStyle("BodyCustom", parent=base["BodyText"], fontName="Helvetica",
                            fontSize=9.2, leading=12.5, textColor=INK, spaceAfter=6))
    base.add(ParagraphStyle("SmallCustom", parent=base["BodyText"], fontName="Helvetica",
                            fontSize=7.5, leading=9.5, textColor=MID, spaceAfter=3))
    base.add(ParagraphStyle("TableCustom", parent=base["BodyText"], fontName="Helvetica",
                            fontSize=7.8, leading=9.4, textColor=INK))
    base.add(ParagraphStyle("TableHeadCustom", parent=base["BodyText"], fontName="Helvetica-Bold",
                            fontSize=7.8, leading=9.4, textColor=WHITE))
    base.add(ParagraphStyle("CoverTitle", parent=base["Title"], fontName="Helvetica-Bold",
                            fontSize=27, leading=32, textColor=NAVY, alignment=TA_CENTER,
                            spaceAfter=8))
    base.add(ParagraphStyle("CoverSub", parent=base["Normal"], fontName="Helvetica",
                            fontSize=13, leading=18, textColor=TEAL, alignment=TA_CENTER,
                            spaceAfter=18))
    return base


S = styles()


def p(text: str, style="BodyCustom"):
    return Paragraph(text, S[style])


def make_table(rows, widths, font_size=7.8, header=True, padd=4):
    cooked = []
    for i, row in enumerate(rows):
        style = "TableHeadCustom" if header and i == 0 else "TableCustom"
        cooked.append([Paragraph(str(cell), S[style]) for cell in row])
    tbl = Table(cooked, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), padd),
        ("RIGHTPADDING", (0, 0), (-1, -1), padd),
        ("TOPPADDING", (0, 0), (-1, -1), padd),
        ("BOTTOMPADDING", (0, 0), (-1, -1), padd),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5DB")),
    ]
    if header:
        cmds.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
        if len(rows) > 1:
            cmds.append(("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PALE]))
    tbl.setStyle(TableStyle(cmds))
    return tbl


def fit_image(path: Path, width: float, max_height: float):
    img = Image(str(path))
    factor = min(width / img.imageWidth, max_height / img.imageHeight)
    img.drawWidth = img.imageWidth * factor
    img.drawHeight = img.imageHeight * factor
    img.hAlign = "CENTER"
    return img


def page_decoration(canvas_obj, doc):
    canvas_obj.saveState()
    w, h = letter
    if doc.page > 1:
        canvas_obj.setFont("Helvetica-Bold", 8)
        canvas_obj.setFillColor(NAVY)
        canvas_obj.drawString(0.62 * inch, h - 0.42 * inch, "BATCH 18  |  ENTRAINED-FLOW COAL GASIFICATION")
        canvas_obj.setStrokeColor(colors.HexColor("#CBD5DB"))
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(0.62 * inch, h - 0.49 * inch, w - 0.62 * inch, h - 0.49 * inch)
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(MID)
    canvas_obj.drawString(0.62 * inch, 0.36 * inch, "ME40249 | Sources and assumptions are identified in the report")
    canvas_obj.drawRightString(w - 0.62 * inch, 0.36 * inch, f"{doc.page}")
    canvas_obj.restoreState()


def build_report():
    out = REPORT / "Batch 18.pdf"
    doc = BaseDocTemplate(str(out), pagesize=letter, rightMargin=0.62 * inch,
                          leftMargin=0.62 * inch, topMargin=0.68 * inch,
                          bottomMargin=0.62 * inch, title="Batch 18 - Entrained-Flow Coal Gasification",
                          author="ME40249 Batch 18")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="body")
    doc.addPageTemplates([PageTemplate(id="main", frames=frame, onPage=page_decoration)])
    story = []

    # 1. Cover and official team record.
    story += [Spacer(1, 0.85 * inch), p("BATCH 18", "CoverSub"),
              p("Reduced-Order Simulation of an Entrained-Flow Coal Gasifier", "CoverTitle"),
              p("BYU atmospheric reactor | Utah bituminous coal | Mularski and Modlinski (2021)", "CoverSub"),
              Spacer(1, 0.16 * inch),
              p("The work uses the published BYU test conditions and compares a transparent Python model with reported experimental and CFD results. The numerical predictions are presented with their limits, including an unresolved temperature ceiling and a substantial conversion gap.", "BodyCustom"),
              Spacer(1, 0.08 * inch), p("Group roster", "H2Custom")]
    story.append(make_table([["Roll number", "Student"]] + [list(row) for row in ROSTER],
                            [1.45 * inch, 5.6 * inch]))
    story += [Spacer(1, 0.15 * inch), PageBreak()]

    # 2. Abstract and requirement map.
    story += [p("Abstract", "H1Custom"), p(
        "This project models the BYU atmospheric entrained-flow gasifier using the Utah bituminous coal and Table 3 streams selected in Mularski and Modlinski (2021). One reduced-model workflow applies axial reacting-lane chemistry across radial annuli, with radial species and heat exchange. The 1-D and radial descriptions refer to spatial detail within this workflow, not separate project phases. The model does not solve momentum, particle trajectories, radiation or recirculation. At 120 radial by 600 axial stations, elemental balances close within 0.000003%, while the outlet-area-average temperature is 3556.7 K and the recovered peak reaches the 4000 K solver ceiling. The predicted carbon conversion is 53.52%, compared with 82% in the BYU experiment; dry inert-free CO, H2, CO2 and CH4 are 58.66, 16.68, 24.21 and 0.45 vol%, respectively. The model also leaves 3.88 vol% dry O2 at the outlet. Grid refinement changes the outlet temperature by 9.1 K and conversion by 1.28 percentage points from 80x400 to 120x600. These checks support numerical bookkeeping, but the outlet disagreement and ceiling prevent a claim of physical validation. A mass-weighted Rosin-Rammler sweep using the cross-section-averaged calculation exposes saturation in the current chemistry.", "BodyCustom"),
              p("Study scope and outputs", "H2Custom")]
    coverage = [
        ["Analysis area", "Evidence presented"],
        ["Feed composition", "Utah coal proximate and DAF ultimate analyses; primary and secondary streams."],
        ["Species distributions", "Cross-sectional area-average axial profiles for CO, H2, CO2, H2O, O2 and CH4."],
        ["Species contours", "Radial-axial contours for CO, H2, CO2, H2O and O2."],
        ["Reactor temperature", "Temperature contour and area-average axial temperature profile."],
        ["Comparison with journal results", "Outlet composition/conversion comparison plus a near-axis profile comparison from the radial calculation against digitized experimental markers from Mularski et al. (2021), Figure 9."],
        ["Conclusions", "Quantitative findings, model limits and validation gaps."],
    ]
    story += [make_table(coverage, [1.72 * inch, 5.33 * inch]), PageBreak()]

    # 3. Case.
    story += [p("1. Selected case and feed", "H1Custom"),
              p("The case is the BYU atmospheric entrained-flow reactor reported by Mularski and Modlinski (2021): 0.20 m internal diameter, 1.80 m length, 1 atm pressure, and a 23.88 kg/h Utah bituminous coal feed.", "BodyCustom"),
              p("Coal analysis", "H2Custom")]
    coal = [
        ["Analysis", "Basis", "Component", "wt%"],
        ["Proximate", "As received", "Moisture", "2.40"],
        ["Proximate", "As received", "Volatile matter", "45.60"],
        ["Proximate", "As received", "Fixed carbon", "43.70"],
        ["Proximate", "As received", "Ash", "8.30"],
        ["Ultimate", "Dry ash free", "Carbon", "77.60"],
        ["Ultimate", "Dry ash free", "Hydrogen", "6.56"],
        ["Ultimate", "Dry ash free", "Nitrogen", "1.42"],
        ["Ultimate", "Dry ash free", "Sulfur", "0.55"],
        ["Ultimate", "Dry ash free", "Oxygen", "13.87*"],
    ]
    story += [make_table(coal, [1.12 * inch, 1.35 * inch, 3.65 * inch, 0.93 * inch]),
              p("* Oxygen is calculated by difference from the reported DAF C, H, N and S fractions. The HHV used in the code is estimated as 33.52 MJ/kg DAF from the Channiwala-Parikh correlation because a measured HHV was not entered for this case.", "SmallCustom"),
              p("Operating streams", "H2Custom")]
    streams = [
        ["Stream", "Mass flow", "Inlet T", "Mole composition"],
        ["Primary", "26.24 kg/h", "400 K", "85.0% O2, 12.6% Ar, 2.4% H2O; coal carried in this stream"],
        ["Secondary", "6.62 kg/h", "473 K", "100% H2O"],
        ["Coal", "23.88 kg/h", "-", "Utah bituminous coal; 1-85 um Rosin-Rammler distribution"],
    ]
    story += [make_table(streams, [0.9 * inch, 1.2 * inch, 0.72 * inch, 4.23 * inch]),
              p("The 2021 paper specifies a Rosin-Rammler scale diameter of 36 um and spread parameter 1.033. The radial inlet profile also uses 13 mm primary-nozzle ID and 28.6 mm secondary-annulus OD from Abani and Ghoniem (2013), because the 2021 case table does not list nozzle sizes. Density (1300 kg/m3), 20% background inlet spreading and the radial mixing coefficient are explicit assumptions, not measurements.", "BodyCustom"), PageBreak()]

    # 4. Model and comparison.
    story += [p("2. Model formulation", "H1Custom"),
              p("The implementation assumes steady, ideal-gas flow at constant pressure. Its cross-section-averaged 1-D calculation uses plug flow, one gas-particle temperature and instantaneous moisture release. Temperature is recovered from an adiabatic enthalpy balance. An explicit 1400 K inlet ignition patch supplies the hot start that a cold plug-flow model cannot generate without recirculation. Summed across the 120 radial annuli, that patch adds 19.35 kW, or 9.75% of the coal HHV input rate. It stands in for flame stabilization and recirculated heat; it is a material model assumption, not a negligible numerical detail.", "BodyCustom"),
              p("The radial calculation allocates primary gas, secondary steam and coal to annular stream tubes using the nozzle areas. It applies the same axial chemistry in each lane and couples neighboring lanes through radial transport. Species exchange is solved with backward-Euler finite volumes. Species enthalpy is transferred with the gas, followed by a conservative radial heat-conduction step. The turbulent diffusivity follows D_t = C_mix U_bulk R with C_mix = 0.05, turbulent Schmidt number 0.70 and turbulent Prandtl number 0.90. A molecular floor and a 0.20 m2/s cap are imposed. The wall remains adiabatic. These 1-D and radial calculations are spatial components of one model workflow.", "BodyCustom"),
              p("The C2SM devolatilization constants are those reported in Table 5 of Mularski and Modlinski (2021), fitted there against FG-DVC. Char oxidation and gasification use that paper's BYU-fitted kinetic-diffusion parameters from Table 6 and its film-diffusion coefficient from Equation (3). The project does not rerun the FG-DVC or CBK/E-CBK/G fitting workflow. Gas chemistry is reduced to four global reactions and does not use the paper's full turbulence-chemistry coupling. The volatile species split adds assumptions to close the elemental balance; surplus carbon goes to a soot/char pool rather than explicit tar. Thus the published operating point and selected chemistry parameterizations are used, while the complete CFD model is not reproduced.", "BodyCustom"),
              p("Difference from the selected CFD", "H2Custom")]
    diff = [
        ["Feature", "Mularski and Modlinski (2021)", "Batch 18 implementation"],
        ["Flow field", "2-D axisymmetric RANS; realizable k-epsilon turbulence", "Radial stream tubes; no momentum equation"],
        ["Particle transport", "Lagrangian particles with stochastic dispersion", "Particles remain in their inlet annulus"],
        ["Radiation", "Discrete ordinates with WSGG gas radiation", "Adiabatic wall; no radiation"],
        ["Chemistry", "C2SM/FG-DVC devolatilization, fitted kinetic-diffusion char model, and EDC global gas reactions", "Published C2SM and BYU-fitted char parameters; four global gas reactions without EDC"],
        ["Tar and mixing", "Explicit tar, turbulent mixing and turbulence-chemistry coupling", "Surplus volatile carbon becomes soot; operator-split radial diffusion"],
    ]
    story += [make_table(diff, [1.08 * inch, 2.95 * inch, 3.02 * inch]),
              p("The radial code is a reduced-order model for spatial trends and conservation checks. It does not reproduce the reference CFD equations or the full burner recirculation zone.", "SmallCustom"), PageBreak()]

    # 5. Numerical verification.
    story += [p("3. Numerical verification", "H1Custom"),
              p("Global C, H, O, N and Ar flows are checked at the outlet, counting gases, char and unreacted coal. On the 120x600 grid, the maximum absolute elemental imbalance is 0.0000021%. This demonstrates that the implemented source terms and radial transfers conserve the tracked elements. It does not establish that the rate laws or closure assumptions match the physical reactor.", "BodyCustom"),
              fit_image(REPORT / "fig_grid_independence.png", 6.9 * inch, 2.85 * inch),
              p("Figure 1. Grid refinement for carbon conversion and area-average outlet temperature. The peak temperature is 4000 K on all four grids because it reaches the recovery ceiling, so peak-temperature convergence cannot be assessed.", "SmallCustom"),
              make_table([
                  ["Grid", "Outlet T (K)", "Conversion (%)", "Dry CO (%)", "Dry H2 (%)", "Dry CO2 (%)"],
                  ["20 x 100", "3447.9", "62.47", "55.95", "17.25", "14.62"],
                  ["40 x 200", "3530.3", "57.41", "53.46", "14.87", "18.73"],
                  ["80 x 400", "3547.6", "54.80", "50.71", "14.98", "19.86"],
                  ["120 x 600", "3556.7", "53.52", "50.07", "14.24", "20.66"],
              ], [0.92 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch]),
              p("The grid-study species fractions are normalized to total dry outlet gas, including Ar, N2 and residual O2. The outlet comparison later uses a dry inert-free basis. From 80x400 to 120x600, outlet temperature shifts by 9.1 K, conversion falls by 1.28 percentage points, and the principal dry species shift by 0.65-0.80 points. This refinement trend does not establish physical accuracy; a separate analytical pure-diffusion test has not been completed.", "BodyCustom"), PageBreak()]

    # 6-9. Spatial fields.
    story += [p("4. Temperature and CO fields", "H1Custom"),
              fit_image(FIG / "fig_contour_T.png", 6.9 * inch, 2.65 * inch),
              p("Figure 2. Temperature field (K), mirrored about the axis. The reported maximum is clipped at the 4000 K temperature-recovery ceiling; its true peak is unresolved.", "SmallCustom"),
              fit_image(FIG / "fig_contour_CO.png", 6.9 * inch, 2.65 * inch),
              p("Figure 3. CO mole fraction. The annular model resolves radial redistribution by the assumed turbulent-diffusion closure; it has no radial momentum or particle-dispersion solution.", "SmallCustom"), PageBreak()]
    story += [p("5. Hydrogen and carbon-dioxide fields", "H1Custom"),
              fit_image(FIG / "fig_contour_H2.png", 6.9 * inch, 2.65 * inch),
              p("Figure 4. H2 mole fraction. In this model, hydrogen comes from the imposed volatile split, water-gas shift and char-steam reaction.", "SmallCustom"),
              fit_image(FIG / "fig_contour_CO2.png", 6.9 * inch, 2.65 * inch),
              p("Figure 5. CO2 mole fraction. The published outlet comparison is more meaningful than apparent contour smoothness because the radial mixing coefficient is assumed.", "SmallCustom"), PageBreak()]
    story += [p("6. Steam and methane fields", "H1Custom"),
              fit_image(FIG / "fig_contour_H2O.png", 6.9 * inch, 2.65 * inch),
              p("Figure 6. H2O mole fraction. The reference paper reports about +/-14% experimental uncertainty for water and excludes it from its model-quality score.", "SmallCustom"),
              fit_image(FIG / "fig_contour_CH4.png", 6.9 * inch, 2.65 * inch),
              p("Figure 7. CH4 mole fraction. Methane is a minor outlet product in both the computed and measured dry inert-free streams.", "SmallCustom"), PageBreak()]
    story += [p("7. Oxygen and carbon conversion fields", "H1Custom"),
              fit_image(FIG / "fig_contour_O2.png", 6.9 * inch, 2.65 * inch),
              p("Figure 8. O2 mole fraction. The model retains 3.88 vol% O2 in its dry outlet, which flags incomplete oxygen consumption and a chemistry/mixing mismatch.", "SmallCustom"),
              fit_image(FIG / "fig_contour_carbon_conversion.png", 6.9 * inch, 2.45 * inch),
              p("Figure 9. Local fuel-carbon conversion, calculated from remaining char and raw coal in each annulus.", "SmallCustom"), PageBreak()]
    story += [p("8. Axial species and temperature profiles", "H1Custom"),
              fit_image(FIG / "fig_tier2_area_average_species.png", 6.35 * inch, 3.35 * inch),
              p("Figure 10. Cross-sectional area-average species profiles. The pointwise experiment comparison uses the near-axis model profile separately, because the reference measurements are centerline data.", "SmallCustom"),
              fit_image(FIG / "fig_tier2_area_average_temperature.png", 6.35 * inch, 3.1 * inch),
              p("Figure 11. Area-average temperature along the reactor. The outlet is 3556.7 K. The local peak reaches the numerical ceiling of 4000 K and must not be interpreted as a resolved physical temperature.", "SmallCustom"),
              p("The selected paper describes a flame peak near 3000 K. The excessive and unresolved peak is consistent with the model's adiabatic wall, missing radiation, ignition patch equal to 9.75% of the coal HHV input rate, one-temperature treatment, and uncalibrated reduced reaction/mixing closures. The calculation is useful for locating where its own species fields change; the temperature field is not quantitatively validated.", "BodyCustom"),
              make_table([
                  ["Radial-model result", "Value", "Interpretation"],
                  ["Peak temperature", "4000 K", "At solver ceiling; unresolved"],
                  ["Outlet area-average T", "3556.7 K", "Reduced-model output"],
                  ["Carbon conversion", "53.52%", "28.48 percentage points below experiment"],
                  ["Dry outlet O2", "3.88 vol%", "Residual oxygen indicates chemistry mismatch"],
              ], [1.65 * inch, 1.35 * inch, 4.05 * inch]), PageBreak()]

    # 10. Near-axis comparison with digitized centerline experimental markers.
    with (REPORT / "validation_errors.csv").open(encoding="utf-8", newline="") as fh:
        validation = {row["species"]: row for row in csv.DictReader(fh)}
    validation_rows = [["Species", "n", "Batch 18 mean / max (pp)", "Paper Table 8 mean / max (pp)"]]
    for sp in ("CO", "H2", "CO2", "H2O"):
        row = validation[sp]
        validation_rows.append([sp, row["n_points"],
                                f"{float(row['mean_abs_error_pp']):.2f} / {float(row['max_abs_error_pp']):.2f}",
                                f"{float(row['paper_table8_mean_abs_error_pp']):.2f} / {float(row['paper_table8_max_abs_error_pp']):.2f}"])
    story += [p("9. Near-axis comparison with centerline measurements", "H1Custom"),
              fit_image(REPORT / "fig_validation_axial_centerline.png", 6.8 * inch, 4.0 * inch),
              p("Figure 12. Near-axis profile from the radial calculation (innermost annulus center, r = 0.00083 m) compared with centerline experimental markers digitized from Figure 9 of Mularski and Modlinski (2021). Marker coordinates are approximate, with estimated digitization uncertainty of about +/-0.3 percentage point and +/-0.01 m.", "SmallCustom"),
              make_table(validation_rows, [0.85 * inch, 0.48 * inch, 2.48 * inch, 2.98 * inch]),
              p("Errors are mean / maximum absolute differences in mole fraction, reported as percentage points at the digitized experimental axial locations. This is the same absolute-difference convention as the paper's Table 8, not a relative percentage error. H2O is shown for completeness but excluded from the paper's quality score because its experimental estimate has about +/-14% uncertainty. The large CO, H2 and CO2 gaps show that the current reduced model does not reproduce the measured axial profiles.", "BodyCustom"), PageBreak()]

    # 10. Radial comparison with digitized experimental probe markers.
    with (REPORT / "validation_radial_errors.csv").open(encoding="utf-8", newline="") as fh:
        radial_validation = {row["species"]: row for row in csv.DictReader(fh)
                            if row["axial_station_m"] == "all"}
    radial_rows = [["Species", "n", "Mean / max absolute error (pp)"]]
    for sp in ("CO", "H2", "CO2"):
        row = radial_validation[sp]
        radial_rows.append([sp, row["n_points"],
                            f"{float(row['mean_abs_error_pp']):.2f} / {float(row['max_abs_error_pp']):.2f}"])
    story += [p("10. Radial profiles against experimental probes", "H1Custom"),
              fit_image(REPORT / "fig_validation_radial_profiles.png", 6.85 * inch, 4.52 * inch),
              p("Figure 13. Radial-model profiles at four representative axial stations compared with orange experimental markers digitized from Figures 12-14 of Mularski and Modlinski (2021). All eight source stations were scored; the plot shows 0.13, 0.28, 0.51 and 1.73 m. Marker coordinates are approximate (estimated +/-0.001 m in radius and +/-0.5 percentage point in composition).", "SmallCustom"),
              make_table(radial_rows, [1.5 * inch, 0.7 * inch, 4.45 * inch]),
              p("The pooled scores cover 105 CO, H2 and CO2 probe points across eight axial stations. H2O is omitted because the paper derives it by hydrogen balance rather than reporting an independent measured profile. These comparisons use radial-model values interpolated to the digitized probe radii. The largest local discrepancies remain substantial, so the reduced model does not reproduce all measured radial structure.", "BodyCustom"), PageBreak()]

    # 11. Outlet comparison.
    story += [p("11. Outlet comparison with published results", "H1Custom"),
              p("Brown et al. (1988) report a dry inert-free Utah-coal effluent composition and 82% carbon conversion. The model composition below is calculated from the summed outlet molar flow of the 120x600 radial calculation after removing H2O, Ar, N2 and O2, then renormalizing CO, H2, CO2 and CH4 to 100%. Differences are model minus reported experiment in percentage points.", "BodyCustom"),
              make_table([
                  ["Quantity", "Batch 18 model", "Experiment", "Difference"],
                  ["CO (vol%)", "58.66", "51.1", "+7.56 pp"],
                  ["H2 (vol%)", "16.68", "24.7", "-8.02 pp"],
                  ["CO2 (vol%)", "24.21", "23.6", "+0.61 pp"],
                  ["CH4 (vol%)", "0.45", "0.3", "+0.15 pp"],
                  ["Carbon conversion", "53.52%", "82%", "-28.48 pp"],
              ], [2.0 * inch, 1.55 * inch, 1.45 * inch, 2.05 * inch]),
              Spacer(1, 7), p("The conversion mismatch and residual outlet O2 show that elemental conservation alone is not validation. The model overpredicts CO, underpredicts H2 and converts too little solid carbon. Cold-gas efficiency is 25.95% on the LHV basis used here; it is not compared directly with the experimental value because the calorific-value basis and product accounting differ.", "BodyCustom"),
              p("The paper's Table 8 values describe its own modified CFD parameters; they are shown on the preceding page as a reference benchmark, not attributed to Batch 18. The paper also reports carbon conversion of 83% for the 36 um monodisperse case and 77% for the 1-85 um size distribution, against 82% measured. These values check the paper's particle-size result, not a prediction reproduced by the reduced model.", "BodyCustom"), PageBreak()]

    # 12. Rosin-Rammler diagnostic.
    with (REPORT / "particle_size_sensitivity.csv").open(encoding="utf-8", newline="") as fh:
        sens = list(csv.DictReader(fh))
    base_row = next(row for row in sens if row["d_scale_um"] == "36.0" and row["spread"] == "1.033")
    story += [p("12. Rosin-Rammler particle-size diagnostic", "H1Custom"),
              p("The paper's particle size distribution is represented as F(d) = 1 - exp[-(d/d_scale)^n], truncated to 1-85 um. Six diameter bins with equal increments in cumulative mass are run independently; outlet gas flows and fuel-based metrics are weighted by each bin's mass fraction. The study varies d_scale = 20, 36 and 60 um and n = 0.7, 1.033 and 1.5. A monodisperse 36 um run is also included.", "BodyCustom"),
              fit_image(REPORT / "fig_particle_size_sensitivity.png", 6.6 * inch, 3.0 * inch),
              p("Figure 14. Mass-weighted carbon conversion and H2/CO response from the cross-section-averaged calculation. Each curve is flat because that calculation converts 100% of fuel carbon and returns identical outlet chemistry for every tested particle distribution.", "SmallCustom"),
              make_table([
                  ["Distribution", "Conversion", "CGE", "H2/CO"],
                  ["RR 36 um, n=1.033", f"{float(base_row['carbon_conversion_pct']):.2f}%", f"{float(base_row['cold_gas_efficiency_pct_course_LHV']):.2f}%", f"{float(base_row['H2_to_CO_molar_ratio']):.3f}"],
                  ["All 10 cases", "100.00%", "71.65%", "0.451"],
                  ["Mularski 36 um mono", "83%", "Reference CFD", "Not listed here"],
                  ["Mularski full 1-85 um RR", "77%", "Reference CFD", "Not listed here"],
                  ["Brown et al. experiment", "82%", "Experimental", "Not listed here"],
              ], [2.0 * inch, 1.15 * inch, 1.2 * inch, 2.7 * inch]),
              p("The flat result does not establish particle-size independence. It diagnoses a limitation in the cross-section-averaged calculation: complete burnout is reached for all distributions, leaving no resolved sensitivity. The extension is therefore documented as a failed predictive test rather than evidence that size does not matter.", "BodyCustom"), PageBreak()]

    # 13. Conclusions and run instructions.
    story += [p("13. Conclusions and reproducibility", "H1Custom"),
              p("1. The radial finite-volume transport and reaction bookkeeping conserve C, H, O, N and Ar to within 0.000003% on the finest grid.", "BodyCustom"),
              p("2. The 80x400 to 120x600 refinement changes outlet temperature by 9.1 K, carbon conversion by 1.28 percentage points, and the principal dry species by less than 0.81 percentage points. Peak-temperature convergence remains unknown because every grid reaches the 4000 K ceiling.", "BodyCustom"),
              p("3. The model predicts 53.52% carbon conversion and dry inert-free CO/H2/CO2/CH4 of 58.66/16.68/24.21/0.45 vol%, compared with 82% conversion and 51.1/24.7/23.6/0.3 vol% in the BYU experiment. It also predicts 3.88 vol% dry outlet O2.", "BodyCustom"),
              p("4. The present model is numerically conservative but physically underpredicts carbon conversion, underpredicts H2 and leaves oxygen at the outlet. Near-axis mean absolute errors are 12.81 pp for CO, 10.50 pp for H2 and 7.27 pp for CO2. Across radial probes, pooled mean errors are 8.54 pp for CO, 7.02 pp for H2 and 6.74 pp for CO2. Its 1400 K hot-start patch adds 19.35 kW, equal to 9.75% of coal HHV input. It should be treated as a reduced model with unresolved peak temperature, not a validated replacement for the reference CFD.", "BodyCustom"),
              p("5. The mass-weighted particle-size sweep is flat because the cross-section-averaged calculation saturates at 100% conversion. A credible size-effect result requires first fixing the chemistry and resolving finite char burnout.", "BodyCustom"),
              p("Run instructions", "H2Custom"),
              p("From the Batch18 folder: python scripts/run_tier1.py; python scripts/run_tier2.py; python scripts/run_grid_study.py; python scripts/sweep_particle_size.py; python scripts/digitize_radial_markers.py; python scripts/make_validation_plots.py; python scripts/make_radial_validation_plots.py. The detailed inputs are in case/byu_case.yaml. The radial-model run writes contours, area-average, near-axis and radial profiles, tier2_summary.csv and tier2_metrics.csv under report/. The validation scripts write the axial and radial comparison figures and error tables. The source code and run instructions are included in the Batch 18 source package.", "BodyCustom"),
              PageBreak()]

    # 13. References.
    story += [p("References", "H1Custom"),
              p("[1] Mularski, J. and Modlinski, N. (2021). Entrained-Flow Coal Gasification Process Simulation with the Emphasis on Empirical Char Conversion Models Optimization Procedure. Energies, 14(6), 1729. https://doi.org/10.3390/en14061729", "BodyCustom"),
              p("[2] Brown, B. W., Smoot, L. D., Smith, P. J. and Hedman, P. O. (1988). Measurement and Prediction of Entrained-Flow Gasification Processes. AIChE Journal, 34(3), 435-446. Original article PDF: https://electronicsandbooks.com/edt/manual/Magazine/A/AIChE%20Journal%20US/1988%20v.34/03%20%28353-526%29/435-446.pdf", "BodyCustom"),
              p("[3] Abani, N. and Ghoniem, A. F. (2013). Large eddy simulations of coal gasification in an entrained flow gasifier. Fuel, 104, 664-680. https://doi.org/10.1016/j.fuel.2012.06.006. Used only for the 13 mm primary and 28.6 mm secondary nozzle dimensions.", "BodyCustom"),
              p("[4] Channiwala, S. A. and Parikh, P. P. (2002). A unified correlation for estimating HHV of solid, liquid and gaseous fuels. Fuel, 81(8), 1051-1063. https://doi.org/10.1016/S0016-2361(01)00131-4.", "BodyCustom"),
              p("Reference values are transcribed from the cited publications. Figure 9 experimental markers are digitized values, not synthetic traces; their provenance and estimated uncertainty are recorded in data/validation/fig09_axial_centerline.csv. The model's 4000 K clipping, residual O2 and assumption-based radial mixing are disclosed because each affects interpretation.", "BodyCustom"),
              Spacer(1, 12), p("End of report", "SmallCustom")]
    doc.build(story)
    return out


# Presentation PDF helpers.
SLIDE_W, SLIDE_H = 960, 540


def slide_text(c, text, x, y, w, font_size=16, leading=None, color=INK, bold=False,
               align=TA_LEFT, max_height=240):
    font = "Helvetica-Bold" if bold else "Helvetica"
    style = ParagraphStyle("slide", fontName=font, fontSize=font_size,
                           leading=leading or font_size * 1.28,
                           textColor=color, alignment=align, spaceAfter=0)
    para = Paragraph(text, style)
    pw, ph = para.wrap(w, max_height)
    para.drawOn(c, x, y - ph)
    return ph


def draw_slide_title(c, title, number):
    c.setFillColor(NAVY)
    slide_text(c, title, 42, 500, 870, 27, leading=32, color=NAVY, bold=True)
    c.setFillColor(MID)
    c.setFont("Helvetica", 9)
    c.drawString(42, 22, "BATCH 18 | ME40249 | Sources: Mularski and Modlinski (2021), Brown et al. (1988)")
    c.drawRightString(916, 22, str(number))


def slide_image(c, path: Path, x, y, w, h):
    c.drawImage(str(path), x, y, width=w, height=h, preserveAspectRatio=True, anchor="c", mask="auto")


def slide_table(c, rows, x, y_top, col_widths, row_h=34, font_size=12):
    y = y_top
    for ri, row in enumerate(rows):
        xcur = x
        for ci, val in enumerate(row):
            ww = col_widths[ci]
            if ri == 0:
                bg, fg, bold = NAVY, WHITE, True
            else:
                bg = WHITE if ri % 2 else PALE
                fg, bold = INK, False
            c.setFillColor(bg)
            c.rect(xcur, y - row_h, ww, row_h, fill=1, stroke=0)
            slide_text(c, str(val), xcur + 7, y - 8, ww - 14, font_size,
                       leading=font_size * 1.18, color=fg, bold=bold, max_height=row_h - 6)
            c.setStrokeColor(colors.HexColor("#CFD8DD"))
            c.setLineWidth(0.4)
            c.rect(xcur, y - row_h, ww, row_h, fill=0, stroke=1)
            xcur += ww
        y -= row_h
    return y


def build_slides():
    out = PRESENTATION / "Batch 18 - Class Presentation.pdf"
    PRESENTATION.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out), pagesize=(SLIDE_W, SLIDE_H), pageCompression=1)
    c.setTitle("Batch 18 - Entrained-Flow Coal Gasification")
    c.setAuthor("ME40249 Batch 18")
    n = 1
    # Slide 1
    c.setFillColor(WHITE); c.rect(0, 0, SLIDE_W, SLIDE_H, fill=1, stroke=0)
    slide_text(c, "BATCH 18", 60, 448, 840, 17, color=TEAL, bold=True, align=TA_CENTER)
    slide_text(c, "Entrained-Flow Coal Gasification", 60, 402, 840, 31, leading=39,
               color=NAVY, bold=True, align=TA_CENTER)
    slide_text(c, "Reduced-order simulation of the BYU atmospheric reactor", 110, 350, 740, 17,
               color=MID, align=TA_CENTER)
    roster = "<br/>".join(f"{roll}  |  {name}" for roll, name in ROSTER)
    slide_text(c, roster, 180, 290, 600, 14, leading=22, color=INK, align=TA_CENTER)
    slide_text(c, "Selected paper: Mularski and Modlinski (2021), Energies 14(6), 1729", 70, 115,
               820, 12, color=MID, align=TA_CENTER)
    slide_text(c, "ME40249 | Gasification and Reforming Processes", 70, 88, 820, 11,
               color=MID, align=TA_CENTER)
    c.showPage(); n += 1

    # Slide 2
    draw_slide_title(c, "The assigned case", n)
    slide_text(c, "Atmospheric oxygen-blown BYU gasifier", 48, 452, 850, 17, color=TEAL, bold=True)
    slide_text(c, "A 0.20 m diameter x 1.80 m reactor processes 23.88 kg/h of Utah bituminous coal. The selected paper reports two coaxial feeds and a Rosin-Rammler coal-size distribution.", 48, 420, 850, 15, leading=21)
    slide_table(c, [["Feed", "Rate", "Inlet", "Composition"],
                    ["Primary", "26.24 kg/h", "400 K", "85% O2, 12.6% Ar, 2.4% H2O"],
                    ["Secondary", "6.62 kg/h", "473 K", "Steam"],
                    ["Coal", "23.88 kg/h", "-", "Utah bituminous, 1-85 um"]],
               48, 340, [110, 145, 90, 470], row_h=43, font_size=13)
    slide_text(c, "Paper: Mularski and Modlinski (2021), Table 3. Particle distribution: mean scale 36 um, spread 1.033.", 48, 122, 850, 12, color=MID)
    c.showPage(); n += 1

    # Slide 3
    draw_slide_title(c, "Utah coal composition", n)
    slide_text(c, "The source reports proximate analysis as received and ultimate analysis on a dry ash free basis. Oxygen is calculated by difference.", 48, 452, 850, 15, leading=21)
    slide_table(c, [["Proximate", "wt%"], ["Moisture", "2.40"], ["Volatile matter", "45.60"], ["Fixed carbon", "43.70"], ["Ash", "8.30"]],
               48, 395, [260, 170], row_h=39, font_size=14)
    slide_table(c, [["Ultimate, DAF", "wt%"], ["Carbon", "77.60"], ["Hydrogen", "6.56"], ["Nitrogen", "1.42"], ["Sulfur", "0.55"], ["Oxygen by difference", "13.87"]],
               492, 395, [270, 190], row_h=39, font_size=14)
    slide_text(c, "HHV input: 33.52 MJ/kg DAF estimated with the Channiwala-Parikh correlation. Particle density is a provisional assumption.", 48, 114, 850, 13, color=MID)
    c.showPage(); n += 1

    # Slide 4
    draw_slide_title(c, "Reduced model and reference CFD", n)
    slide_table(c, [["Model feature", "Reference CFD", "Batch 18 model"],
                    ["Flow", "2-D axisymmetric turbulence model", "Radial stream tubes, no momentum equation"],
                    ["Particles", "Trajectories and dispersion", "Coal stays in its inlet annulus"],
                    ["Heat", "Radiation and wall terms", "Adiabatic wall, no radiation"],
                    ["Coal chemistry", "C2SM/FG-DVC; char kinetics fitted to CBK/E and CBK/G", "C2SM Table 5 and BYU-fitted char parameters from Table 6; reduced gas chemistry"],
                    ["Mixing", "Turbulence-chemistry interaction", "Assumed radial diffusion, operator split"]],
               48, 445, [170, 350, 360], row_h=50, font_size=12)
    slide_text(c, "One solver workflow applies axial chemistry across radial annuli with species and heat exchange. The 1-D lanes describe the axial chemistry; the radial calculation resolves cross-stream variation. These describe spatial detail, not project phases. Momentum, particle trajectories and radiation are omitted. The 1400 K ignition patch adds 19.35 kW (9.75% of coal HHV input).", 48, 115, 850, 14, color=TEAL, bold=True)
    c.showPage(); n += 1

    # Slide 5
    draw_slide_title(c, "Temperature field", n)
    slide_image(c, FIG / "fig_contour_T.png", 48, 110, 864, 322)
    slide_text(c, "Peak reported at 4000 K, the solver's temperature-recovery ceiling. The true peak is unresolved. Outlet area-average temperature is 3556.7 K. The 1400 K hot-start patch supplies 9.75% of coal HHV input.", 48, 88, 860, 13, color=INK)
    c.showPage(); n += 1

    # Slides 6-8 contour pairs
    for title, left, right, note in [
        ("Species contours: CO and H2", "fig_contour_CO.png", "fig_contour_H2.png", "Local mole fractions in the radial-annulus model."),
        ("Species contours: CO2 and H2O", "fig_contour_CO2.png", "fig_contour_H2O.png", "Water measurements carry about +/-14% uncertainty in the source study."),
        ("Species contours: O2 and CH4", "fig_contour_O2.png", "fig_contour_CH4.png", "The model leaves 3.88 vol% dry O2 at the outlet."),
    ]:
        draw_slide_title(c, title, n)
        slide_image(c, FIG / left, 45, 185, 420, 165)
        slide_image(c, FIG / right, 495, 185, 420, 165)
        slide_text(c, left.replace("fig_contour_", "").replace(".png", ""), 55, 165, 400, 13, color=MID, align=TA_CENTER)
        slide_text(c, right.replace("fig_contour_", "").replace(".png", ""), 505, 165, 400, 13, color=MID, align=TA_CENTER)
        slide_text(c, note, 48, 105, 860, 14, color=INK)
        c.showPage(); n += 1

    # Carbon conversion contour
    draw_slide_title(c, "Fuel-carbon conversion field", n)
    slide_image(c, FIG / "fig_contour_carbon_conversion.png", 48, 150, 864, 322)
    slide_text(c, "The field uses the remaining char and raw coal in each annulus. Its near-uniform high values are another sign that this chemistry saturates locally.", 48, 122, 860, 13, color=INK)
    c.showPage(); n += 1

    # Axial profiles
    draw_slide_title(c, "Axial species and temperature profiles", n)
    slide_image(c, FIG / "fig_tier2_area_average_species.png", 48, 135, 425, 278)
    slide_image(c, FIG / "fig_tier2_area_average_temperature.png", 492, 135, 420, 278)
    slide_text(c, "Both plots show cross-sectional area averages, not centerline probe data.", 48, 110, 850, 13, color=MID)
    c.showPage(); n += 1

    # Slide 10 grid/verification
    draw_slide_title(c, "Numerical verification", n)
    slide_image(c, REPORT / "fig_grid_independence.png", 45, 230, 500, 210)
    slide_text(c, "120 x 600 grid", 590, 425, 300, 17, color=TEAL, bold=True)
    slide_text(c, "Element closure", 590, 390, 300, 14, bold=True)
    slide_text(c, "Maximum absolute C/H/O/N/Ar balance error: 0.0000021%", 590, 365, 300, 13)
    slide_text(c, "80 x 400 to 120 x 600", 590, 315, 300, 14, bold=True)
    slide_text(c, "Outlet T change: 9.1 K<br/>Conversion change: -1.28 percentage points<br/>Main dry gas changes: 0.65-0.80 percentage points", 590, 290, 300, 13, leading=19)
    slide_text(c, "The peak is capped on every grid, so peak-temperature convergence is unknown. Grid refinement does not establish physical accuracy.", 48, 170, 850, 14)
    c.showPage(); n += 1

    # Slide 11 validation
    draw_slide_title(c, "Comparison with BYU experiment", n)
    slide_table(c, [["Result", "Batch 18", "Experiment", "Difference"],
                    ["CO, dry inert-free", "58.66%", "51.1%", "+7.56 pp"],
                    ["H2, dry inert-free", "16.68%", "24.7%", "-8.02 pp"],
                    ["CO2, dry inert-free", "24.21%", "23.6%", "+0.61 pp"],
                    ["CH4, dry inert-free", "0.45%", "0.3%", "+0.15 pp"],
                    ["Carbon conversion", "53.52%", "82%", "-28.48 pp"]],
               48, 440, [235, 190, 190, 190], row_h=43, font_size=13)
    slide_text(c, "Interpretation", 48, 140, 850, 15, color=TEAL, bold=True)
    slide_text(c, "Element balance closes, but the model underpredicts conversion and H2 and leaves oxygen in the outlet. The next two slides compare near-axis and radial profiles with digitized experimental markers; the paper's Table 8 errors describe its own CFD.", 48, 112, 850, 14, leading=20)
    c.showPage(); n += 1

    # Slide 12: pointwise axial validation.
    draw_slide_title(c, "Near-axis comparison with centerline data", n)
    slide_image(c, REPORT / "fig_validation_axial_centerline.png", 38, 54, 620, 416)
    slide_text(c, "Mean / max absolute error (pp)", 674, 435, 250, 14, color=TEAL, bold=True)
    slide_text(c, "Species       Batch 18       Paper CFD", 674, 410, 250, 11, bold=True)
    slide_text(c, "CO            12.81 / 25.72    4.82 / 18.48", 674, 386, 260, 11, leading=17)
    slide_text(c, "H2            10.50 / 13.03    5.47 / 7.95", 674, 359, 260, 11, leading=17)
    slide_text(c, "CO2            7.27 / 14.46    4.72 / 10.15", 674, 332, 260, 11, leading=17)
    slide_text(c, "H2O           25.54 / 31.34    9.58 / 20.22", 674, 305, 260, 11, leading=17)
    slide_text(c, "Digitized experimental markers from Mularski & Modlinski (2021), Fig. 9. Errors are absolute composition differences in percentage points. H2O carries about +/-14% measurement uncertainty and is excluded from the paper's quality score.", 674, 260, 250, 12, leading=17)
    c.showPage(); n += 1

    # Radial validation at all eight axial probe stations (four shown).
    draw_slide_title(c, "Radial comparison with experimental probes", n)
    slide_image(c, REPORT / "fig_validation_radial_profiles.png", 32, 60, 600, 380)
    slide_text(c, "Pooled mean / max error (pp)", 690, 434, 235, 14, color=TEAL, bold=True)
    slide_text(c, "CO     8.54 / 24.22 (n=34)<br/>H2     7.02 / 15.33 (n=36)<br/>CO2   6.74 / 20.51 (n=35)", 690, 403, 235, 13, leading=22)
    slide_text(c, "All eight stations are scored; four are plotted. Orange markers were digitized from Figures 12-14 of Mularski & Modlinski (2021). Estimated digitization uncertainty: +/-0.001 m radius and +/-0.5 pp composition.", 690, 320, 235, 12, leading=17)
    slide_text(c, "H2O is excluded because the paper derives it by hydrogen balance. Errors are absolute mole-fraction differences in percentage points. The comparison shows meaningful local gaps; the reduced model does not reproduce all radial structure.", 690, 207, 235, 12, leading=17)
    c.showPage(); n += 1

    # Particle size extension
    draw_slide_title(c, "Particle-size distribution diagnostic", n)
    slide_image(c, REPORT / "fig_particle_size_sensitivity.png", 48, 220, 600, 255)
    slide_text(c, "Six mass-weighted Rosin-Rammler bins; scale diameter 20, 36, 60 um and spread 0.7, 1.033, 1.5. The cross-section-averaged calculation is flat: 100% conversion, 71.65% CGE and H2/CO = 0.451 in all cases.", 48, 194, 850, 14, leading=19)
    slide_text(c, "This diagnoses complete-burnout saturation in the cross-section-averaged calculation. It does not demonstrate that particle size has no effect. The reference study reports 83% conversion at 36 um mono and 77% for the full distribution, versus 82% measured.", 48, 116, 850, 13, leading=18)
    c.showPage(); n += 1

    # Conclusions
    draw_slide_title(c, "Conclusions", n)
    conclusions = [
        "The 120 x 600 model conserves tracked elements to about 0.0000021%.",
        "Outlet temperature is 3556.7 K; peak temperature reaches the 4000 K ceiling. The hot-start patch adds 9.75% of coal HHV input.",
        "Carbon conversion is 53.52%, 28.48 percentage points below the 82% experiment.",
        "Dry inert-free H2 is 16.68% versus 24.7% measured, and dry outlet O2 remains at 3.88%.",
        "Pooled radial mean errors are 8.54 pp for CO, 7.02 pp for H2 and 6.74 pp for CO2; substantial local gaps remain.",
        "The current particle-size sweep is inconclusive because the cross-section-averaged calculation saturates at 100% conversion.",
    ]
    y = 442
    for item in conclusions:
        y -= slide_text(c, item, 55, y, 850, 16, leading=23, color=INK) + 14
    slide_text(c, "Administrative check: roster and case are recorded; operating-condition uniqueness should be confirmed with the instructor.", 48, 72, 850, 13, leading=18, color=TEAL, bold=True)
    c.showPage()
    c.save()
    return out


if __name__ == "__main__":
    REPORT.mkdir(parents=True, exist_ok=True)
    report_path = build_report()
    slides_path = build_slides()
    print(report_path)
    print(slides_path)
