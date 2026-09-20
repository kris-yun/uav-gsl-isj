# Loop 9 — η-Regularized Predictive Proxy: Not Robust Enough

Date: 2026-09-20
Branch: research/remote-paradigm-loop-20260919
Status: auxiliary candidate screened; current form demoted.

## Question

Does the 2026 Nature Communications η-learning idea provide a genuine incremental auxiliary innovation after the predictive M1, rather than only a plausible rare-event story?

## Proxy

Existing 12 controlled histories:
H01/H02/H03 × {SA,SB} × {fast,slow}.

Base predictor:
- 5 s source-blind context windows;
- current gas statistics + local wind + pose predict next-window gas statistics;
- train on fast wind, test held slow wind.

η-inspired training proxy:
- keep the same model and inputs;
- reweight predictive loss toward target windows with larger rare/high-concentration response;
- fixed global alpha values {0,1,2,5,10};
- no House-specific choice.

This is closer to the η-learning principle than the earlier invalid “tail feature concatenation” proxy, because the rare-event observable modifies training rather than becoming a direct source feature.

## Results

The result is mixed and fails the required uniform auxiliary gate.

### H01
180 s:
- alpha 0 ratio 1.471, 1/2 source identity.
- increasing rare-event weight lowers the ratio gradually to 1.142 at alpha 10, but identity remains 1/2.

240 s:
- identity stays 2/2 for all alpha;
- however the best transport/source ratio is the unweighted model (0.128).
- stronger η weighting progressively worsens the ratio up to 0.233.

### H02
180/240 s:
- identity stays 2/2;
- every tested positive η weight worsens the transport/source ratio relative to alpha 0.

### H03
180 s:
- identity stays 2/2;
- positive η weighting consistently worsens the ratio.

240 s:
- base predictor is 1/2.
- alpha 5 temporarily reaches 2/2, but alpha 10 returns to 1/2.
- this isolated rescue is not stable enough to justify the module.

## Decision

The existing data do support the physical fact that rare/intermittent events can carry source identity.

They do **not** support the stronger claim that a generic η-style rare-event weighting is a robust second innovation on top of the predictive representation.

Therefore:

```
EXTREME_EVENT_IMPORTANCE = SUPPORTED_PHYSICAL_FACT
ETA_REGULARIZATION_AS_M2 = DEMOTED / NOT YET QUALIFIED
NAIVE_TAIL_CONCAT = REJECTED
```

Do not rescue-tune alpha per House.

Nature Communications 2026 η-learning remains useful conceptual literature, but it is no longer counted as a selected auxiliary innovation.

## Consequence

Current architecture temporarily has:
- M1 predictive latent physical representation: ACTIVE.
- M2: OPEN.
- M3 structured shift-aware source region: ACTIVE CANDIDATE.

The next M2 search should solve the actual failure seen here:
- evidence is intermittent and long-memory;
- recent-only predictive summaries can miss source evidence;
- rare-event emphasis alone is too unstable.

Next candidate to test:
**multiscale history integration for partially observable long-memory physical systems**, motivated by NeurIPS 2025 work on partially observable dynamical systems.
