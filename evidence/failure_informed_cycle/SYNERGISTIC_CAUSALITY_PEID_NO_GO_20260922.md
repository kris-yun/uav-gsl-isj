# Synergistic causality / Partial Effective Information Decomposition transfer — NO-GO

Date: 2026-09-22
Status: **NO-GO AS MAIN LINE**

## Mother idea

Yang, Wang & Zhang, *Partial Effective Information Decomposition for Synergistic Causality* (2026), arXiv:2605.03267.

The theory decomposes interventionist effective information into unique, redundant and synergistic causal contributions. Scite excerpts explicitly describe synergy as non-additive effective information under source-side maximum-entropy interventions.

## GSL transfer tested

For each source hypothesis:
- candidate plume state Q_s(t);
- robot/source geometry state G_s(t);
- current sensor encounter Y_t;
- target future encounter Y_{t+1}.

Using empirical conditional channels with uniform source-state interventions, compute:
- EI(Y_t -> Y_{t+1});
- EI(Y_t,Q_s -> Y_{t+1});
- EI(Y_t,G_s -> Y_{t+1});
- EI(Y_t,Q_s,G_s -> Y_{t+1}).

The PEID-inspired non-additive synergy proxy was

  EI(Q,G,Y -> Y') - EI(Q,Y -> Y') - EI(G,Y -> Y') + EI(Y -> Y').

A second diagnostic used plume contribution beyond geometry:
  EI(Q,G,Y -> Y') - EI(G,Y -> Y').

## Joint old+new development result

Natural K=4, lag=1 screen:

### Synergistic term
- all-12 mean = **4.5632 m**
- pooled reduction = **21.11%**
- non-worse = **6/12**
- old = **19.82%**, 3/6
- new = **22.30%**, 3/6

### Plume beyond geometry (unique + synergy)
- all-12 mean = **4.1788 m**
- pooled reduction = **27.76%**
- non-worse = **8/12**
- old = 5/6
- new = 3/6

### Undecomposed joint effective information
- all-12 mean = **3.5959 m**
- pooled reduction = **37.83%**
- non-worse = **12/12**

The undecomposed joint state is predictive, but the specific synergistic contribution that motivates the 2026 mother theory is not robustly source-identifying.

## Decision

The defining PEID mechanism fails the failure-informed gate before destructive-control escalation:
- synergy only 6/12;
- old and new each only 3/6;
- the strongest number comes from a different, undecomposed quantity.

Therefore it would be scientifically incorrect to relabel the strong joint-EI result as synergistic causality.

Final verdict:
`SYNERGISTIC_CAUSALITY_PEID_GSL_TRANSFER_NO_GO_20260922`
