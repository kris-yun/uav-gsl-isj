# CFIR V1: one-shot H03 causal-footprint gate

CFIR is the one next mechanism after CTAER.  It combines two 2026 ideas at the
candidate-evidence level:

1. backward source footprints / domains of dependence from turbulent-source
   inversion; and
2. forward-versus-reversed trajectory likelihood ratios from nonequilibrium
   statistical physics.

For candidate source `c` and the frozen LMBT diffusivity `kappa`, CFIR computes

`J(c) = log F_chronological(c) - log F_reversed(c)`.

Higher `J` means the observed whiffs are more compatible with the physical
wind chronology than with its reversed negative control.  `J` is a
candidate-relative evidence field produced before Bayesian accumulation.

The formal sequence is fixed:

1. read `THEORY_AND_COLLISION_AUDIT.md`, `LITERATURE_TRACE.md`, and
   `PREREGISTRATION_H03_SEED11.json`;
2. run `python cfir_h03_gate.py --selftest`;
3. commit and verify the remote branch before opening H03 outcomes;
4. execute exactly one H03 seed11 development run; and
5. freeze the raw JSON and verdict without tuning.

Even a pass is only an oracle-wind development premise.  It is not a
cross-dataset result, deployable real-flight method, or completed main claim.

