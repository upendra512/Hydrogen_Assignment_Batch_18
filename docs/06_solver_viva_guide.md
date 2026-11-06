# Batch 18 solver: plain-language walkthrough and viva guide

This guide follows `notebooks/Batch18_Full_Solver_Live_Demo.ipynb` from top to bottom. It explains the model, what the main code blocks calculate, what the figures mean, and how to answer likely questions. “Cell” numbers below are the notebook cell numbers, including Markdown cells.

## The solver in one sentence

The program predicts how coal, oxygen, and steam change into hot product gas as they travel down an atmospheric entrained-flow gasifier, using reaction balances, an enthalpy balance, a one-dimensional plug-flow calculation, and a reduced annular model for radial mixing.

## What physical problem is being modeled?

An **entrained-flow gasifier** carries small coal particles with a fast gas stream through a hot vessel. The coal heats up and releases **volatiles** (vapours and gases). The carbon-rich solid left behind is **char**. Volatiles react in the gas phase; char reacts at its surface. The desired product is **syngas**, mainly hydrogen (H₂) and carbon monoxide (CO), with water (H₂O), carbon dioxide (CO₂), methane (CH₄), and argon also present.

The modeled vessel is 0.20 m in diameter and 1.80 m long at about 1 atmosphere. The case feeds 23.88 kg/h as-received coal, an oxygen/argon/steam primary stream, and a steam secondary stream. “As received” includes moisture and ash. “DAF” means dry and ash free: the coal portion represented as reactive fuel after moisture and ash are excluded.

The **1-D** view tracks changes along the reactor axis `z`, treating each cross-section as mixed. The **radial 2-D** view tracks axial distance `z` and radius `r` using a set of annular lanes. It adds a simplified exchange of species and heat between neighboring lanes. It is not a full CFD solution: there is no solved velocity field, turbulence field, particle tracking, recirculation, or radiation.

## The core equations, in simple terms

### Gas material balance

For species *i*, `F_i` is its molar flow rate in mol/s, `A` is reactor cross-sectional area, and `R_i` is its net reaction source per gas volume. A plug-flow balance has the form:

`dF_i/dz = A × R_i + surface-reaction and devolatilization contributions`.

If a reaction makes the species, its contribution is positive; if it consumes it, negative. Integrating this equation from the inlet to the outlet predicts each species flow along the reactor.

### Solid balance

The solver also tracks unreacted raw DAF coal and char carbon. Their flow rates fall as coal devolatilizes and char reacts. Dividing a particle-time rate by the assumed particle velocity converts it into a change per metre of reactor length.

### Energy balance

The model assumes adiabatic operation along each stream lane: no heat leaves through the wall in the energy equation. The code calculates mixture enthalpy from chemical formation enthalpies and sensible heat. It finds the temperature that matches the target enthalpy. Thus temperature is recovered from energy conservation rather than integrated as a separate ODE variable.

An ignition enthalpy adjustment is applied at the inlet because the reduced 1-D model has no flame recirculation or radiation to ignite a cold stream. In the saved run this adjustment is 19.35 kW. It is an imposed model input, not a calculated burner or a physical source term resolved by the solver.

### Ideal gas and concentration

The solver estimates gas density with `rho = P × MW / (R × T)`. It estimates superficial gas speed as `u = gas mass flow / (rho × A)`. A species concentration is found from `C_i = F_i / (u × A)`. The code divides by 1000 to convert mol/m³ into kmol/m³ because its empirical gas-rate formulas use kmol/m³.

## Cell-by-cell walkthrough

### Cells 1–3: orientation

1. **Title and model boundary.** This cell says what case the notebook represents, how the demonstration is organized, and that the solver is a transparent reduced-order implementation. It does not reproduce the reference paper’s complete commercial CFD setup.
2. **Physical model map.** It introduces feed streams, atom bookkeeping, reactions, energy closure, axial integration, radial extension, and validation. It also explains that “1-D” and “radial 2-D” are two views in one solver walkthrough, not two project tiers.
3. **Imports and units.** NumPy handles arrays; SciPy provides numerical integration and solvers; Pandas reads tabular validation data; Matplotlib plots results. Internally, distances are metres, rates are seconds, mass is kilograms, pressure is pascals, temperature is kelvin, and energy is joules. Gas feeds are mol/s.

