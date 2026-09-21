# MIPO V1 collision audit + source-blind probe screen

Date: 2026-09-21

Data commit:

`fa97cd6fc3be7b6ef40eee828038b94de40fa514`

## Verdict

**MIPO_V1_CURRENT_FORM = NO-GO FOR PROMOTION**

The raw probe export is valid and useful, but the current formulation does
not meet either the novelty or efficacy bar required for a main innovation.

Two separate conclusions are important:

1. deliberate motion clearly creates command-frequency gas modulation in the
   local GADEN field;
2. that modulation does **not** reliably encode source direction in the
   pre-registered screen below.

Therefore "motion creates a measurable signal" must not be conflated with
"motion restores source observability".

## Collision audit

The broad idea "periodically perturb robot motion and synchronously demodulate
the gas response" is **not new to odor/gas source localization**.

Relevant prior art includes:

- Nakamoto/Ishida odor compass (1996): rotating active sampling probe,
  multiple gas sensors and fan-induced sampling for odor-source direction.
- Ishida et al. (1998): moving a robot through the gas field and fitting a gas
  distribution model while accounting for sensor response delay.
- Neumann et al. micro-drone work (2012/2013): a pseudo-gradient strategy that
  deliberately splits one measurement location into spatially separated
  measurements because simultaneous spatial gradients are unreliable on a
  rotorcraft.
- Jabeen et al., Building and Environment (2023), gradient-adaptive extremum
  seeking OSL: sinusoidal perturbation/modulation, system response, high-pass
  filtering and same-frequency demodulation are explicitly used to estimate
  plume gradients.
- Sniffbot (2026): active odor sampling/sniffing is already an explicit
  robotic-olfaction mechanism.

The 2025 European Journal of Control active-sensing theorem and 2026
event-based visual-servoing work provide a strong cross-domain
**observability** motivation, but importing their language does not make the
GSL instantiation novel if the implemented mechanism reduces to classical
extremum-seeking dither/demodulation.

Thus:

- "MIPO = periodic probe motion" is not a sufficient novelty claim.
- "ECD = multiply gas signal by the known sinusoidal command" substantially
  collides with extremum-seeking demodulation.
- "virtual bilateral sensing" substantially collides with long-standing
  moving/split-position gradient sampling.

A narrower ASF idea -- selecting the probe frequency from ambient-clutter and
sensor spectra -- was not found as a direct GSL method in this targeted
search, but it is only an auxiliary concept and cannot rescue a collided,
non-discriminative main mechanism.

## Frozen screen

No source truth was used to choose the probe waveform or frequencies.

Fixed probe:

- circular motion;
- radius A = 0.4 m;
- frequencies = {0.125, 0.25, 0.5} Hz;
- raw GADEN patch, 32 s, 5 Hz;
- bilinear interpolation within the exported 7x7 patch.

For each frequency, the moving signal was compared with the simultaneous
stationary-center signal at the same Fourier bin.

### Motion-induced spectral signal

Median moving/stationary amplitude ratio:

| f | median ratio | anchors >1 | anchors >2 |
|---|---:|---:|---:|
| 0.125 Hz | 2.153 | 14/18 | 9/18 |
| 0.25 Hz | 2.578 | 16/18 | 12/18 |
| 0.5 Hz | 14.987 | 16/18 | 16/18 |

Therefore controlled motion can create a strong command-frequency modulation.

Two early anchors have essentially no usable gas signal, showing the obvious
limit: local excitation cannot create chemical information where the entire
local patch is effectively blank.

### Source-direction relevance

The command-referenced circular probe was demodulated into an estimated local
2-D response vector.

Median angular error to the true source direction:

| readout | median angular error |
|---|---:|
| static time-mean local concentration gradient | 84.08 deg |
| 0.125-Hz probe | 89.66 deg |
| 0.25-Hz probe | 84.04 deg |
| 0.5-Hz probe | 85.48 deg |
| source-blind ASF-selected frequency | 87.12 deg |

For the ASF-selected response:

- only 3/16 non-degenerate anchors are within 45 deg of the source;
- static gradient has 4/16 within 45 deg;
- source-relative crosswind-side sign is correct in only 4/16 usable anchors.

Thus the probe response is strong but is not a reliable source-direction
observable in this dataset.

## ASF source-blind selection

For the three fixed frequencies, the screen selected frequency using only:

- stationary-center spectral power;
- the frozen sensor first-order response magnitude with tau = 1.2 s.

No source truth was used.

Selected frequencies:

- 0.125 Hz: 7 anchors
- 0.25 Hz: 1 anchor
- 0.5 Hz: 10 anchors

This adaptive selection does not improve source-direction error over the
static gradient or the fixed-frequency probes.

The exported patches contain raw GADEN concentration, not a physically
continued counterfactual sensor state. The actual R2 sensor has 0.4-s dead
time and 1.2-s time constant. Its nominal first-order amplitude response is
approximately:

- 0.125 Hz: 0.728
- 0.25 Hz: 0.469
- 0.5 Hz: 0.256

Therefore the very large raw 0.5-Hz modulation ratios should not be interpreted
as equally large PMFS-observable sensor modulation.

## Scientific interpretation

This screen falsifies the strongest current MIPO claim:

> "a small designed periodic motion restores a source-direction observable."

What is supported is only:

> "a small designed motion produces a measurable local plume modulation."

Those are not equivalent.

The failure is physically plausible: a local concentration gradient or local
motion-transfer response in a turbulent, obstacle-affected plume can describe
local filament geometry without pointing toward the source.

## Decision

Do not implement MIPO V1 closed loop.

Do not promote ECD or ASF as paper innovations from this dataset.

Do not tune amplitude/frequency after reading source truth to rescue V1.

The 18-anchor patch dataset should be retained because it is a useful
source-blind acquisition benchmark for future *different* sensing principles.

The next research candidate should avoid reducing to:

- extremum-seeking dither + demodulation;
- local concentration-gradient estimation;
- another posterior score on the same passive measurements.

## External sources used for the collision audit

- Jabeen et al., "Robot odor source localization in indoor environments based
  on gradient adaptive extremum seeking search", Building and Environment 229
  (2023), 109983.
- "A review of the evolution of mobile robot odor source localization
  methods", Discover Computing 28 (2025).
- Nakamoto et al., "An odor compass for localizing an odor source", Sensors
  and Actuators B 35 (1996), 32-36.
- Neumann et al., gas-source localization with a gas-sensitive micro-drone,
  2012/2013.
- Biswas, Sontag & Cowan, "An exact active sensing strategy for a class of
  bio-inspired systems", European Journal of Control (2025).
- Mordad et al., "Bio-Inspired Event-Based Visual Servoing for Ground
  Robots", IEEE Control Systems Letters (2026).
- "The Sniffbot: A biohybrid robot for active sensing-based odor localization
  and discrimination" (2026).
