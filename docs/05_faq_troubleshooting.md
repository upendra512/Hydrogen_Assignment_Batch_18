# Frequently asked questions and result checks

## Why are elemental balances close to zero but the prediction still differs?

An element balance checks whether tracked atoms are conserved by the code. It
does not check whether reaction rates, mixing, heat transfer, or assumptions
match the real reactor. This model conserves C/H/O/N/Ar closely, but predicts
53.52% carbon conversion against 82% measured and leaves 3.88 vol% dry oxygen
at the outlet.

## Why does the peak temperature show 4000 K?

Every grid reaches the model's temperature-recovery ceiling. The true peak is
therefore unresolved. The report also records the 1400 K hot-start patch,
which adds 19.35 kW (9.75% of the coal HHV input). Treat the peak and hot-start
assumption as model limits, not validated predictions.

## Why does Tier 1 convert all of the carbon in the particle-size sweep?

The Tier 1 chemistry burns out all the char in every tested case. The flat
particle-size curves diagnose that saturation; they do not show that particle
size has no physical effect. The Tier 2 result is the project's reduced
reactor-field calculation.

## What exactly is compared in the profile figure?

Orange squares are experimental centerline markers digitized from Figure 9 of
Mularski and Modlinski (2021). The model curve is sampled at its first annulus
center, r = 0.83 mm, and is a near-axis proxy. The plotted differences are
absolute composition differences in percentage points. H2O is shown with the
paper's approximately +/-14% uncertainty caveat.

## What does the radial comparison add?

Figures 12-14 show measured radial profiles at eight axial stations. Their
orange markers have been digitized and compared with Tier 2 profiles at the
same stations. The pooled mean absolute differences are 8.54 percentage
points for CO, 7.02 for H2, and 6.74 for CO2. These values are approximate
because they were digitized from plotted markers, not raw probe files. H2O is
not scored because the reference paper derives it by hydrogen balance.

## Where are the required outputs?

The rubric checklist maps the six assignment results to the report. The report
includes feed composition, species profiles and contours, temperature
results, experimental comparisons, and conclusions. The 15-slide PDF follows
the same sequence and includes all five group members.

## What remains before course submission?

The local PDFs and source archive are prepared. The user-supplied
selection sheet does not provide enough operating-condition detail to verify
topic uniqueness. The instructor must confirm uniqueness and the late
submission procedure. Upload to the course Drive remains to be done.
