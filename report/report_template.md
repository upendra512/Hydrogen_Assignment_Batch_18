---
# Starter outline only. The completed submission is `Batch 18.pdf` in this folder. This template still contains unfilled sections and is not the final report.

title: "Eulerian Simulation of Coal Gasification in an Entrained-Flow Reactor"
subtitle: "ME40249 — Introduction to Hydrogen Energy and Utilization"
batch: "Batch 18"
authors: "<name 1>, <name 2>, <name 3>, <name 4>"
rolls: "<roll 1>, <roll 2>, <roll 3>, <roll 4>"
date: "<submission date>"
---

<!--
HOW TO USE THIS TEMPLATE
========================
Every section carries (a) what it must contain, (b) roughly how long, and
(c) which required result it satisfies. Delete the HTML comments as you fill
each section in.

WRITE IT FROM WEEK 4, NOT AFTER. The report lead drafts sections 2 and 3 while
the solver lead is still building Tier 2. A report written in the last four
days always reads like one.

Submit as `Batch 18.pdf`. Convert with:
    pandoc report_template.md -o "Batch 18.pdf" --pdf-engine=xelatex --toc
-->

## Abstract

<!-- 150-200 words, written LAST. One sentence each on: the case, the model,
the validation, the headline numbers, and the one thing you found that nobody
asked you for (the particle-size study). -->

---

## 1. Introduction

<!-- ~1 page. -->

### 1.1 Why gasification, and why entrained flow
<!-- Gasification converts any carbon-bearing solid into syngas. Entrained
flow is the high-temperature, short-residence-time variant: fine particles
carried with the gas, ~1500-2000 K, tar-free product. Cite the course
material and one or two reviews. -->

### 1.2 Objective
<!-- State it plainly: simulate the BYU entrained-flow gasifier, validate
against published experimental data, and quantify the effect of particle size
distribution on conversion. -->

### 1.3 Scope and what this work is not
<!-- IMPORTANT. State here that you are simulating the same case as Mularski &
Modlinski (2021) with a deliberately simpler model, and comparing against the
same experimental data - NOT reproducing their model. Getting this on page one
frames everything that follows. -->

---

## 2. Case description
<!-- REQUIRED RESULT 1: feedstock/feed composition and major species. ~1 page. -->

### 2.1 Reference paper and reactor
<!-- Full citation. Reactor: BYU entrained-flow, 0.2 m dia x 1.8 m,
atmospheric, oxygen-blown. The reference reports 23.88 kg/h of Utah coal.
State the operating conditions you are reproducing, explicitly - this is
required by the assignment brief. -->

### 2.2 Fuel
<!-- Table: proximate (as received) and ultimate (dry ash free) analyses of
Utah bituminous coal. Oxygen is by difference from the paper's listed CHNS.
Particle size: Rosin-Rammler, 1-85 um, mean parameter 36 um, spread 1.033. -->

| | Proximate (wt %, as received) | | Ultimate (wt %, DAF) |
|---|---|---|---|
| Moisture | 2.40 | C | 77.60 |
| Volatile matter | 45.60 | H | 6.56 |
| Fixed carbon | 43.70 | N | 1.42 |
| Ash | 8.30 | S | 0.55 |
| | | O* | 13.87 |

*Oxygen calculated by difference from the reported DAF C, H, N, and S values.

### 2.3 Inlet streams

| Stream | Mass flow | T | Composition (mol %) |
|---|---|---|---|
| Primary | 7.289 g/s | 400 K | O₂ 85.0, Ar 12.6, H₂O 2.4 |
| Secondary | 1.839 g/s | 473 K | H₂O 100 |

---

## 3. Model formulation
<!-- ~3 pages. The section an examiner reads to decide whether you understand
what you built. -->

### 3.1 Governing equations
<!-- The parabolised axisymmetric transport equation. Explain what
parabolising means and WHY it is justified here (directional flow, no
recirculation in the bulk) and where it is not (the burner near-field). -->

### 3.2 Devolatilisation
<!-- C2SM. Give the equations, the rate constants you chose, and the citation.
Then the volatile composition: state that the element balance is
underdetermined, name your two closure assumptions explicitly, and explain the
surplus-carbon/tar issue. Reproduce the arithmetic - ~50 mol C, ~120 mol H,
~14 mol O per kg VM - it shows you understand rather than copied. -->

### 3.3 Char conversion
<!-- Three surface reactions, the kinetic/diffusion combination, the two
limiting regimes and where each applies along the reactor. -->

