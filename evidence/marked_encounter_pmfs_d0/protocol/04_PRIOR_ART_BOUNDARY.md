# Prior-art boundary

## Distant-domain mother theory

The broad mother idea is **marked event-process inference**, not “use continuous
concentration”.

- Berghaus et al., *In-Context Learning of Temporal Point Processes with
  Foundation Inference Models*, ICLR 2026: marked temporal point processes as
  a principled event-sequence generative object and amortized/in-context
  inference over process dynamics.
- Chang et al., *Deep Continuous-Time State-Space Models for Marked Event
  Sequences*, NeurIPS 2025 Spotlight: continuous-time state-space modeling for
  marked event sequences.
- Draxler et al., *Transformers for Mixed-type Event Sequences*, NeurIPS 2025
  Spotlight: unified event modeling with discrete and continuous attributes.

QA/PMFS D0 does NOT yet justify transplanting any of those neural architectures.
They motivate the information object: event occurrence and event marks are
distinct pieces of a generative process.

## Physical support

Turbulent passive-scalar literature documents intermittent concentration and
non-Gaussian positive concentration PDFs (including gamma/lognormal behavior)
whose form varies across plume core/edge. Thus a positive-event amplitude mark
is physically meaningful and not merely a numeric feature.

## Near-domain claims that are forbidden

Do NOT claim:
- first use of continuous concentration in GSL;
- first Bayesian concentration likelihood;
- first calibration-free GSL;
- first use of gas measurement rank;
- first temporal correlation in olfactory search.

Jin et al., ICRA 2026 explicitly compare gas value, gas hit and gas rank and
propose EDF concentration ranking for uncalibrated MOX sensors.

The prospective contribution is narrower:

**retain PMFS's occurrence probability map, expose the positive-event mark
already implicit in the filament simulator, and update source odds with a
sensor/source-strength nuisance-invariant conditional mark likelihood.**