### Cell 4: imports, constants, and data location

The code imports the libraries and defines `R`, the universal gas constant, `T_REF`, the enthalpy reference temperature, and `P`, the pressure. `Path.cwd()` checks the current folder and its parents to locate the `Batch18/case/byu_case.yaml` file. This makes the notebook less dependent on the folder from which it was opened. It prints the data folder it found.

### Cells 5–7: case data and feed conversion

5. **Case description.** The text introduces the gasifier geometry, feed streams, coal properties, and the representative 36 μm particle diameter.
6. **Input data and species table.** The `case` dictionary stores geometry, mass rates, temperatures, compositions, coal analyses, and particle assumptions. The `species` table stores each gas’s molecular weight, formation enthalpy, heat capacity, and number of atoms of each element. `GAS` lists species; `IDX` maps a species name to its location in the state vector. The code calculates ash, moisture, DAF coal, normalized DAF elemental fractions, and vessel area. `stream_moles()` converts a gas mass flow into species molar flows using its mean molecular weight. Moisture in the coal is added as steam. The primary and secondary inlet temperatures are combined using a mass-weighted approximation.
7. **Why molar flow?** Reaction equations count molecules and atoms, so mol/s makes stoichiometric balances direct. The main saved inlet values are about 0.190 mol/s O₂, 0.0281 mol/s Ar, and 0.116 mol/s H₂O (including the coal moisture contribution).

**Terms:** A **mole** is a fixed count of molecules. **Molecular weight** converts mass to moles. **Mole fraction** is the fraction of gas molecules that belong to one species. **Proximate analysis** divides as-received coal into moisture, volatile matter, fixed carbon, and ash. **Ultimate analysis** gives elemental percentages; the DAF analysis excludes moisture and ash.

### Cells 8–9: heating value and enthalpy

8. The text explains the coal heating-value estimate and the constant-heat-capacity approximation.
9. `h_species()` calculates a gas species’ enthalpy at temperature `T`: formation enthalpy at the reference state plus `cp × (T − T_REF)`. `hhv_channiwala()` estimates the coal’s higher heating value from its elemental mass percentages. `coal_formation_enthalpy()` backs out a DAF coal formation enthalpy using combustion products and the estimated HHV. The saved estimate is 33.52 MJ/kg DAF.

**HHV** is the higher heating value, including the heat recoverable if product water condenses. **Formation enthalpy** is the reference energy associated with forming a substance from its elements. **Heat capacity `cp`** measures energy needed to raise temperature. The code holds each gas `cp` constant; this is transparent but approximate at gasifier temperatures.

### Cells 10–11: coal devolatilization

10. The text introduces the competing two-step model, called C2SM. Raw coal reacts through two parallel Arrhenius pathways; each pathway has a rate constant and a volatile yield. The notebook uses the reported parameters but does not run the paper’s FG-DVC fitting software. It also explains that element balances alone cannot uniquely determine the assumed five volatile gas species, so the code states allocation assumptions and sends excess volatile carbon to a solid soot/tar surrogate.
11. `A1`, `E1`, and `alpha1` and their pathway-2 counterparts are frequency factors, activation energies, and volatile yields. `devol_rates(m_raw, Tp)` calculates the volatile-release and char-formation rates. Each pathway follows `k = A × exp(−E/(R × Tp))`; higher particle temperature generally speeds reaction. `volatile_partition()` allocates coal C, H, O, and N to CO, CO₂, CH₄, H₂, H₂O, and N₂ under the declared split rules. Any leftover carbon is stored as soot surrogate. The printed 84.2% volatile / 15.8% char split is an example at 1800 K, not a universal fixed yield.

**Arrhenius law:** `A` is the pre-exponential factor, `E` the activation energy, `R` the gas constant, and `Tp` the assumed particle temperature. The exponential term describes how the fraction of sufficiently energetic reactions changes with temperature. **Underdetermined** means there are more unknown gas amounts than independent element equations; extra assumptions are needed to choose one allocation.

