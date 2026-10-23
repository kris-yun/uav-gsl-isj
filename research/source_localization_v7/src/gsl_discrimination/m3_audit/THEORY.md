# M3: cost allocation, persistent coverage, and a fresh-data audit

Implemented 2026-10-23. The implementation is a finite-channel research module. It does not certify that a simulator-fitted channel is the true conditional law of a physical plume.

## 1. Public interface and ownership of observations

```python
from gsl_discrimination.m3_audit import CoveragePlanner, AuditLedger

planner = CoveragePlanner(epsilon=0.2, rng=rng)
audit = AuditLedger(channel, alpha=0.05)  # fresh suffix; no old posterior

plan = planner.plan(
    channel, posterior.predict(), posterior.source, step,
    exploit_mask=return_tube_mask,  # optional boolean [action]
    challenger=challenger,        # optional legal source index
)
action = plan.action  # None only when the planner was not given an RNG
audit.prepare(action)             # MUST precede seeing this outcome
raw_block = environment.observe(action)
symbol = encoder.transform(raw_block)  # encode this raw block once
posterior.update(action, symbol, event_id)
snapshot = audit.update(action, symbol, event_id)
```

`posterior.update` and `audit.update` have distinct purposes. The first updates the source probability map once with the raw symbol. The second uses that same event in a separate decision/stop audit. An e-value is never multiplied back into the source posterior. Running both computations is not two observations. Reusing the block in a second posterior likelihood, or treating an overlapping window as independent, would be double counting.

`AuditLedger.prepare(action, probabilities=P_t, model_version=...)` can instead freeze a predictable conditional table for the next event. `P_t` must retain the original `[action, source, nuisance, outcome]` shape and nuisance meanings. The stored table is copied before the outcome. A pending observation, mismatched action, duplicate event ID, or impossible modeled suffix produces an error before evidence is changed. Event IDs detect duplicate identifiers; they cannot detect a client disguising the same raw measurements under new IDs.

The module does not automatically stop on a posterior threshold or eliminate a source from the planner. A caller may apply a prespecified confidence-list stopping rule, with all assumptions below, or use a fixed resource horizon.

## 2. What the installed channel means

The intended semantic is

\[
P_t(a,s,r,o)
=P(Y_t=o\mid \mathcal F_{t-1}=f_{t-1},A_t=a,S=s,R=r).
\]

Every candidate is conditioned on the same **actual realized past**. A hypothetical source may imply a different latent-state filter, but not a different observed history. Source labels, future snapshots, and the current outcome cannot enter the table before `prepare`.

A fixed `FiniteChannel` table represents a memoryless channel or conditionally independent nonoverlapping blocks. Ten snapshots spaced 50 seconds apart do not by themselves establish independence or a dense temporal motion law. To handle temporal memory, produce correct conditional increments, carry the necessary hidden sensor/transport state, or change the experiment to justified independent blocks. The API's ability to accept a new table does not solve that modeling problem.

Nuisance index `r` denotes one shared value throughout an audit: for example an emission-rate bin, fixed sensor-response setting, or fixed error-channel parameter. Its interpretation cannot change at each observation. A finite grid that excludes the actual continuous parameter does not satisfy the null-family assumption merely because a nearby grid point exists.

## 3. Cost allocation and the resource-frequency counterexample

For installed source-conditional predictive laws, compute

\[
D_{ij}(a)=\sum_o p_i^a(o)\log\frac{p_i^a(o)}{p_j^a(o)}.
\]

`pairwise_kl` retains exact support mismatches, including infinite KL; it does not silently smooth the channel. Finite KL is passed to

\[
\max_{y\ge0,v}v,
\quad c^\top y=1,
\quad \sum_a y_aD_{ij}(a)\ge v\quad(j\ne i),
\qquad \lambda_a=\frac{y_a}{\sum_b y_b}.
\]

The implementation solves equivalent resource fractions `z_a=c_a*y_a`, then converts them to observation frequencies. It normalizes the rate coefficients before calling the LP solver so small positive differences are not automatically lost to an absolute solver tolerance.

An analytic counterexample is

\[
D=\begin{pmatrix}1&0\\0&9\end{pmatrix},
\qquad c=(1,9).
\]

The optimum resource fractions are `(0.5, 0.5)`, but the observation frequencies are `(0.9, 0.1)`. The achieved worst-opponent evidence rate is `0.9/1.8=0.5`. Using `(0.5,0.5)` as observation frequencies yields `0.5/5=0.1`, five times worse. This test is algebraic and does not depend on a favorable simulator instance.

Only the incumbent is selected by the source posterior. Every other legal source supplies a constraint regardless of its posterior mass, including numerical zero. With only two sources there is one opponent; the LP reduces to selecting a best `D/c` action. A two-source pilot therefore cannot demonstrate the multi-source allocation mechanism.

## 4. Coverage, zero pairs, and escape from an M2 tube

