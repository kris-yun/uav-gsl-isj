# Novelty boundary — 2026 robotics sim-to-real e-process near-neighbor

Date: 2026-09-23  
Branch: \`research/anytime-valid-source-eprocess-v1\`

## Near-neighbor found

Chen & Weng, *Sim-to-Real Betting on the E-Process: Bringing "simulators" to anytime-valid confidence sequences*, arXiv:2606.24038, 2026.

Public code:
\`ISUSAIL/Bet4Sim2Real-EProcess\`.

The repository README states that the notebook implements **Algorithm 1 (Approximate-Kelly betting confidence sequence)** and reproduces confidence-bound width / coverage experiments. The simulator banks are inherited from \`ISUSAIL/Bet4Sim2Real\`.

The paper's stated target is a simulator-assisted anytime-valid **mean/performance certificate**, motivated especially by robot performance testing.

## Consequence

Do NOT claim:

- first e-process in robotics;
- first simulator-assisted e-process;
- first sim-to-real anytime-valid confidence sequence;
- first betting-based robot confidence certificate.

## Remaining candidate distinction

M2 is only defensible if it remains about a different inferential object and closed-loop role:

1. finite/discrete **source-location hypotheses**, not a scalar performance mean;
2. one e-process **per candidate source / source region**;
3. inversion into a **time-uniform source confidence set**;
4. validity along **adaptively selected spatial measurements**;
5. a **safe source declaration / elimination rule** at data-dependent stopping times;
6. eventual action selection by candidate-elimination evidence growth, not simulator-assisted performance evaluation.

This is a near-neighbor and a useful remote-field anchor, but not currently a direct source-localization collision.

## Status

\`M2 KEEP; CLAIM NARROWED\`.
