# PFDI-V12: rate-complete causal spatiotemporal source inference

## 1. What V11 actually established

V11 showed a real positive signal on some realizations, but it did not establish
a general method. The same frozen binary improved all three original seeds, yet
the expanded qualification improved only 11/15 pairs, only 8/12 newly sampled
pairs, and produced one catastrophic H01 regression. The failure is not a
binary mix-up. The implemented operator declared `transport_members=8` and
`model_error_members=8` in its JSON contract while `applyMEAci()` actually used
`transportMembers=0` and a 3 x 3 x 2 x 3 = 54 analytic component family.

Four coupled mathematical defects explain the observed failure pattern:

1. V11 conditioned on the total number of hits. This removed the absolute hit
   rate, even when 119/128 measurements were hits.
2. Candidate log-evidence was converted to normal ranks. Rank normalization
   removed the physical scale of Bayes factors and forced a broad redistribution
   even when evidence was weak.
3. Event parity was called a temporal channel, but it was not an eigenchannel
   learned from source contrast versus temporal fluctuation.
4. The nominal 8 x 8 physics factorization was not executed, so temporal
   realization and structural model error were not separately identifiable.

PFDI-V12 replaces that source-scoring operator as one coherent model. It does
not add a posterior repair, entropy widening rule, rescue threshold, or planner
change.

## 2. Causal observation model under adaptive motion

Let the static gas source be `S=s`. At event `i`, the robot position, wind,
threshold, elapsed time, and completed measurement-block identity form the
design variable

\[
D_i=(x_i,w_i,q_i,\Delta t_i,k_i).
\]

The PMFS controller chooses `D_i` using only the past filtration
`F_(i-1)`. Therefore inference conditions on the realized adaptive design:

\[
p(h_{1:n}\mid s,D_{1:n})=
\prod_{i=1}^{n}p(h_i\mid s,D_i,\mathcal F_{i-1}),
\]

where `h_i` is the binary threshold-crossing observation. No future event,
source truth, final error, or posterior-derived tuning variable may enter the
likelihood. This is the causal boundary of the method.

The deployed V12 posterior is maintained separately from native PMFS source
scoring:

\[
q_n(s)\propto p_0(s)\,p(h_{1:n}\mid s,D_{1:n}),
\]

where `p_0` is geometry-only free-cell mass. V12 replaces PMFS's source-evidence
operator, while retaining the PMFS map, native background simulation, motion
controller, navigation stack, sensing budget, and official final-error metric.
For the V12 evidence ledger itself, the free map is partitioned once into
immutable non-overlapping `2 x 2`-cell carriers (clipped at map boundaries);
this prevents the adaptive native quadtree from changing the hypotheses after
evidence has accumulated. It must not
multiply a second likelihood into a native PMFS posterior constructed from the
same observations, because that would double-count evidence.

## 3. Nested ensemble contract: 8 for the main method, 8 x 8 only for the full method

There are two immutable, nested deployment contracts. They may not be renamed
or conflated in reports:

- **V12-M (main innovation):** `R=8` transport members and `B=1` nominal
  discrepancy member. This is the only contract used to qualify RC-SD-TFEI.
- **V12-F (full PFDI):** the identical frozen V12-M operator plus `B=8`
  independently calibrated TADM members, giving `R x B = 64` crossed logits.

If the independent TADM calibration artifact is missing or fails its
identifiability gate, V12-F is unavailable. The program must fail closed; it
must not repeat the nominal member eight times and call that an 8 x 8 ensemble.
This makes the paper ablation executable as `C`, `C+S`, `C+D`, and `C+S+D`.

For every candidate source `s`, exact observed design `D_(1:n)`, and transport
member `r`, the physical simulator produces a causal hit-frequency trajectory
`hat p_(sr,1:n)` from `N_sim` recorded timesteps. Define

\[
\bar p_{sr,i}=\frac{N_{sim}\widehat p_{sr,i}+1/2}{N_{sim}+1},
\qquad
a_{sr,i}=\operatorname{logit}(\bar p_{sr,i}).
\]

This Jeffreys posterior mean maps zero and one simulated frequencies to finite
logits without an empirical floor and converges to the physical frequency as
`N_sim` grows.

The eight `eta_r` are stochastic plume realizations at fixed physical
parameters. Each member has one trajectory-global counter-based random-field
root key `(global_seed, transport_member_id, transport_substream)`; simulator
time step and draw index form its internal counters. Candidate identity,
candidate refinement id, source-update id, observed event id, and hit outcome
are excluded. Thus member label `r` denotes the same exogenous realization
across candidates and source updates, giving common random numbers and making
the HMM persistence parameter physically meaningful.

