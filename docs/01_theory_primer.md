# Theory primer: entrained-flow coal gasification

## Gasification in simple terms

Burn coal with plenty of oxygen and most of its carbon becomes carbon dioxide.
Gasification uses less oxygen. The goal is to convert coal into a fuel-rich gas
containing mainly carbon monoxide (CO) and hydrogen (H2), called synthesis gas
or syngas. Some coal is oxidized to provide heat; steam and carbon dioxide
also react with the remaining carbon.

Examples of the main reactions are:

```text
C + 1/2 O2  -> CO       partial oxidation; releases heat
C + H2O     -> CO + H2  steam gasification; absorbs heat
C + CO2     -> 2 CO     Boudouard reaction; absorbs heat
CO + H2O    <-> CO2 + H2 water-gas shift
```

The real reactor has several reactions at once. Feed composition, temperature,
mixing, and the rate at which char reacts all affect the final gas.

## Why entrained flow is different

Finely ground coal enters with fast-moving gas. The particles travel through
the reactor while heating, releasing volatile matter, and leaving char behind
to react. Conditions change with distance from the burner and with radius, so
measurements can vary throughout the vessel.

The selected case is the atmospheric BYU gasifier, using Utah bituminous coal.
The paper by Mularski and Modlinski (2021) describes the operating case and
compares gasification models. Brown et al. (1988) report experimental
composition and probe measurements used for comparison.

## What the selected paper contributes

The reference paper examines how char-conversion models and their parameters
affect predicted coal conversion and syngas. It considers more detailed
reactor descriptions than the simplified calculations in this project. In
plain language: even when the feed is known, the predicted result depends
strongly on how the model represents reactions and transport.

## What happens to a coal particle

1. **Heating and drying:** moisture leaves as the particle warms.
2. **Devolatilization:** the coal releases gases and heavier volatile
   material.
3. **Gas reactions:** volatile gases react with oxygen, steam, and one another.
4. **Char conversion:** the remaining carbon reacts with oxygen, steam, and
   carbon dioxide.

The current code simplifies several steps. Moisture is released at the inlet,
the volatile gas split uses stated assumptions, and the same bulk chemistry is
used across the radial cells. Particle trajectories and separate particle
temperatures are not resolved.

## Why there are two model tiers

**Tier 1** assumes one uniform cross-section and follows gas composition and
temperature along the reactor. It is useful for checking chemistry and
balances, but it cannot produce radial contours.

**Tier 2** divides the reactor radius into annular cells and marches them
downstream. Primary and secondary feeds enter in different radial regions, and
neighboring annuli exchange species and enthalpy. This produces approximate
contours and area-average profiles.

Tier 2 is not a full CFD solution. It has no momentum equation, turbulence
field, radiation model, recirculation, or Lagrangian particle tracking. Those
omissions help explain why good element conservation does not guarantee close
agreement with experiment.

## How to interpret the comparisons

The outlet comparison uses dry, inert-free product gas. The profile comparison
uses experimental centerline markers digitized from Figure 9 and model values
from the first annulus center, at r = 0.83 mm. The model values are therefore
near-axis values, not measurements at exactly r = 0.

The model's mean absolute profile differences are large: 12.81 percentage
points for CO, 10.50 for H2, and 7.27 for CO2. H2O is also shown, but the
reference reports about +/-14% uncertainty for those experimental values.
Radial experimental traverses have not been digitized in this project.

Element balance checks answer “did the numerical bookkeeping conserve the
tracked atoms?” Validation answers “does the model reproduce measured
behavior?” They are different questions.
