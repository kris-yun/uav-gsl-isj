# CESS D1B Pre-Registered Strong-Decoder Control

Date: 2026-09-25

Branch:
\`research/causal-emergent-source-scale-v0\`

Status:
**PRE-REGISTERED BEFORE D1A RESULT — DO NOT RUN UNLESS D1A PASSES AND IS INDEPENDENTLY REVIEWED**

D1B uses **zero new GADEN simulations**.

Its sole purpose is to test whether a D1A macro-scale gain survives a stronger
temporal decoder, rather than being an artefact of the factorized Bernoulli
measurement model.

## 1. Dependency

D1B is authorized only when the frozen D1A result is:

\`CESS_D1A_PASS_EMERGENT_SOURCE_SCALE\`

and the primary thread independently confirms that PASS.

If D1A fails, D1B is never run.

## 2. Inputs are frozen by D1A

Reuse exactly:

- the same 168 source microstates;
- all 16 fresh D1A realizations/source;
- the same two 8/8 train/test directions;
- the same connected Ward hierarchy;
- the same macrostate size vectors;
- the D1A-supported scale band(s).

No scale may be added because it looks favorable under Markov decoding.

## 3. Stronger decoder

D1B uses a **time-homogeneous first-order binary Markov model per source and
probe**.

It is a discrete snapshot-history model only.

It is not a claim about continuous-time point processes, whiff durations,
renewal processes, or true first-passage times.

For each source \(s\) and probe \(q\):

### Initial state

\[
\hat p_s(H_{0q}=1)
=
\frac{k^{init}_{s,q}+1/2}{8+1}.
\]

### Transition

For previous state \(a\in\{0,1\}\):

\[
\hat p_s(H_{tq}=1|H_{t-1,q}=a)
=
\frac{n_{s,q,a\rightarrow1}+1/2}
{n_{s,q,a\rightarrow0}+n_{s,q,a\rightarrow1}+1}.
\]

Transition counts pool the 9 adjacent snapshot transitions across the 8
training realizations.

## 4. Macro intervention remains unchanged

For every D1A macrostate:

\[
\hat p(h|do(M=m))
=
\frac{1}{|\mathcal S_m|}
\sum_{s\in\mathcal S_m}
\hat p(h|do(S=s)).
\]

No Markov macro model is fitted.

Macro prior is uniform and held-out evaluation is also uniform over
macrostates, then uniform over microstates within each macrostate.

## 5. Information metric

For the Markov decoder:

\[
\underline{EI}_{Markov}(M)=\log M-CE_{do(M)}.
\]

\[
\Delta EI_{Markov}(M)
=
\underline{EI}_{Markov}(M)
-
\underline{EI}_{Markov}(168).
\]

Raw EI is primary.

## 6. Uncertainty and random controls

For every M belonging to any D1A-supported band:

- 2000 source-stratified realization bootstrap replicates;
- resample the 8 held-out realizations within every source;
- q2.5/q50/q97.5 of Markov \(\Delta EI\);
- 250 size-matched non-spatial random partitions;
- same strict macro likelihood and uniform-macro evaluation.

D1B bootstrap base seed:
\`2026119101\`.

D1B random control seed:
\`2026119102 + M\`.

## 7. Markov-supported scale

A D1A-supported M remains supported under D1B only if in BOTH split directions:

1. Markov \(\Delta EI(M)>0\);
2. bootstrap q2.5 > 0;
3. spatial EI percentile > 0.95 against size-matched random grouping.

A surviving Markov band requires at least two adjacent M values from the same
pre-existing D1A-supported band.

## 8. Peak robustness

Find the raw Markov-EI maximizing M separately in Split A and Split B.

Both Markov peaks must be:

- inside a surviving Markov band, or
- one adjacent frozen hierarchy level from that band.

## 9. Decision

### PASS

\`CESS_D1B_PASS_DECODER_ROBUST_EMERGENT_SCALE\`

Requires:
- at least one surviving band with >=2 adjacent M;
- Markov peak robustness.

Interpretation:
the emergent source-scale signal is not specific to the independent Bernoulli
decoder and is strong enough to advance to fresh environment falsification.

### STOP

\`CESS_D1B_FAIL_STOP_CAUSAL_EMERGENT_SCALE_MAINLINE\`

Any failure.

No new seeds, decoder modification, different Markov order, or scale reselection
is allowed as rescue.

## 10. Why D1B is pre-registered now

R0 already showed temporal adjacency carries additional source identity.

A causal-emergence claim based only on a weaker independent decoder would be
vulnerable to the explanation:

> coarse-graining merely repairs decoder misspecification.

D1B is therefore frozen **before D1A is revealed**.

It is a robustness control for the main innovation, not an auxiliary innovation
claim.
