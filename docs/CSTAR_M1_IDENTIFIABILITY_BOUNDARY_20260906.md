# CSTAR M1 — identifiability boundary before execution

Date: 2026-09-06
Status: **scientific contract, not a proved identifiability theorem**

## 1. What M1 is allowed to claim

M1/PICR studies whether a source-relevant representation can remain stable under
predefined transport/release/sensor perturbations while retaining source
separability. This is an empirical causal-representation claim under controlled
interventions. It is **not** an unconditional theorem that source location is
identifiable from every finite gas/wind/pose history.

The 2026 causal-representation papers used as mother ideas have their own
mixing, variability, alignment and support assumptions. CSTAR does not inherit
those identifiability theorems merely by using an invariance loss.

## 2. Variables

Let

- `S` be the fixed source hypothesis/location;
- `E` be a preregistered nuisance/intervention environment describing transport,
  release and sensor-mechanism variation;
- `H_t` be the causal history available by decision time `t`:
  gas observations, local wind, robot pose, geometry and an explicitly typed
  sensor state/auxiliary channel;
- `Z_S = f(H_t)` be the source representation;
- `pi_t(S)` be the source posterior produced from `Z_S` and the static candidate
  domain.

No future gas/wind, House identity, simulator member identity or source truth is
an M1 runtime input.

## 3. Conditional distinguishability, not universal separation

For two source hypotheses `s_i` and `s_j`, define their intervention-conditioned
history laws under an allowed environment `e` as

`P_e(H_t | S=s_i)` and `P_e(H_t | S=s_j)`.

A source pair is empirically distinguishable only on intervention/support
regions where these laws differ. A convenient diagnostic is a weighted
Hellinger separation

`D_ij(t) = sum_e w_e H^2(P_e(H_t|s_i), P_e(H_t|s_j))`.

CSTAR does not assume `D_ij(t)>0` for every pair and every early history.
If the available history makes two candidate sources observationally
indistinguishable, no deterministic encoder can honestly force them apart
without additional information.

Therefore:

1. same-source perturbation invariance is enforced only for scientifically legal
   same-source intervention pairs;
2. different-source separation is tested only under matched/overlapping context
   where the observation support is sufficient;
3. low-information/unsupported histories must retain broad posterior uncertainty
   or emit an explicit abstention/invalid-source-belief state;
4. finite training-pair separation is never reported as a physical
   identifiability theorem.

## 4. What the intervention pairs mean

Legal same-source nuisance pairs require the **same exact source_xyz** and a
predeclared difference in at least one nuisance mechanism/realization, such as:

- distinct transport realization/seed;
- controlled wind-mechanism perturbation;
- controlled release strength/process perturbation;
- controlled sensor-response perturbation.

A different source placement inside the same quadtree/region is not an
exact-source transport intervention.

Natural differences between historical closed-loop arms are not automatically
`do()` interventions.

## 5. Structural load-bearing rule for zS

All history-dependent source evidence must pass through `zS` before candidate
scoring. The candidate scorer may use candidate-static coordinates/validity,
but it may not directly re-read a history-dependent candidate-relative
wind/pose summary.

The revised research model additionally subtracts the candidate-only evidence
path:

`score(s | H) = g(zS(H), candidate_s) - g(0, candidate_s)`.

Thus, for a fixed candidate set, a posterior change caused by gas/wind/pose must
be mediated by a change in `zS`.

This structural rule only closes a bypass. It does **not** by itself prove that
`zS` is causal or useful.

## 6. Mandatory destructive controls

A formal M1 PASS requires all of the following on held-out controlled data:

1. **zS-zero/mask control**: removing `zS` destroys nontrivial source evidence;
2. **zS permutation control**: permuting `zS` across matched contexts destroys
   source discrimination;
3. **context-only baseline**: context/candidate information without source
   response evidence cannot reproduce the full gain;
4. **source-label permutation**: shuffled source labels remove held-out task
   gain;
5. **no-intervention-loss ablation**: removing the intervention constraint
   worsens same-source nuisance invariance;
6. **source-separation anti-collapse**: different-source representation
   separation and proper source score do not collapse while invariance improves;
7. **uninformative-history test**: zero/near-zero information histories do not
   produce unsupported sharp source certainty.

A result that improves only pairwise `zS` distance, without source proper-score
and destructive-control evidence, is not a causal M1 PASS.

## 7. Formal empirical claim if the gate passes

The strongest allowed wording before broader confirmation is:

> Under the preregistered source/transport/release/sensor intervention family and
> held-out environments tested here, the constrained representation preserves
> more source-discriminative information while reducing nuisance sensitivity
> relative to matched unconstrained/context-only controls.

Do not state that CSTAR has proved global source identifiability.

## 8. Literature boundary

The review specifically checked Kim et al., *On Causal Representation Learning
with Internal Auxiliaries* (UAI 2026, PMLR 337). Its identifiability result is
conditional on assumptions including properties of the mixing process,
variability and alignment, and identifies latent structure up to the stated
equivalence. CSTAR must not cite that result as a ready-made theorem for sparse
robotic gas transport.

Source:
https://proceedings.mlr.press/v337/kim26e.html
