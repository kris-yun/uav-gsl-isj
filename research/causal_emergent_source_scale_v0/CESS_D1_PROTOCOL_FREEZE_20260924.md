# CESS D1 Frozen Gate — 630-Source Emergent-Scale Falsification

Date: 2026-09-24

Branch:
\`research/causal-emergent-source-scale-v0\`

Status:
**FROZEN DESIGN — EXECUTION AUTHORIZATION MAY FOLLOW AFTER CODE AUDIT**

## 1. Scientific claim being tested

D1 tests one claim only:

> Under fresh stochastic plume realizations, a spatially contiguous coarse-graining of the 0.30 m PMFS source-cell interventions can carry **more held-out raw interventional effective information** about source state than the original micro-cell representation.

D1 does not test closed-loop navigation.

D1 does not claim a final physical source radius.

D1 does not use normalized effectiveness to choose the scale.

## 2. Frozen source microstates

Use the complete frozen Gate1A House02 equal-area source bank:

- 630 free PMFS support cells;
- cell spacing 0.30 m;
- source z = 0.20 m;
- source order exactly as stored in \`source_bank.tsv\`.

Using all 630 cells preserves the spatial adjacency graph.

No source subsampling is permitted.

## 3. Environment

House:
\`House02\`

Wind:
\`W2 = 3,5-1_slow\`

Reuse the frozen GADEN / occupancy / extractor contracts from R0 and Gate1A.

Observation operator:
- the same 10 times;
- the same 30 pooled probes;
- primary encounter variable:
  \(H_{tq}=1[C_{tq}>0]\).

The exact-zero threshold is a simulation-mechanism contract, not a real-sensor detection threshold. Real-flight threshold transfer is outside D1.

## 4. New realizations

Generate exactly **8 fresh realizations for every one of the 630 source cells**.

Total:
\[
630\times 8 = 5040
\]
new GADEN realizations.

No Gate1A C/D realization may enter D1 estimation.

Frozen seed rule for source-bank row index \(i=0,\dots,629\) and replicate \(r=1,\dots,8\):

\[
seed(i,r)=2026100000+8i+r.
\]

Thus every source/replicate receives a unique seed.

## 5. Frozen split

Two symmetric directions are evaluated.

### Split A
- train micro likelihoods: replicates 1–4;
- held out: replicates 5–8.

### Split B
- train: replicates 5–8;
- held out: replicates 1–4.

No realization appears in train and held-out sets within one direction.

D1 does not select a final source scale from only one direction.

## 6. Micro likelihood

For each micro source \(s\), estimate only its binary encounter marginals:

\[
\hat p_{s,tq}
=
\frac{k_{s,tq}+1/2}{4+1},
\]

where \(k_{s,tq}\) is the number of encounters in the four training realizations.

This is the Jeffreys Beta(1/2,1/2) posterior mean.

For a held-out binary observation \(h\):

\[
\log \hat p(h|s)
=
\sum_{t,q}
h_{tq}\log\hat p_{s,tq}
+
(1-h_{tq})\log(1-\hat p_{s,tq}).
\]

Uniform micro intervention prior:

\[
p(S=s)=1/630.
\]

No learned neural decoder is allowed in D1.

## 7. Frozen spatial hierarchy

Construct a deterministic hierarchy using only:

- PMFS \((i,j)\);
- x-y source coordinates;
- four-neighbor free-cell adjacency.

Use **connectivity-constrained Ward agglomeration**:

- start from all 630 singleton cells;
- only adjacent clusters may merge;
- Ward merge cost:
\[
\Delta(A,B)
=
\frac{|A||B|}{|A|+|B|}
\|\mu_A-\mu_B\|_2^2;
\]
- deterministic tie break by the minimum source-bank row id in each cluster.

Plume observations must never influence the hierarchy.

Frozen macrostate counts:

\[
M\in
\{630,420,315,210,158,126,90,63,45,30,21,15,10,6,4,3,2\}.
\]

If an exact requested count is impossible because of an implementation bug, D1 is infrastructure STOP; do not silently replace the count.

Every macrostate must be four-neighbor connected.

## 8. Strict macro intervention likelihood

No macro Bernoulli profile is fitted.

For macrostate \(m\) containing micro sources \(\mathcal S_m\):

\[
\hat p(h|do(M=m))
=
\frac{1}{|\mathcal S_m|}
\sum_{s\in\mathcal S_m}
\hat p(h|do(S=s)).
\]

Compute this in log space by log-sum-exp.

Uniform macro intervention prior:

\[
p(M=m)=1/M.
\]

Therefore macro scale receives no extra parameter-estimation samples relative to the trained micro channel.

## 9. Primary information metric

For a held-out realization from the true source, compute posterior probability of its true micro source or true macrostate.

Held-out cross entropy:

\[
CE(M)=
\mathbb E[-\log q(M_{true}|H)].
\]

Primary raw effective-information lower bound:

\[
\underline{EI}(M)
=
\log M-CE(M).
\]

The micro reference is:

\[
\underline{EI}_{micro}=\underline{EI}(630).
\]

Macro information gain:

\[
\Delta EI(M)
=
\underline{EI}(M)-\underline{EI}(630).
\]

Normalized effectiveness

\[
\underline\eta(M)=\underline{EI}(M)/\log M
\]

is diagnostic only and cannot select the D1 scale.

## 10. Source-cluster bootstrap

For each split and each macro count, compute a 95% bootstrap interval for \(\Delta EI(M)\).

Bootstrap unit:
**micro source cell**.

When one source is sampled, include all four held-out realizations of that source.

Use:
- 2000 bootstrap replicates;
- fixed bootstrap RNG seed \`2026109001\`.

The trained likelihoods and hierarchy remain fixed during bootstrap.

Report the 2.5%, 50%, and 97.5% quantiles.

## 11. Random grouping control

For every \(M<630\):

- preserve the exact cluster-size vector of the spatial hierarchy;
- generate 250 random non-spatial partitions;
- RNG seed \`2026109002\`;
- do not refit micro likelihoods;
- construct every random macro likelihood by the same uniform mixture of trained micro likelihoods.

Report the spatial \(\underline{EI}(M)\) percentile among the 250 random controls separately for Split A and Split B.

The random control tests whether a gain is specifically associated with spatial source coherence rather than simply fewer labels.

## 12. Scale-band criterion

A single lucky hierarchy level is insufficient.

Let the frozen M sequence be ordered from fine to coarse.

A **supported scale band** requires at least two adjacent tested macro counts \(M_a,M_b\) such that, in BOTH split directions:

1. \(\Delta EI(M)>0\);
2. the 95% source-bootstrap lower bound of \(\Delta EI(M)\) is >0;
3. the spatial partition is above the 95th percentile of its size-matched random partitions.

The band must exclude the micro endpoint \(M=630\).

## 13. Peak reproducibility

For each split, find the \(M\) with maximum raw \(\underline{EI}(M)\).

PASS requires the two peak macro counts to lie within one adjacent step of one another in the frozen M sequence **or** both lie inside the same supported scale band.

This prevents promoting a scale whose optimum moves wildly with plume realization subset.

## 14. Frozen decision

### PASS

\`CESS_D1_PASS_EMERGENT_SOURCE_SCALE\`

Requires:

- all 630 sources ×8 realizations valid;
- one supported scale band as defined above;
- peak reproducibility condition passes.

A PASS means:
a spatial emergent source scale is a reproducible offline mechanism in House02/W2.

It does **not** yet authorize a main-paper claim or closed loop.

### HOLD

\`CESS_D1_HOLD_MORE_REALIZATIONS\`

Use HOLD only if:

- at least one macro count has positive point-estimate \(\Delta EI\) in both splits;
- and spatial percentile >0.95 in both splits;
- but bootstrap or peak-reproducibility criteria fail.

HOLD action is predetermined:
add 8 more fresh realizations per same 630 sources to reach K=16. Do not change hierarchy, metric, or M sequence.

### STOP

\`CESS_D1_FAIL_STOP_CAUSAL_EMERGENT_SCALE_MAINLINE\`

If no macro count has positive \(\Delta EI\) in both split directions or spatial random-control specificity fails.

No alternative clustering, threshold, M grid, or decoder may be tried as rescue.

## 15. Secondary spatial metrics

For every hierarchy level report, but do not use to change D1 decision:

- macro cell-count distribution;
- macro area distribution (0.09 m² per micro cell);
- cluster Euclidean diameter distribution;
- graph diameter distribution;
- number of clusters touching obstacles/boundaries if derivable.

These statistics translate information-optimal macro count into a physical source-resolution interpretation after the gate, not before it.

## 16. After D1

If PASS:
- freeze the supported scale band;
- run one new fully fresh House02 confirmation batch or directly a cross-wind/cross-House gate according to the subsequent protocol;
- only then build the PMFS macro posterior.

If HOLD:
- K=16 only, same sources and frozen theory.

If STOP:
- stop causal-emergent source scale as the mainline.
- retain temporal encounter history only as a possible auxiliary mechanism, not as an automatic replacement mainline.

No PMFS closed loop is authorized by D1 alone.