### Cells 12–13: char reactions

12. The text describes three reactions at the char surface and how intrinsic reaction and external gas-film diffusion resistances are combined.
13. `char_rx` stores parameters and stoichiometry for:

- `C + ½ O₂ → CO` (oxidation, releases heat)
- `C + CO₂ → 2 CO` (Boudouard gasification, absorbs heat)
- `C + H₂O → CO + H₂` (steam gasification, absorbs heat and forms H₂)

`char_rate()` calculates an effective rate. Intrinsic surface chemistry has coefficient `ks`; transport through the gas film has coefficient `kd`. The combination `keff = kd × ks / (kd + ks)` represents two resistances in series: if either step is slow, the overall step is slow. `p_ox` is the oxidizing species’ partial pressure; `area` is available particle surface area per axial length in the solver. The particle surface area is held fixed as char burns.

**Heterogeneous** means a reaction between different phases: solid char and gas. **Homogeneous** means a reaction within the gas phase. **Partial pressure** is the pressure contribution of one gas species, approximated as its mole fraction times total pressure.

### Cells 14–15: gas-phase chemistry

14. The text introduces four overall gas reaction expressions and clarifies that they are global empirical rates, not an elementary mechanism or the paper’s turbulence-chemistry closure.
15. `gas_rx` stores the reaction rate constants, activation energies, concentration orders, stoichiometric coefficients (`nu`), heat of reaction (`dH`), and whether the reaction is reversible. The four reactions are CO oxidation, H₂ oxidation, water-gas shift (WGS), and steam methane reforming. `gas_sources()` calculates a rate for each reaction and adds production/consumption to each species. For WGS, `Q` is the reaction quotient and `Kp` is the equilibrium constant correlation; the multiplier `1 − Q/Kp` makes the net rate go forward or reverse depending on how the current composition compares with equilibrium.

**Reaction order** is the exponent applied to a species concentration in an empirical rate expression. **Stoichiometric coefficient** is the amount of a species consumed or produced by one reaction event; negative `nu` means consumed, positive means produced. **Equilibrium** is the composition at which forward and reverse rates balance.

### Cells 16–20: one-dimensional plug-flow solver

16. The text introduces the axial balances and assumptions: plug flow, ideal gas, one shared gas/particle temperature, and no explicit turbulence or recirculation field.
17. This is the main 1-D implementation:

- `N_GAS`, `I_CHAR`, and `I_RAW` define the positions of gas flows, char flow, and raw-coal flow in one numerical state vector.
- `stream_enthalpy()` sums sensible and formation enthalpy for the gas and sensible enthalpy for char, raw coal, and inert ash.
- `temperature_from_enthalpy()` uses Brent’s bracketed root solver to find the temperature matching a target enthalpy. It searches between 280 K and 4000 K. If no root is bracketed, the code returns the closer endpoint; reaching 4000 K therefore means the answer hit the model’s numerical ceiling.
- `rhs(z, state, H0, local_case)` is the right-hand side of the ODE: it calculates derivatives of every flow with respect to axial distance `z`. It clips negative trial values to zero, recovers temperature, calculates gas composition, mean molecular weight, density, mass flow, velocity, and concentration, then adds gas reaction sources. It adds raw-coal devolatilization, the resulting char, volatile products, soot surrogate, and the three char-surface reactions.
- `solve_1d()` forms the inlet state, starts all DAF coal as raw coal, applies the ignition enthalpy adjustment at the configured 1400 K, and calls SciPy `solve_ivp()` with `method="LSODA"`. It evaluates the solution at 180 axial positions, then returns temperatures, species flows and mole fractions, solid flows, enthalpy, and case information.

**ODE** means ordinary differential equation. Here, the independent variable is distance down the reactor, not time. The underlying particle reaction rates are time-based; velocity converts those rates into axial change. **Plug flow** assumes material progresses down the reactor without axial back-mixing. **LSODA** automatically switches numerical methods when the system becomes stiff. **Stiff** means some reaction processes change much faster than others, making a simple large integration step unstable or inaccurate. `rtol` and `atol` are numerical error tolerances; `max_step` caps the axial step size.