The ensemble root seed is a **method seed**, frozen once before House seeds are
selected and shared by every qualification run. It is not the GADEN realization
seed and cannot change from one ON arm to another. Therefore a favorable test
seed cannot acquire a specially matched simulator ensemble.

### 3.1 Truth-blind physical response bank

The physical map generated by `(carrier s, transport member r)` depends on the
occupancy/visibility map, frozen simulator settings and method seed, but not on
the robot trajectory or observed hit outcomes. V12 therefore evaluates every
immutable carrier-member pair once and stores the full hit-frequency map in a
House-specific **response bank**. Later source updates only sample these frozen
maps at the newly observed positions. This is exact memoization of the declared
simulator, not a surrogate, fitted likelihood, or offline performance test.

The bank is built before qualification seeds are selected or any source truth
is read. Its binary header contains map geometry and occupancy, ordered carrier
manifest, simulator settings, `R=8`, method seed and transport substream. The
launcher verifies its SHA-256 and the runtime verifies every header field;
missing or mismatched banks fail closed. Bank construction wall time, size and
hash are reported separately from the 300 s localization budget. No bank may be
rebuilt between seeds. This amortization makes the source-update cost depend on
`events x carriers x R`, not on rerunning the physical plume simulator, and is
the scientific route to a 100--120 s update cadence.

In V12-F only, let `z_b` enumerate `{-1,+1}^3`, let `L_delta` be the Cholesky
factor of an independently calibrated coefficient covariance, and set
`delta_b=L_delta z_b`, each with weight `1/8`. These are normalized two-node
Gauss-Hermite cubature points. TADM acts in a transport-coordinate discrepancy
field:

\[
B_{s,i}=\left[1,\frac{\xi_{\parallel,s,i}}{D_{map}},
                 \frac{\xi_{\perp,s,i}}{D_{map}}\right],
\qquad
a_{srb,i}=a_{sr,i}+B_{s,i}\delta_b,
\]

where the signed along-wind and cross-wind coordinates come from measured wind
and source-to-observation displacement, and `D_map` is the frozen free-space
map diagonal. The coefficients represent global log-odds bias, downwind-range
distortion, and lateral plume displacement. They are static over a trajectory,
not plume-realization variables.

`L_delta` is estimated only from a separately hashed, known-source calibration
bank by fitting this residual field to simulator-versus-sensor logit residuals.
Calibration uses no House qualification outcome, final localization error, or
candidate truth. Its rank, conditioning, predictive residual score, and hashes
must pass `CALIBRATION_PROTOCOL.md`; otherwise only V12-M may run.

Thus V12-M executes eight actual physical plume realizations. V12-F constructs
64 crossed logits from those eight simulations and an explicit static
discrepancy model. Temporal covariance varies `r` only; structural discrepancy
varies `b` and is marginalized once. The two factors are identifiable by
construction rather than mixed into 54 unrelated analytic components.

## 4. RC-SD-TFEI: protect increment rate, filter relative spatiotemporal patterns

V11's global conditional likelihood discarded total hit count. V12 instead
separates the absolute rate of each immutable likelihood increment from the
relative pattern across its measurement blocks and event times.

Let `g_i` identify the immutable source-update likelihood increment to which
event `i` belongs. `Q` contains one normalized indicator column per increment,
not per StopAndMeasure block, and

\[
P=I-QQ^T.
\]

`QQ^T a` identifies the incrementwise constant logit subspace and `Pa` retains
relative differences among measurement blocks/events inside an increment. Only
`Pa` is passed through the stable spatiotemporal operator. Using one indicator
per StopAndMeasure block is forbidden: because the platform is nearly static
inside a block, that choice would project out almost all candidate pattern.
The protected quantity is the raw increment mean probability, restored exactly
by the intercept solve below.

The source average below is not taken over the adaptively selected PMFS
candidates. It uses a geometry-stratified subset of the immutable V12 carriers.
Let `J=min(64,N_carrier)`. The first carrier center is closest to the free-space
centroid; subsequent carrier centers are selected by deterministic farthest-point
sampling. All ties use the ordered carrier ID. The selected response maps are
views into the same frozen response bank used for candidate scoring; no second
simulation family is introduced. The ordered carrier list and occupancy-map
hash are frozen. The number 64 is a computational design constant, not selected
from localization outcomes. Consequently, planner choices and current
posterior support cannot change the operator used to score observations.