### 3.4 Homogeneous chemistry
<!-- Four global reactions. Emphasise the reversible water-gas shift and its
role in setting the final H2:CO ratio. Link back to the SMR tutorial. -->

### 3.5 Turbulence and radiation
<!-- What you used, and what you did not. Honesty here is cheap and it
pre-empts the obvious question. -->

### 3.6 Numerical method
<!-- Marching scheme, implicit radial diffusion, the enthalpy-conservation
approach to temperature and why it is more stable than integrating dT/dz. -->

### 3.7 Differences from the reference model
<!-- A TABLE. Their sub-model vs yours, row by row. This single table is
probably the highest marks-per-square-inch in the whole report. -->

---

## 4. Numerical verification
<!-- Short, ~0.5 page, but do not skip it. Verification is not validation and
examiners notice when you know the difference. -->

- Element balance closure (C, H, O, N)
- Pure-diffusion test against the analytical error-function solution
- Grid independence at three resolutions

---

## 5. Results
<!-- ~4 pages. The core. -->

### 5.1 Reactor structure
<!-- Walk the reader down the reactor through the five zones: lean, flame,
post-flame, reforming. Use the axial temperature and species plots. This
narrative is what turns a set of figures into a result. -->

### 5.2 Species distribution
<!-- REQUIRED RESULT 2. Axial profiles of CO, H2, CO2, H2O, O2, CH4. -->

### 5.3 Species contours
<!-- REQUIRED RESULT 3 - the one that decides the grade. Contours of each
major species on a consistent colour scale. Say what each one shows; do not
just paste six pictures. -->

### 5.4 Temperature field
<!-- REQUIRED RESULT 4. Contour plus centreline profile. Discuss the peak and
where it sits relative to the paper's ~3000 K. -->

### 5.5 Performance metrics
<!-- Exit composition, carbon conversion, cold-gas efficiency, in one table
against the paper's values. -->

---

## 6. Validation
<!-- REQUIRED RESULT 5. ~2 pages. -->

### 6.1 Axial comparison
<!-- Your model, the experimental points, and the paper's model curve - all
three on one plot per species. -->

### 6.2 Radial comparison
<!-- The eight axial stations. Most groups will have nothing like this. -->

### 6.3 Error quantification

| Species | This work, avg % | This work, max % | Mularski avg % | Mularski max % |
|---|---|---|---|---|
| CO | | | 4.82 | 18.48 |
| H₂ | | | 5.47 | 7.95 |
| CO₂ | | | 4.72 | 10.15 |

<!-- State why H2O is excluded: the paper does the same, because the
experimental H2O carries +/-14% uncertainty from the char ash analysis. -->

### 6.4 Discussion of discrepancies
<!-- THE MOST IMPORTANT SUBSECTION IN THE REPORT. For each significant
disagreement, name the specific simplification responsible and argue the
direction of the effect. "Our peak temperature is X K higher because we
neglect radiative loss and use Arrhenius rates without an eddy-dissipation
limit, both of which over-predict heat release in the flame zone."

Do not apologise. Attribute. -->

---

## 7. Effect of particle size distribution
<!-- THE DIFFERENTIATOR. ~1.5 pages. Nobody asked for this. -->

<!-- Frame it from the paper's own limitation: CBK/E and CBK/G handle only
monodisperse particles, so the optimised parameters apply at the 36 um mean
alone, and the authors state that a polydisperse treatment would improve
accuracy. You are addressing a documented open gap in the paper you validated
against - say exactly that.

Sweep the Rosin-Rammler mean diameter and spread parameter. Plot carbon
conversion, exit H2:CO and cold-gas efficiency against each. Explain the
result through the kinetic/diffusion regime argument: smaller particles have
more surface area per unit mass and shift the balance between the two limits. -->

---

## 8. Conclusions
<!-- REQUIRED RESULT 6. Numbered, specific, quantitative. No new material.
Each conclusion should be a sentence someone could disagree with - "the model
predicts exit CO within 12% of experiment" is a conclusion; "the model
performed well" is not. -->

---

## References
<!-- Mularski & Modlinski (2021) Energies 14(6) 1729 is reference 1.
Brown et al. (1988) AIChE J 34(3) for the experimental data.
Every rate constant needs a citation. -->

## Appendix A — Model parameters
<!-- Every rate constant, with its source. -->

## Appendix B — Code
<!-- Repository structure and how to run it. The Drive upload has the code
itself. -->