18. Explains the ignition patch. If asked, say: “We impose inlet enthalpy corresponding to 1400 K because this reduced model has no flame stabilization physics. It makes the calculation ignite; it is an explicit assumption and a major uncertainty.”
19. Introduces the plots from the 1-D solution.
20. Plots temperature, wet gas mole fractions, and the remaining raw DAF coal and char as fractions of inlet DAF coal. “Wet” means the mole fraction includes water vapour. Read each x-axis as distance from reactor inlet toward outlet. In the saved run, the reported 4000 K peak is the root-finding ceiling, not a resolved physical peak; the exit temperature is about 3029 K. The 1-D result reaches 100% carbon conversion, which is a warning that this reduced setup over-consumes its modeled solid carbon for this case. Do not present that as proof of complete real-world conversion.

### Cells 21–22: conservation and performance indicators

21. The text explains atom balances, carbon conversion, and cold-gas efficiency.
22. `atom_flows()` counts atoms in the outlet gases plus carbon in char and elements remaining in raw coal. The table compares input and output C, H, O, N, and Ar. The saved 1-D balance errors are near numerical zero, showing that bookkeeping is internally consistent. Then carbon conversion is calculated as one minus the fraction of initial fuel carbon left in solids. The cold-gas efficiency numerator uses the stated molar lower heating values for H₂, CO, and CH₄; the denominator is the coal HHV input used in this project calculation. The saved value is 71.7% on that stated basis.

**Conservation check is not validation.** A model can conserve atoms perfectly and still predict the wrong temperature or gas composition if its rates or assumptions are inaccurate. Conversion means carbon no longer counted in the remaining raw coal or char; it is not itself a measurement of syngas quality.

### Cells 23–26: radial annular calculation

23. Explains how the radial cross-section is divided into annuli and how primary and secondary inlet streams are initially distributed. It calls the radial mixing closure an assumption, not an experimental measurement.
24. This is the radial extension:

- `NR` is the number of annuli; `NZ` is the number of axial stations. The demonstration defaults to 12 × 100.
- `BACKGROUND_SPREAD` lets some inlet flow spread across the full cross-section; the rest is concentrated in the injector’s core or annulus.
- `MIXING_COEFFICIENT`, `SCHMIDT_T`, `PRANDTL_T`, `MOLECULAR_D`, and `D_MAX` set the assumed radial species/heat diffusivity closure and its bounds.
- `radial_weights()` calculates normalized inlet weights so the total allocated primary and secondary flow sums to the original feed.
- `make_annular_cases()` divides the cross-section into concentric annuli, allocates coal and inlet gases to each lane, and sets each lane’s local cross-sectional area and inlet temperature.
- `lane_properties()` calculates composition, temperature, density, and velocity for one annulus.
- `solve_radial()` first runs the same 1-D chemistry in each lane to provide its baseline axial chemistry changes. At each axial station, it applies those changes, then solves a conservative implicit finite-volume exchange of species and heat between adjacent annuli. “Operator split” means chemistry and radial transport are applied as separate numerical substeps. This is a reduced stream-tube approximation, not fully coupled CFD.
- It reconstructs fields of temperature and gas mole fractions, integrates lane flows, checks radial feed normalization and atom balance, and prints carbon conversion. In the saved run, the radial calculation uses 12 annuli × 100 stations, reaches the 4000 K ceiling somewhere in the field, and reports about 59.9% carbon conversion. This difference from the 1-D run demonstrates sensitivity to the radial treatment; neither number should be presented as a validated measurement.

25. Tells the reader how to interpret the contours: primary feed begins oxygen-rich; secondary feed begins steam-rich; mixing assumptions shape the radial gradients.
26. Plots the temperature, H₂, and CO fields versus `z` and `r`. The color bar shows the value; the vertical axis is radius in centimetres; the horizontal axis is axial distance in metres. The temperature plot marks the 4000 K cap, which must be disclosed if it appears.

**Finite volume** means conservation is applied to small control volumes—in this case annular lanes—with fluxes between neighboring cells. **Diffusion** is modeled exchange down a concentration or temperature gradient. **Schmidt number** relates momentum diffusivity to species diffusivity; **Prandtl number** relates momentum diffusivity to thermal diffusivity. Their values here are closure assumptions.