For a calibration replica fold of the V12-M bank, define

\[
C_S=\operatorname{Cov}_s\!\left[
\mathbb E_r(P a_{sr})\right],
\]

\[
C_\eta=\mathbb E_s\!\left[
\operatorname{Cov}_r(Pa_{sr})\right].
\]

The Bernoulli observation model below already accounts for binary hit/miss
sampling noise. Adding an empirically estimated sensor covariance to the
eigen-denominator would count that uncertainty a second time and, in the
current simulated Houses, would require calibration data that do not exist.
Therefore V12-M uses `M_0=C_eta`. Let `d` be its dimension and define the
non-tunable numerical ridge

\[
\rho=\sqrt{\epsilon_{machine}}\,
\max\!\left(\operatorname{tr}(M_0)/d,1\right).
\]

Then set

\[
M=C_\eta+\rho I,
\qquad
B=M^{-1/2}C_SM^{-1/2}.
\]

Let `B=U diag(lambda_i) U^T`. These are genuine
source-information/temporal-fluctuation eigenchannels. No `lambda>1` gate is
used. Every numerically supported channel receives the continuous Wiener
weight

\[
w_i=\frac{\max(\lambda_i,0)}{1+\max(\lambda_i,0)}.
\]

The stable pattern operator is

\[
\mathcal K=M^{1/2}U\operatorname{diag}(w_i)U^TM^{-1/2}P,
\]

For any raw member logit vector `a`, first form its centered pattern

\[
u=\mathcal K a.
\]

For immutable increment `g`, retain the member's raw physical mean hit probability

\[
\pi_g(a)=\frac{1}{n_g}\sum_{i:g_i=g}\sigma(a_i).
\]

There is a unique scalar intercept `c_g` satisfying

\[
\frac{1}{n_g}\sum_{i:g_i=g}\sigma(c_g+u_i)=\pi_g(a).
\]

It is found by deterministic bisection. A guaranteed initial bracket is
`[logit(pi_g)-max(u_i), logit(pi_g)-min(u_i)]` over the increment, so there is no
fixed empirical search range. The final filtered logits are

\[
\widetilde a_i=c_g+u_i,\qquad g_i=g.
\]

Thus RC-SD-TFEI preserves the predicted absolute hit rate in every immutable
increment exactly in probability space, not merely the mean logit, while still
allowing block-to-block/time-relative source structure to be filtered.

This is not PCA. PCA maximizes total variance; RC-SD-TFEI retains absolute
block rate and continuously preserves only source-discriminative pattern
energy that is stable against plume realization.

Replica cross-fitting prevents a finite ensemble from selecting and scoring
the same fluctuations. Fold A learns `K_A` from transport members `{0,2,4,6}`
and scores `{1,3,5,7}`; fold B swaps the roles. Event parity is never used to
define a temporal mode.

## 5. Proper causal likelihood and TADM marginalization

For fold `f` and scoring transport state `r`, V12-M sets

\[
\widetilde p_{sr,i}^{(f)}=\sigma(\widetilde a_{sr,i}^{(f)}).
\]

For V12-F only, TADM first constructs `a_srb`; the same frozen operator then
filters and rate-matches every `(r,b)` member, giving

\[
\widetilde p_{srb,i}^{(f)}=\sigma(
\widetilde a_{srb,i}^{(f)}).
\]

Each source update constructs the operator only for the newly completed
measurement blocks, using the frozen geometry-stratified source library and
no observed hit values. That operator is then immutable and stored with the
increment. Earlier increments are never re-fitted after later outcomes or
candidate refinements.

Let `ell_(u,X)^(f)(s)` be the fold likelihood produced from the raw events that
arrived since update `u-1`, using operator `K_u`. Cumulative evidence is

\[
L_{n,X}^{(f)}(s)=\prod_{u=1}^{n}\ell_{u,X}^{(f)}(s).
\]

Production must not concatenate all earlier raw events into the newest window
and fit them again. Replay means re-evaluating the stored sequence of immutable
increments, not a growing-reservoir re-fit.

Transport realization is a block-persistent latent state. The physical PMFS
replica is a finite-time hit-frequency map, not an instantaneous plume movie,
so an exponential event-by-event persistence time would be unidentifiable. The
transition is instead fixed by the measurement protocol:

\[
K_{rr'}(i)=
\begin{cases}
\mathbf 1[r=r'], & \text{event }i\text{ is in the same StopAndMeasure block},\\
1/R_f, & \text{event }i\text{ starts a new block}.
\end{cases}
\]

Thus one transport member explains the correlated hit sequence acquired while
the vehicle is stationary, and the member is marginalized anew after motion.
There is no fitted persistence time, forgetting factor, or outcome-dependent
reset gate.

For V12-M the causal forward recursion has no discrepancy index:

\[
\alpha_i^{(f)}(r)=
\operatorname{Bern}(h_i;\widetilde p_{sr,i}^{(f)})
\sum_{r'}K_{r'r}(i)\alpha_{i-1}^{(f)}(r'),
\qquad
\ell_{u,M}^{(f)}(s)=\sum_r\alpha_{u,end}^{(f)}(r).
\]

For V12-F and each static discrepancy member `b`, the recursion is

\[
\alpha_i^{(f,b)}(r)=
\operatorname{Bern}(h_i;\widetilde p_{srb,i}^{(f)})
\sum_{r'}K_{r'r}(i)\alpha_{i-1}^{(f,b)}(r').
\]

TADM marginalizes the static structural mismatch once over the complete
trajectory:

\[
\ell_{u,F}^{(f)}(s)=\sum_{b=1}^{8}\omega_b
\sum_r\alpha_{u,end}^{(f,b)}(r).
\]

The A/B fold identity is global over the trajectory. Each fold is accumulated
through every immutable increment before the two folds are mixed. Mixing A and
B inside every update and then multiplying updates is forbidden because it
would create an unintended `2^U`-component model after `U` updates.

Finally, with `X` equal to `M` or `F`,

\[
\boxed{
L_{n,X}^{V12}(s)=\tfrac12 L_{n,X}^{(A)}(s)+
\tfrac12 L_{n,X}^{(B)}(s)
}
\]

and

\[
\boxed{
q_{n,X}(s)=\frac{p_0(s)L_{n,X}^{V12}(s)}
{\sum_{s'}p_0(s')L_{n,X}^{V12}(s')}
}.
\]

Both likelihoods retain hit and miss probabilities, including saturated runs,
use absolute probability scale, and contain no candidate ranking transform.
V12-M marginalizes the dynamic transport state once; V12-F additionally
marginalizes the static discrepancy state once.

## 6. Reversible cumulative contract

The online recursion and a full replay from the geometry prior using the stored
sequence of immutable update operators must agree:

\[
\max_s|q_n^{online}(s)-q_n^{replay}(s)|\le 10^{-10}
\]

in double-precision unit tests. The qualification implementation does not
refine V12 carriers: the deterministic non-overlapping carrier partition is
immutable for the entire 300 s arm. Native PMFS may still refine its internal
simulation quadtree, but that adaptive object cannot enter the V12 hypothesis
manifest. Any carrier ID, rectangle, coverage, map or bank change fails closed;
posterior mass is never copied to a changed hypothesis. New evidence can reverse
an early wrong source ranking because no hard-zero likelihood, accepted-update
latch, or carried posterior gate exists. A rejected numerical update leaves the
last valid state unchanged and is classified as infrastructure failure, not
scientific abstention.

## 7. What is and is not the main innovation

The main innovation is V12-M RC-SD-TFEI: a causal, rate-complete observation operator
that extracts source-discriminative spatiotemporal modes against stochastic
plume fluctuation and inserts them before Bayesian source accumulation.

TADM is the optional second mechanism in V12-F: a static structural-discrepancy quadrature that
is crossed with, but not merged into, the temporal ensemble and marginalized
once at trajectory level.

PFDI-V12 is the unified inference framework. The planner is not an innovation
and remains frozen. No posterior smoothing, entropy widening, decoder,
truth-aware gate, or tuned rescue rule qualifies as part of V12.

## 8. Claims permitted before and after closed-loop validation

Before qualification, the only permitted claim is:

> Formula-code consistency and synthetic failure-mode closure have been
> established for a frozen V12-M candidate; no performance claim is made.

V12-M is qualified first against PMFS. V12-F may be tested only after V12-M is
frozen and its independent TADM calibration gate passes. After a truth-blind,
fresh-seed, paired 300 s House01/02/03 qualification, a performance claim
requires all preregistered conditions: pooled official PMFS error improvement
at least 10%, at least two of three Houses improved, no catastrophic regression,
no false-confident collapse, and secondary evidence that source mass/rank
improved rather than only the top-five centroid.