The executed distribution is

\[
\rho_t=(1-\epsilon)\lambda_t+\epsilon\nu,
\]

where `nu` is a fixed source-independent action distribution, uniform by default. `epsilon=0` is supported only as an explicit no-coverage ablation; it loses the persistent-coverage premise. The code reports the entire distribution, its floor, expected cost, and optionally the sampled mixture component. If a caller samples the returned probabilities itself, it must record actual action counts and costs.

`exploit_mask` restricts the normal LP only. Coverage retains access to all globally legal actions. When the complete-opponent LP has zero value, an explicit or rotating legal challenger is compared using

\[
\operatorname{score}_{ij}(a)
=\frac{\min\{D_{ij}(a),D_{ji}(a)\}}{c_a}.
\]

The challenger search can leave the M2 return tube. An outside action is labeled `tube_escape_challenge`. If the pair is indistinguishable under all actions, the planner labels that fact and executes coverage. It never substitutes EIG for these branches. Infinite-KL installed models use the same explicitly labeled pair-challenge fallback instead of an invalid LP containing infinite coefficients; no claim of full-LP optimality is made for that branch.

The symmetric pair score and tube escape are this implementation's engineering decisions. They are not attributed as new equations from TIT2025 or the cost-ASHT paper.

All coverage actions are paid. The expected coverage cost per decision is `epsilon * dot(nu,c)`, and the total is `dot(rho,c)`. These expected-cost equations are not pathwise budget guarantees. A mission controller must reserve resources, enforce the realized travel/dwell budget, and use the same accounting for every comparison. A tube mask represents a navigational proposal, not a safety constraint: truly forbidden actions must be excluded from the globally legal action set before calling this planner.

## 5. Why a wrong high posterior cannot shut down coverage

For exact simple channels, a true source `s*`, a false source `j`, and a nonterminating sequence of actions,

\[
\mathbb E_{s_*}\left[
\Delta\log\frac{L_{s_*}}{L_j}\mid\mathcal F_{t-1}
\right]
=\sum_a\rho_t(a)D(p_{s_*}^a\Vert p_j^a)
\ge\epsilon\sum_a\nu(a)D(p_{s_*}^a\Vert p_j^a).
\]

No source-posterior multiplier appears on the right. With positive initial prior, positive separating coverage information for every false alternative, and suitable bounded-increment or martingale large-number conditions, accumulating observations can overcome a finite initial odds deficit. For a fixed finite nuisance family, the separating condition must hold against every false `(source,nuisance)` state, or an appropriate cumulative-divergence version must be proved.

The statement does not guarantee five-step recovery, recovery after the true source has been physically deleted, recovery from an exactly zero initial prior, or recovery under a misspecified channel. If a false source with another emission amplitude can reproduce every true observation law, no action policy supplies missing identifiability.

The tests include an installed two-source channel with prior probability `1e-9` on the true source and fourteen informative outcomes. The posterior recovers above `0.999`, while the fresh audit initially contains both sources and the planner continues producing actions. This is a controlled mechanism test, not a probability-of-recovery claim for GADEN or a real UAV.

## 6. Audit construction and its exact scope

Let an audit begin after a past-measurable time `t0`. Its source/nuisance log likelihood begins at zero:

\[
A_{sr}(t)=\sum_{k=t_0+1}^{t}\log P_k(a_k,s,r,o_k).
\]

For each null source `s`, choose positive fixed weights over all other source/nuisance states; the default is uniform. The weights do not come from the old source posterior. Define

\[
Q_{-s}(t)=\sum_{j\ne s,r} w^{(-s)}_{jr}\exp A_{jr}(t),
\qquad
E_s(t)=\frac{Q_{-s}(t)}{\max_r\exp A_{sr}(t)}.
\]

The code freezes the alternative one-step prediction before the outcome and accumulates its log probability. It equals the fixed-mixture path likelihood above; the equality is tested numerically. The null uses the maximum of products for a single shared nuisance, not the product of a new maximum at each step.

For example, nuisance values with Bernoulli probabilities `0.1` and `0.9`, followed by outcomes `1,0`, both have likelihood `0.09`. The correct null supremum is `0.09`, whereas changing nuisance after each observation gives `0.81` and changes the model. Against an alternative with probability `0.5`, the correct e-value is `0.25/0.09`.

### Model-relative risk theorem

Suppose the true null source and a fixed true nuisance `r*` are included, all tables are the actual proper conditional laws given the same past, the alternative prediction is normalized and predictable, and observation increments have their claimed dependence law. Then

\[
E_s(t)\le \frac{Q_{-s}(t)}{\exp A_{sr_*}(t)}=:M_t.
\]

`M_t` is a nonnegative test supermartingale under the true null. With absolute continuity/full support it is the usual mean-one likelihood-ratio martingale. Allowing exact zero probabilities can lose mass on null-impossible outcomes, hence the more general supermartingale wording. Ville's inequality gives

