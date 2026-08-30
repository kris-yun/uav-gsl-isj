# CTT H01 wind-conditioned M1 — pregeneration freeze addendum

Status: `FROZEN_BEFORE_BANK_GENERATION`

Parent scientific contract:
`docs/CODEX_CTT_H01_WIND_CONDITIONED_M1_BANK_AND_GATE_20260830.md`.

This addendum closes implementation degrees of freedom that were not explicit
in the parent contract.  It does not change the causal first-passage method,
the wind/transport/route split, the physical threshold, or any scientific
gate.  Any change to Sections 1--6 after opening TEST outputs invalidates the
qualification.

## 1. Exact data split

- source query carriers: all frozen H01 carriers `0..209` in every split;
- source query geometry manifest: `H01_persistent_carriers.csv`, SHA-256
  `94525a3c3abc6b309a5a64dcee9bd57d34613f2fca3ce960df7dc1d57fbbf8ed`;
- candidate geometry uses those PMFS quotient-region centroids; nuisance
  3-D placements from the physical generator are marginalized targets and
  must not be substituted as candidate-centroid features;
- TRAIN wind contexts: `0,3,5,6,8,9`;
- VALIDATION wind contexts: `4,7`;
- TEST wind contexts: `1,2`;
- TRAIN transport keys: `0..5`;
- VALIDATION transport keys: `0..5` only;
- TEST transport keys: `6,7` only;
- TRAIN routes: `4001,4002,4003`;
- VALIDATION route: `4004`;
- TEST route: `4005`.

No TEST wind context, TEST transport key, route 4005 source-evidence result,
source rank, localization error, or closed-loop outcome may be read before the
two model checkpoints are frozen.

## 2. Physical observation and generator provenance

The bank must preserve

`native physical ppm -> run-persistent sensor -> measured ppm -> native 0.2 s
samples -> first passage F in {0..79, never}`.

Before the first full-bank job, `02_BANK_CONTRACT.json` must resolve and hash:

- H01 map, obstacle geometry, environment and converted wind files;
- the exact source carrier 3-D support and quotient mapping;
- source release strength/rate and all source-emission parameters;
- legal source height/placement rule;
- GADEN filament/diffusion/noise/boundary/time-origin parameters;
- transport RNG initialization hook, key-to-seed mapping and substream rule;
- query binary, linked GADEN library, overlay and source commit;
- route schedules and their time origins;
- sensor model source, `dt=0.2 s`, dead time, time constant, initial state;
- measured first-passage threshold `0.1 ppm` and exactly 80 consumed samples.

Missing or ambiguous provenance is terminal
`STOP_CTT_H01_M1_BANK_INVALID`; values may not be inferred from result files.

One `(source, wind context, transport key)` plume realization is sampled on all
five routes only if an explicit time-origin parity check proves that reuse is
valid.  Each route has an independent sensor state initialized only at its own
causal start.

The ten H01 contexts are frozen as ten native CFD wind snapshots, not as
trajectory-derived estimates.  Context `c in 0..9` uses the immutable original
H01 `wind_iteration_(c+1)` payload for every native wind slot `0..10` in an
isolated context directory.  Thus every context is a complete static spatial
wind field accepted directly by the unchanged GADEN wind loader.  The original
payload is never edited.  Context hashes are recorded before any plume run.
This tests held-out spatial wind media; it does not claim generalization to an
independent CFD building or to temporally evolving wind.

The original four-vCPU generation environment is reproduced with
`OMP_NUM_THREADS=4` and `OMP_DYNAMIC=FALSE`. On the expanded 12-vCPU VM, three
independent native field jobs run concurrently. A preregistered
source/context/key file generated before and after the VM change must be
bitwise identical; otherwise the expanded VM is forbidden.

## 3. Deployable wind-context contract

The conditional model may consume only numerical wind features available
causally at the scored stop.  For the H01 simulation qualification these are
sampled from the exact wind field used by the forward simulation at the
historical route poses and timestamps.  The following are forbidden:

- wind context ID/name or one-hot encoding;
- hidden CFD frame/phase identifiers;
- future wind samples;
- a separately estimated wind field that did not generate the forward sample;
- source truth, posterior, rank, localization error or planner outcome.

The simulation claim is therefore explicitly scoped to
`simulator-known causal wind field`.  A real-robot claim requires a separate
sensor-available wind observation contract and is not established here.

### 3.1 `W_gen` is not silently equated with `W_online`

`W_gen` is the complete native CFD field used only by GADEN to generate the
plume. The network never receives that field, its file name, context index, or
hidden CFD phase. `W_online` consists only of local wind samples at the UAV's
already visited poses and timestamps. In simulation they are queried from the
same field for parent consistency; in an eventual robot they must come from a
source-independent calibrated local anemometer. Therefore this H01 experiment
qualifies simulation inference, not real-robot wind reconstruction.