### Cells 27–28: comparison with experimental markers

27. Explains that the CSV measurements are approximate markers digitized from published graphs, not raw instrument files or the paper’s CFD curves. It defines absolute error in percentage points and notes digitization uncertainty.
28. Loads the axial and radial CSVs, plots model against digitized markers, interpolates the model to the marker coordinates, and calculates mean and maximum absolute error. The saved outputs report axial mean absolute errors of about 9.5 percentage points for CO, 9.6 for H₂, and 7.6 for CO₂. The radial mean errors are about 7.2, 6.8, and 6.5 percentage points, respectively. These mismatches are much larger than the stated marker digitization uncertainty, so describe the comparison honestly: it is a validation diagnostic that exposes model error, not proof of close agreement.

**Interpolation** estimates a value between two grid points. **MAE** is mean absolute error: average of the absolute differences between model and marker. A **percentage point** is the direct difference between percentages; 12% − 10% = 2 percentage points.

### Cells 29–30: particle-size distribution diagnostic

29. Explains a Rosin–Rammler size distribution and clearly says it is a diagnostic, not a size-resolved gasifier calculation.
30. Builds diameter bins from 1 to 85 μm. The cumulative formula `F(d) = 1 − exp[−(d/ds)^q]` estimates the mass fraction below diameter `d`; subtracting adjacent cumulative values gives each bin fraction. It plots the bins and estimates surface area per mass using spherical particles. The saved diagnostic estimates 425 m²/kg over the truncated size range, compared with 128 m²/kg for a single 36 μm sphere size. It does not feed those bins into the reaction solver; a true size-resolved calculation would need a separate history and reaction calculation for each class.

### Cells 31–33: limitations and questions

31. Lists the assumptions and limitations to disclose: ideal gas, constant heat capacities, omitted sulfur chemistry, inert ash, assumed volatile split, pure-carbon char, fixed particle surface area, one representative size, global gas kinetics, one shared gas/particle temperature, ignition patch, simplified radial transport, 4000 K numerical cap, and the suspicious 100% 1-D carbon conversion.
32. Provides short viva answer cues. Use these as a prompt; explain the physical meaning rather than memorizing wording.
33. Empty cell; it has no computation or explanation.

## A ready-to-say three-minute explanation

“Our project models an atmospheric entrained-flow coal gasifier. Coal particles and oxygen/steam enter a 0.2-m-diameter, 1.8-m-long reactor. The goal is to estimate how temperature and gas composition change along the reactor, especially the hydrogen and carbon monoxide in syngas.

We store gas flow as mol/s because chemical reactions conserve molecules and atoms. Our state tracks each gas species, unreacted dry-ash-free coal, and char carbon. First, raw coal devolatilizes through two competing Arrhenius pathways. The volatile products are assigned to gases using explicit element-based assumptions; excess carbon remains in a soot/tar surrogate. Then char reacts with oxygen, carbon dioxide, and steam. In the gas phase we include CO oxidation, H₂ oxidation, water-gas shift, and methane reforming.

At every axial step, the solver calculates gas composition, density, velocity, and concentration. It integrates the species and solid balances with LSODA. Temperature is recovered from an adiabatic enthalpy balance using a bracketed root solver. We add an explicit ignition enthalpy adjustment because our reduced equations do not resolve flame recirculation or radiation.

The one-dimensional calculation assumes a cross-section-averaged plug flow. To show radial differences, we split the reactor cross-section into annuli, distribute the primary and secondary streams according to their injector locations, and add assumed radial exchange of species and heat. This gives a 2-D field, but it is a reduced stream-tube model rather than full CFD.

We check C, H, O, N, and Ar atom balances and compare predictions with digitized experimental markers. Atom balance closes closely, but that alone does not prove the physics is accurate. Our model has visible limitations: the temperature reaches the 4000 K numerical ceiling, the 1-D result predicts 100% carbon conversion, and validation errors are several percentage points. We therefore present the solver as a transparent engineering model and use these results to identify where better kinetics, particle tracking, thermodynamics, and mixing data are needed.”

