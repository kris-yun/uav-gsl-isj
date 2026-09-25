# Blackwell / Bayes Sufficiency Audit for GSL

Date: 2026-09-25

Decision: **STOP_BLACKWELL_AS_MAIN_INNOVATION / RETAIN_AS_THEORY_AUXILIARY**

## 1. Candidate question

Can the main GSL innovation be framed as learning a representation T(Y) that preserves all source-decision information while discarding plume/environment nuisance?

## 2. Decision-theory requirement under PMFS log loss

For source S, observation Y and representation T(Y), exact Bayes sufficiency for the PMFS probabilistic task requires

  P(S | Y) = P(S | T(Y))

almost surely.

Equivalently,

  S is conditionally independent of Y given T(Y).

For a finite source support and strictly proper log loss, the Bayes-optimal object is the full conditional source distribution.

Therefore a minimal Bayes-sufficient object is equivalent to the posterior vector

  eta(Y) = P(S | Y),

or to an equivalent set of source posterior log-odds / likelihood ratios.

This is a powerful evaluation principle but, without extra structure, it is not a distinct GSL inference mechanism beyond learning a calibrated probabilistic classifier/posterior.

## 3. Recent theory overlap

Recent 2026 representation-learning theory already formalizes Bayes-sufficient representations for a fixed supervised decision problem and explicitly notes that strictly proper scoring rules demand preservation of the predictive distribution.

Blackwell sufficiency is even stronger because it compares experiments across classes of decision problems.

Therefore the project must not claim novelty for:
- Blackwell sufficiency itself;
- Bayes-sufficient representation learning;
- likelihood-ratio preservation;
- learning a representation sufficient for source classification/probability prediction.

## 4. D1R finite-sample sanity check

Use D1R log(1+ppm) observations.

For each symmetric 8/8 fresh-realization direction:
- within the training half use 6 realizations/source to fit a global LDA generalized-eigen representation;
- use the remaining 2 training realizations/source only to select posterior temperature;
- evaluate the opposite 8 realizations/source on the original 168-cell proper log score.

Candidate latent dimensions:
  {5,10,20,40,80,120,160}.

Fresh mean true-source log2 scores:

Direction A:
- d=5: -3.371;
- d=10: -2.549;
- d=20: **-2.386**;
- d=40: -3.019;
- d=80: -3.862;
- d=120: -4.060;
- d=160: -4.084.

Direction B:
- d=5: -3.023;
- d=10: -2.716;
- d=20: **-2.433**;
- d=40: -3.348;
- d=80: -4.084;
- d=120: -4.298;
- d=160: -4.306.

Thus finite-sample predictive risk has a strong interior optimum near 20 dimensions; simply retaining more source-discriminative dimensions degrades fresh proper score under the 6-reference/source fit budget.

## 5. Interpretation

This finite-sample optimum must NOT be interpreted as evidence that 20 dimensions are Blackwell/Bayes sufficient.

It instead demonstrates the same finite-sample phenomenon seen repeatedly in the project:

> oracle information preservation and finite-sample estimability are different objectives.

More theoretically relevant dimensions can hurt because their estimation error exceeds their predictive value under a small stochastic-realization budget.

Therefore Blackwell/Bayes sufficiency does not by itself resolve the central GSL problem of how to trade retained source information against stochastic estimation risk.

## 6. Relation to LSC

LSC remains the stronger empirical mechanism:
- local source-distribution distinguishability is reproducible;
- it predicts fresh pairwise source confusion;
- it predicts fresh 168-cell posterior NLL.

Blackwell/Le Cam theory can provide language for comparing how much source-decision information an observation/representation preserves, but it does not supply a distinct algorithm beyond ordinary calibrated discriminative representation learning.

## 7. Mainline decision

STOP Blackwell/Bayes sufficiency as the main innovation.

Retain it only as a theoretical auxiliary for:
- explaining why posterior odds / likelihood-ratio geometry is the task-relevant information;
- auditing whether a future representation discards source-decision information;
- distinguishing rank-only performance from proper probabilistic sufficiency.

Do not authorize new simulation, a Blackwell-specific neural model, or a new closed-loop experiment from this route.