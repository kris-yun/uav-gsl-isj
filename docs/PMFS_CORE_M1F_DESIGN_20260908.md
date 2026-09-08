# CORE-M1F: intervention-time-aligned causal evidence

Status: **IMPLEMENTATION CANDIDATE; CLOSED-LOOP EVIDENCE PENDING**.

## Why M1E is insufficient

M1E fixed two real PMFS failure modes: it commits each observation block once,
and it marginalizes the source likelihood over three native transport members.
Its H01/H02/H03 seed9 gate passed, but H01 seed8 failed final error.  Audit logs
show the remaining mismatch: with `stepsSourceUpdate=3`, an update interprets
24 new blocks from three physical stops using the transport state available at
the end of that multi-stop window; the first update contained 32 blocks.

That violates the intended event-time estimand.  Executed sensing action,
outcome, and environmental context must refer to the same local intervention
window.  M1F therefore makes one source update after every post-warm-up
physical stop (`stepsSourceUpdate=1`), excludes pre-warm-up blocks from causal
scoring, and keeps all eight ordered sensor-dynamic blocks from that stop.
Three transport members are still marginalized at the likelihood level.

The paired A0 baseline uses exactly the same source-update cadence.  No planner
weight, gas threshold, sensor law, map, wind helper, trajectory budget, source
truth, or stopping rule changes between arms.

## Causal object

For post-warm-up physical stop `k`, the vehicle executes
`A_k = do(X_k=x_k)` and observes the ordered block vector
`Y_k=(Y_k1,...,Y_k8)`.  Conditional on source candidate `s`, local context
`H_k`, and transport member `u`, M1F uses

```text
logit P(Y_kr=1 | do(A_k), S=s, H_k, U_k=u)
  = b_kr(H_k,U_k) + tau_skr(A_k,U_k).
```

Candidate-centering removes an additive candidate-common log-odds nuisance for
each member.  The member-specific sequence likelihoods are then averaged and
multiplied into the previously committed posterior exactly once.  The local
stability assumption is now limited to one physical stop rather than three or
four stops.

## 2026 theory support and its boundary

- Moran and Aragam, JASA 2026, organize causal representation learning around
  interventions, latent factors, and explicit identifiability classes.  This
  supports stating the intervention and the remaining equivalence class rather
  than relabelling generic robustness as causality:
  <https://doi.org/10.1080/01621459.2026.2620154>.
- Markham et al., CLeaR 2026, use context-specific interventions to separate
  causal concepts and prove an identifiability result.  M1F adopts the narrower
  design principle that action-responsive source contrast must be separated
  from environmental context:
  <https://proceedings.mlr.press/v323/markham26a.html>.
- Kim et al., UAI 2026, show that observed inputs internal to a mixing process
  cannot simply be treated as external auxiliaries, and establish conditions
  under which conditioning restores subspace identification.  This directly
  motivates binding observed wind/sensor context to the same intervention
  window instead of mixing contexts across stops:
  <https://proceedings.mlr.press/v337/kim26e.html>.
- Asiaee, Aryan and Long, UAI 2026, quantify validity loss when interventions
  incorrectly pooled as unaffected are not actually invariant.  It supports
  M1F's refusal to pool evidence across non-aligned transport contexts:
  <https://proceedings.mlr.press/v337/asiaee26b.html>.

These papers support the causal design principles, not the gas-specific
likelihood equation or its utility.  M1F's algebraic cancellation test,
event-window audit, and paired closed-loop results carry that burden.

## Frozen first gate

Run H01 algorithm seed7, sensor/replay seed12, 240 s, paired A0 versus M1F.
Both arms use `stepsSourceUpdate=1`.  Continue to H02/H03 only if M1F improves
both final source error and 0--240 s distance AUC.  A failure is preserved and
stops seed7 expansion.

This is still not an independent-plume or big-data test because the current
environment certificate freezes sensor/replay seed12.  That claim requires a
new family of per-sensor-seed environment certificates after M1F passes the
cheap staged gate.