## Likely professor questions and strong short answers

**Why are you using a reduced solver instead of reproducing the paper’s CFD?**  
“The assignment implementation is a transparent model we can explain and run. Full CFD also needs flow and turbulence fields, particle tracking, radiation, chemistry coupling, and specialized setup. We use the reported case and selected fitted parameters, but we do not claim to reproduce the paper’s complete Fluent calculation.”

**What is the most important assumption?**  
“Several assumptions matter, especially the imposed ignition enthalpy, volatile-product allocation, char kinetics and particle size, and radial mixing closure. The 4000 K temperature ceiling and 100% 1-D carbon conversion show that these predictions require caution.”

**What does the 4000 K result mean?**  
“It is the upper bound of the enthalpy root-search bracket. Since the computed temperature hits that bound, the peak is unresolved. We do not report it as a physical peak temperature.”

**If atom balance is excellent, why are you concerned about accuracy?**  
“Atom balance checks accounting. It does not check whether the rate laws, temperature, mixing, or assumptions match the real reactor. A model can conserve atoms and still have poor predictive accuracy.”

**Why does the 1-D conversion differ from the radial conversion?**  
“The radial solver starts from annular lanes with different inlet streams and applies a sequence of local chemistry increments and radial mixing steps. That reduced operator-split treatment changes local concentrations and conversion. The difference is evidence of model sensitivity and should be investigated, not hidden.”

**Where does H₂ come from?**  
“It can be released from volatile matter, made by char–steam gasification, produced by water-gas shift, and formed in methane reforming. Which pathway dominates depends on the predicted local temperature and composition.”

**What is the difference between the 1-D and radial calculations?**  
“The 1-D model uses one cross-section-averaged stream at each axial position. The radial model uses annular lanes to represent the separate coaxial feeds and exchanges species and heat between lanes. It still does not solve momentum or turbulence.”

**What does LSODA do?**  
“It integrates the ordinary differential equations along reactor length and switches between non-stiff and stiff numerical methods. That helps when reaction timescales differ greatly.”

**What is your validation result?**  
“We compare model predictions with approximate digitized CO, H₂, and CO₂ markers. In the saved run the mean absolute errors are around 6.5–9.6 percentage points depending on species and location. This is a useful diagnostic, but it shows noticeable mismatch rather than close validation.”

**What would you improve first?**  
“First I would resolve the 4000 K enthalpy-bracket issue and investigate the 100% 1-D carbon conversion. Then I would perform sensitivity studies on the ignition input, particle size, volatile split, and radial mixing, and improve thermophysical properties and particle histories using relevant measurements.”

## Key vocabulary to remember

| Term | Plain meaning |
|---|---|
| State vector | The list of variables whose values the solver advances: gas flows, raw coal, and char. |
| RHS / `rhs()` | The derivatives that tell the ODE solver how each state variable changes with axial distance. |
| Mole fraction | Moles of one gas divided by total gas moles. |
| Stoichiometry | The molecule-counting ratios in a balanced reaction equation. |
| Kinetics | Equations describing how fast reactions occur. |
| Enthalpy | A flow’s thermal plus chemical energy accounting quantity. |
| Adiabatic | No heat transfer through the system boundary in the energy balance. |
| Stiff ODE | An equation system with widely separated rates or timescales. |
| Annulus | A ring-shaped section between two radii. |
| Closure | A practical assumption used to represent unresolved physics, such as turbulent mixing. |
| Validation marker | A value estimated from an experimental plot for model comparison. |
| Sensitivity analysis | Changing an assumed input systematically to see how much predictions change. |

## Presentation reminders

- Explain the physical process first; then show the state variables, reaction models, energy closure, integration, radial extension, and checks.
- Call the reported model a reduced-order implementation. Be specific about the parts it includes and does not include.
- Say “the code closes the atom balance” rather than “the solver is fully validated.”
- Explicitly identify 4000 K as a numerical ceiling and 100% 1-D carbon conversion as a model warning.
- Treat the radial maps and efficiency as model predictions, not experimental facts.