| feature_name | physical meaning | frame | timestamp semantics | training source | runtime simulation source | real-robot source | future? | simulator-only? |
|---|---|---|---|---|---|---|---|---|
| `wind_stop_mean_{x,y,z}` | mean local velocity over the consumed stop | H01 map/world | current 80 samples, available when update fires | exact local samples of `W_gen` at UAV poses | local wind samples already delivered during stop | calibrated onboard anemometer | NO | NO (quantity); exact simulator provenance is qualification-only |
| `wind_stop_std_{x,y,z}` | local intermittency over consumed stop | H01 map/world | current 80 samples | same as above | same as above | calibrated onboard anemometer | NO | NO |
| `wind_stop_final_{x,y,z}` | final local wind sample | H01 map/world | final consumed sample at update time | same as above | same as above | calibrated onboard anemometer | NO | NO |
| `wind_prefix_mean_{x,y,z}` | causal route-history mean | H01 map/world | route start through current stop end | exact local causal history | buffered local wind history | buffered anemometer history | NO | NO |
| `wind_prefix_std_{x,y,z}` | causal route-history variability | H01 map/world | route start through current stop end | exact local causal history | buffered local wind history | buffered anemometer history | NO | NO |
| `wind_along,wind_cross` | stop-mean horizontal wind projected onto candidate-to-query axes | candidate-relative in H01 map | derived at current update | preceding stop-mean plus public candidate/query coordinates | same causal derivation | same causal derivation | NO | NO |

The full spatial field `W_gen`, wind context ID, wind-file identity, hidden
iteration/phase and any sample after the current update are forbidden neural
inputs. Equality is required only between the **local training wind samples**
and the local samples of the field that generated that synthetic plume.

## 4. Frozen input vector

No carrier ID embedding is used.  The ordered float input columns are:

1. `source_x, source_y`;
2. `query_x, query_y`;
3. `dx=query_x-source_x, dy=query_y-source_y, distance, unit_dx, unit_dy`;
4. `carrier_half_diagonal` on the frozen PMFS grid;
5. `stop_start_time, causal_path_length, delta_previous_stop_x,
   delta_previous_stop_y, sin(yaw), cos(yaw)`;
6. for the exact generating wind sampled over the current 80-sample stop:
   componentwise `mean(3), std(3), final(3)`;
7. for exact generating wind over the causal route prefix ending at the stop:
   componentwise `mean(3), std(3)`;
8. current-stop mean horizontal wind projected along and across the
   source-to-query displacement: `wind_along, wind_cross`.

Total input dimension is 33.  Normalization is TRAIN-only columnwise mean and
population standard deviation; any standard deviation below `1e-6` is replaced
by `1.0`.  NaN/Inf is terminal.  No additional obstacle descriptor or learned
embedding may be added in this H01 qualification.

The STATIC-WIND comparator receives the identical 33-dimensional vector and
identical architecture.  Columns 17--33 are replaced by their TRAIN-set means
before normalization.

## 5. Frozen neural solver

- encoder: `Linear(33,128) -> SiLU -> Linear(128,128) -> SiLU ->
  Linear(128,128) -> SiLU`;
- survival head: `Linear(128,1)`;
- conditional phase head: `Linear(128,80)`;
- probability factorization:
  `p(F=t)=sigmoid(survival)*softmax(phase)[t]`,
  `p(F=never)=1-sigmoid(survival)`;
- loss: `BCE(ever) + CE(first_passage_bin | ever)`, unit coefficients;
- optimizer: AdamW, learning rate `2e-3`, weight decay `1e-5`;
- batch size `2048`, maximum epochs `50`, patience `7`;
- improvement tolerance `1e-5` on validation factorized loss;
- model/data-loader/random seed `20260835`;
- checkpoint tie rule: earliest epoch attaining the minimum accepted
  validation loss;
- checkpoint selection reads validation physical loss only.

CONDITIONAL and STATIC-WIND are trained from the same initialization seed and
data order.  No architecture sweep, restart selection, ensemble, class weight,
temperature, calibration or loss reweighting is permitted.

## 6. Frozen controls and statistics

- bootstrap seed: `20260835`;
- paired cluster bootstrap replicates: `5000`;
- primary physical-gate cluster: `(source carrier, wind context)`, preserving
  all stops and transport replicates within the cluster;
- report effects separately for TEST wind contexts `1` and `2`;
- additionally report a context-level two-row effect table; it is descriptive
  and is not used to tune or replace the parent gate;
- TIME-PERMUTE uses a SHA-256-derived permutation from
  `CTT-H01-WIND-M1-TIME|wind|transport|source|stop`;
- PHASE_LABEL_SHUFFLE uses a SHA-256-derived candidate permutation from
  `CTT-H01-WIND-M1-PHASE|wind|transport`;
- all mid-ranks use exact floating-point equality; no probability tolerance is
  introduced.

The parent document's physical and source-evidence GO criteria remain binding.

## 7. Runtime Bayesian replacement contract

If and only if both offline gates pass, runtime inference proposes the exact
replacement update

`q_t(s) proportional_to q_{t-1}(s) * p_CTT(F_t | s, causal_context_t)`.

For the same 80 native samples, the native PMFS HIT/NOTHING gas likelihood is
disabled.  Motion, map support and other source-independent native state remain
unchanged.  The observation is consumed exactly once.  There is no multiplication
of CTT and native gas likelihoods, posterior reset, blend, temperature, Top-K
router or learned acceptance gate.

Before any 300-s run, Python/deployment parity must identify the precise PMFS
gas-likelihood call site being replaced and prove exact OFF parity.  This
addendum does not authorize closed loop.

## 8. Terminal boundary

This phase can end only in one of the terminal states listed in the parent
contract.  A PASS authorizes H01 closed-loop development; it is not evidence of
`>=10%` improvement, cross-House generalization or real-robot deployment.