\[
P_{s,r_*}\{\exists t:E_s(t)\ge1/\alpha\}\le\alpha.
\]

The supremum-denominator statistic need not itself be a supermartingale; domination supplies its e-process guarantee. All adaptively chosen actions are permitted when they use only the past. The finite enumeration test evaluates every binary outcome path through seven steps, under every fixed nuisance, using adaptive actions and checking the crossing event at every prefix.

The returned sets are:

- `compatible_now`: current `log E_s < log(1/alpha)`, allowing reentry.
- `not_rejected_since_start`: running maximum of `log E_s` remains below threshold.

Neither set is a source probability distribution. A singleton-list stop has model-relative wrong-source error at most alpha because a wrong singleton excludes the one true source; no additional factor equal to the number of source candidates is needed for that coverage statement. Repeatedly starting new audits requires alpha spending or another valid combined construction. An empty list cannot be turned into a certified winner by normalizing inverse e-values.

### Estimated channels and error models

An empirical histogram, Gaussian model, copula, or learned conditional law does not become exact because it was fit only on past data. For such channels, the software's alpha is conditional on the installed family. Physical error control is unproved. An external simultaneous family-inclusion guarantee `1-beta`, together with valid maximization over that family, could support an `alpha+beta` bound; merely having four independent seeds does not establish it.

Finite corruption can be modeled in the **joint** observation law. One test uses a common bit error that flips both sensor bits together, so joint outcomes `01` and `10` have probability zero; the e-value uses the full joint probability. This is not two independent bit errors, a Hamming-distance acceptance rule, or a robustness guarantee against arbitrary physical corruption. An outcome with zero likelihood under every installed state raises `ImpossibleObservationError` without inventing confidence.

## 7. Fourth-round scientific claim boundary

The following OCB figures were reported by the integrating parent after its frozen, training-only probe selection; this module's author did not rerun or tune that experiment:

|Frozen pilot comparison|Reported result|Permitted interpretation|
|---|---:|---|
|Mean concentration|31/40 development snapshots|A common concentration-only reference for this pilot|
|Raw joint Gaussian|40/40|The selected spatial pair contains useful joint information on these development worlds|
|Invertible even/odd Gaussian|40/40; numerical equivalence difference `4.51e-17`|Expected reparameterization equivalence; no new information or filter innovation|
|Static M1 histogram|31/40|No demonstrated improvement over the reported mean reference in this frozen run|

The selected probes were 12 and 17, separated by 7 m. They are an offline spatial pair, not an established simultaneous UAV sensor baseline. The sample is four development worlds times ten snapshots, not forty independent seeds. There are only two sources. It does not validate a continuous-time MNM, an M2 flight controller, multi-candidate M3 action mixtures, or a physically calibrated e-process.

Subsequent M3 control matrices that sample an installed `FiniteChannel` must be labeled **Level 1 / conditional mechanism tests**. They can expose frequency-conversion errors, zero-pair paralysis, posterior-dependent loss of exploration, nuisance mistakes, and double counting. They cannot upgrade the observed pilot into evidence of a new physical localization algorithm outperforming a raw-joint baseline.

## 8. Verification and algorithm provenance

Standard-library test command:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p test_m3_audit.py -v
```

At fourth-round verification, all 18 tests pass. They cover the analytic cost counterexample, weak-KL scaling, two-source limit, complete legal candidates, explicit challenges, tube escape, paid global coverage, support singularities, fixed nuisance, alternative normalization, exact finite-path risk, list reentry, incorrect prior recovery, observation ownership, prediction freezing, zero-alternative paths, and model support failure. A zero numerator and impossible null cannot silently produce a NaN: a suffix impossible under every installed state is rejected before mutation; otherwise at least the null or its full positive-weight alternative mixture has nonzero path mass.

Primary algorithm sources:

- [Hsu and Wang, TIT2025, DOI 10.1109/TIT.2025.3588527](https://arxiv.org/html/2405.06554v3): all-pair evidence/exploration theory in specified channels. Its asymptotic theorem is not claimed as this five-step implementation's guarantee.
- [Nonhomogeneous-cost ASHT, 2025 preprint / ICASSP2026](https://arxiv.org/html/2509.11632v3), [official ICASSP entry](https://www.cmsworkshops.com/ICASSP2026/view_paper.php?PaperNum=7206&bare=1): ratio of expected divergence to expected cost and the correct allocation conversion.
- [2025 sequential split-likelihood application](https://arxiv.org/html/2508.21594v1): an explicit recent use of predictable alternative densities and composite-null likelihood maxima. Likelihood ratios, Ville's inequality, and universal-inference domination are classical tools, not inventions of this implementation or that application.

The challenger score, explicit M2 tube escape, API event ledger, and combined software architecture are the present implementation choices. Their practical benefit beyond the specified mechanism tests remains to be measured with equal resources and an independent observation backend.
