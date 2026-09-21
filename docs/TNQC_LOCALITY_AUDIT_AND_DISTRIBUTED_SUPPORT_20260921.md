# TNQC locality audit and distributed-support refinement
Date: 2026-09-21

## Why this audit was added

A review correctly identified an important claim boundary in the previous TNQC
screen: the archived 240 s VGR experiment is a **two-source, fixed-route
cross-transport discrimination test**, not the full PMFS localization task.
That criticism stands.

A stronger criticism was also raised: perhaps the positive TNQC signal is only
coming from a small local patch or the immediate neighborhood of the source.
That can be tested without another closed-loop run because the controlled VGR
asset uses the **exact same pose and timing sequence** across SA/SB and
fast/slow within each House.

The new audit is:

- `reference/tnqc_vgr_distributed_support_audit.py`
- frozen result:
  `evidence/TNQC_VGR_DISTRIBUTED_SUPPORT_AUDIT_20260921.json`

It does not change the online method or the frozen 300 s GO gate.

---

## 1. Route identity is exact

For H01, H02 and H03, all four episodes
`SA_fast / SA_slow / SB_fast / SB_slow` have:

- 1200 samples;
- identical simulation timestamps;
- maximum pose difference = **0 m**.

Therefore cross-transport comparisons cannot be explained by different robot
routes.

---

## 2. The signal is not confined to one local spatial patch

At 240 s, using the opposite-wind episode as the candidate template:

| support retained | affine quotient | raw amplitude |
|---|---:|---:|
| all common PMFS bins | 12/12 | 12/12 |
| checkerboard even bins only | 12/12 | 12/12 |
| checkerboard odd bins only | 12/12 | 12/12 |
| remove all bins within 1 m of either source | 12/12 | 12/12 |
| remove all bins within 2 m of either source | 11/12 | 11/12 |
| remove all bins within 3 m of either source | **11/12** | 8/12 |
| retain only bins farther than 4 m from both sources | **11/12** | 9/12 |

The distance masks are evaluator-only destructive tests; source position is not
available to the method. Their purpose is only to ask where the signal lives.

This falsifies the narrow statement “the observed TNQC signal exists only next
to the source.”  A substantial source-dependent spatial pattern persists in
far-field support.

It does **not** prove full localization, because only SA and SB are candidate
hypotheses in this controlled asset.

---

## 3. Independent disjoint spatial subsets agree

A stronger source-blind test partitions PMFS bins without using source truth.

### Two-fold checkerboard

Compute the affine quotient twice:

[
q^{(0)}_{m aff}(s),qquad q^{(1)}_{m aff}(s)
]

on the two disjoint parity subsets
((i+j)mod2=0) and ((i+j)mod2=1).

Both halves independently rank the true source in **12/12** cases.

### Four-fold spatial hashes

For a fixed four-way hash, all folds agree in 10/12 cases and every released
case is correct.

Across **100 source-blind four-fold hash partitions**:

- coverage: **91.7% to 100%**;
- mean coverage: **96.9%**;
- conditional accuracy: **100% in every run**.

So the signal is not being carried by one special local subset.  Independent
spatial subsets usually recover the same candidate ordering.

---

## 4. The quotient has a real nuisance advantage over raw amplitude

The raw representation is also 12/12 on the unperturbed terminal asset, so
unperturbed accuracy alone cannot establish the need for quotienting.

The discriminating test is nuisance intervention.

### Independent positive scale, 100 source-blind seeds

Each episode receives its own scale
(asimmathrm{LogUniform}(0.05,20)).

- affine quotient: **12/12 for all 100 runs**;
- raw amplitude: mean accuracy **75.1%**;
- raw minimum **58.3%**;
- raw achieved 12/12 in **0/100** runs.

### Independent positive background offset, 100 source-blind seeds

Each episode receives its own (bin[0,5]) ppm.

- affine quotient: **12/12 for all 100 runs**;
- raw amplitude: mean accuracy **62.3%**;
- raw minimum **8.3%**;
- raw achieved 12/12 in only **1/100** runs.

This is the cleanest current evidence that TNQC is doing something different
from merely reading the strongest concentration region.

---

## 5. Important negative result: identifiability is late

The same audit also found a weakness that should not be hidden.

The full affine field is not informative enough early in the route:

| time | valid-case coverage | accuracy among valid |
|---:|---:|---:|
| 80 s | 0% | — |
| 120 s | 0% | — |
| 160 s | 41.7% | 60% |
| 176 s | 41.7% | 100% |
| 200 s | 41.7% | 100% |
| 220 s | 75% | 100% |
| 240 s | **100%** | **100%** |

Thus the present mechanism evidence supports **terminal robustness**, not an
early-search claim.  This is exactly why the final 300 s PMFS replay remains
necessary: the online method is useful only if this late but robust spatial
evidence moves the posterior enough to reduce the actual localization error.

---

## 6. Better second-innovation direction: distributed-support consistency

The audit suggests a stronger auxiliary mechanism than simply adding another
local feature.

Let the supported spatial field be split source-blind into disjoint folds
(mathcal S_1,ldots,mathcal S_K).  For every candidate (s_i), compute

[
q_i^{(k)} = q_{m aff}(x_{mathcal S_k},
                         y_{s_i,mathcal S_k}).
]

For two folds, define candidate-bank ordering concordance

[
C_{m sp}
=
rac{1}{|mathcal P|}
sum_{(i,j)inmathcal P}
operatorname{sgn}(q_i^{(1)}-q_j^{(1)})
operatorname{sgn}(q_i^{(2)}-q_j^{(2)}),
]

ignoring tied/invalid pairs, and a shared gate

[
g_{m sp}=max(0,C_{m sp}).
]

The existing local-order corroboration gives another shared non-negative gate
(g_{m ord}).  A future version can use

[
e_i=g_{m sp},g_{m ord},q_{m aff}(s_i).
]

Because both gates are common non-negative scalars for the whole candidate
bank,

[
e_i-e_j
=
g_{m sp}g_{m ord}
left[q_{m aff}(s_i)-q_{m aff}(s_j)ight],
]

so neither auxiliary channel can reverse the ordering of the exact main
quotient.  They can only attenuate or abstain.

This gives a cleaner hierarchy:

1. **main:** exact transport-nuisance quotient;
2. **auxiliary A:** monotone local-order corroboration for sensor-transfer
   robustness;
3. **auxiliary B:** disjoint spatial-support consistency for identifiability
   and protection against a local-patch artifact.

The new spatial gate is **not yet enabled online**.  Enabling it would create a
new method version and must be pre-registered before looking at the
authoritative 300 s House result.

---

## 7. Current decision

The locality audit changes the interpretation as follows.

**What is now supported**
- VGR signal is real on the controlled project asset;
- it is cross-transport;
- it is distributed across space rather than confined to one source-near
  region;
- affine quotienting has a strong, exact nuisance advantage over raw amplitude;
- disjoint spatial partitions provide a promising source-blind identifiability
  gate.

**What is still not supported**
- improvement of the PMFS final top-5% localization error at 300 s;
- benefit over the already frozen ME-ACI method;
- full multi-candidate localization from the 240 s two-source asset;
- early-time localization gain.

Therefore the scientifically correct status remains:

> **TNQC mechanism: strengthened positive.  Full localization: unconfirmed.**

The next authoritative command is unchanged:

```bash
bash reference/run_tnqc_vgr_offline_gate_20260920.sh
```

That fixed-trajectory 300 s replay is the cheapest remaining experiment that
can turn the mechanism signal into a localization decision before any new
closed-loop matrix.
