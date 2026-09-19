# Candidate Challenger — Latent Context Adaptation for GSL

Date: 2026-09-19
Branch: research/remote-paradigm-loop-20260919
Status: DEMOTED AFTER OFFLINE NEGATIVE CONTROL

## Remote-domain provenance

- ICLR 2025 — *Neural Context Flows for Meta-Learning of Dynamical Systems*.
- NeurIPS 2025 — *MaNGO — Adaptable Graph Network Simulators via Meta-Learning*.
- NeurIPS 2025 — *Dynamics-Aligned Latent Imagination in Contextual World Models for Zero-Shot Generalization*.

Shared paradigm:
infer a compact latent environment/context variable from short dynamics histories and use it to adapt a shared dynamics model to unseen physical conditions.

## GSL translation tested

Candidate scientific hypothesis:
> wind/House/transport variation can be summarized by a source-independent latent transport context whose effect can be transferred between source hypotheses.

If true, a lightweight context encoder could modulate the PMFS forward model without a separate candidate-specific discrepancy model.

## Existing-data negative control

The 12 controlled H01/H02/H03 × {SA,SB} × {fast,slow} histories use identical routes within each House.

A strict residual-transfer proxy was used:
1. learn the complete fast↔slow log-response change from one source;
2. apply the same context correction to the other source;
3. evaluate response error on the target wind.

Results:
- only 2/12 transfers improve, both negligibly;
- 10/12 worsen;
- severe failures include ~446×, ~3992× and ~5262× MSE increases;
- H03 worsens in all four transfer directions.

The existing project also independently shows candidate-dependent transport error and failure of generic wind centering/alignment.

## Decision

The source-independent latent-context premise is rejected.

A context model that is explicitly conditioned on source/candidate is still possible, but then its scientific object is no longer “environment context alone”; it becomes a candidate×transport discrepancy model, which is already more directly captured by the current **Learned Missing Physics / Gray-Box Correction** candidate.

Therefore:

LATENT_CONTEXT_ADAPTATION_AS_M1 = NO_GO
LATENT_CONTEXT_AS_INTERNAL_CONDITIONER_FOR_MISSING_PHYSICS = ALLOWED_FUTURE_IMPLEMENTATION

No closed-loop experiment is authorized.
