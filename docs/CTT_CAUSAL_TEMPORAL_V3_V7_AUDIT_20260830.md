# CTT causal-temporal audit V3--V7 (House01 offline)

Date: 2026-08-30  
Status: **closed loop NOT authorized**

## Main scientific contract

The paper-level direction remains **causal + temporal + neural**. The forward causal chain is source -> transport -> persistent sensor -> ordered observation. The neural component is not allowed to replace the native physical generator; it must exploit ordered temporal information conditioned on candidate forward predictions.

This branch preserves V3--V7 as an auditable sequence of falsification attempts. No prior NO-GO is overwritten.

## V3 -- soft physics-order-consistent temporal NRE

Fresh subset: 64 sources, trajectory4005/member3.

- chronological Top5: 0.194
- chronological Top10: 0.422
- energy Top5: 0.319
- energy Top10: 0.378
- TIME-PERMUTE wins/losses/ties: 289/28/3
- TIME-PERMUTE sign p: 8.520e-56
- gates: {'time': True, 'physics_non_degradation': False, 'online': True, 'posterior': False}

Verdict: **NO-GO**. Time is strongly load-bearing, but Top5 physical near-order is damaged and geometry-prior posterior safety fails.

## V4 -- physics-certified interval selector

Fresh subset: 48 sources, trajectory4005/member7, disjoint from V1/V2/V3 truth subsets.

- chronological Top5: 0.321
- chronological Top10: 0.408
- energy Top5: 0.287
- energy Top10: 0.379
- TIME-PERMUTE wins/losses/ties: 29/40/171
- sign p: 2.284e-01
- gates: {'time': False, 'physics_non_degradation': True, 'online': True}

Verdict: **NO-GO**. Hard interval containment protects physics but suppresses temporal information.

## V5 -- physics-certified partial-order temporal linear extension

Fresh subset: 40 sources, trajectory4005/member3, disjoint from V1/V2/V3/V4 truth subsets.

- projected Top5: 0.145
- projected Top10: 0.250
- energy Top5: 0.315
- raw temporal Top10: 0.390
- projected TIME-PERMUTE wins/losses/ties: 119/53/28
- sign p: 5.278e-07
- certificate violations: 0
- gates: {'time': False, 'physics_non_degradation': False, 'online': False, 'certificate': True}

Verdict: **NO-GO**. Kahn linear extension causes cascading unlock/reordering and damages early physical ranking despite zero hard-order violations.

## V6 -- Dykstra isotonic projection

Fresh subset was preregistered as 16 sources. The first fresh evaluation stopped before a scientific metric verdict because the frozen numerical solver failed its own dense certificate after 1000 sweeps (max residual about 1.2e-7 > preregistered 1e-8 rank-equivalence tolerance).

Verdict: **IMPLEMENTATION NO-GO / no scientific performance claim**. The V6 source subset is conservatively treated as consumed.

## V7 -- exact dual NNLS isotonic projection

Fresh subset: final disjoint 10 sources, trajectory4005/member3. The NNLS dual solver satisfies the dense physical certificate.

- projected Top5: 0.380
- projected Top10: 0.520
- energy Top5: 0.460
- raw temporal Top10: 0.380
- TIME-PERMUTE projected Top10: 0.800
- chronological wins/losses/ties vs TIME-PERMUTE: 7/31/12
- sign p: 1.162e-04
- certificate violations: 0
- gates: {'time': False, 'physics_non_degradation': False, 'online': True, 'certificate': True}

Verdict: **NO-GO**. On the final disjoint subset, TIME-PERMUTE is significantly better than chronological after exact physical projection. Therefore the current temporal representation is not stable across held nuisance/source subsets.

## Frozen interpretation

1. Native source-conditioned physical evidence is real and should remain the anchor.
2. The V3 TCN can learn order-sensitive signal on some held subsets, but that signal is not nuisance-stable enough to authorize intervention.
3. V4--V7 show that post-hoc physical protection cannot rescue an unstable temporal representation: soft constraints damage Top5, hard intervals erase time, linear extension cascades, exact projection exposes sign instability.
4. **Do not continue by tuning blend weights, Top-K thresholds, loss weights, or projection margins on H01.**
5. The next scientific version must change the temporal representation itself, preferably back toward explicit candidate-conditioned transport phase / first-passage / persistent-sensor event timing rather than generic residual-sequence classification.
6. Closed loop remains: `CLOSED_LOOP_NOT_AUTHORIZED`.

## Historical-bank note

The archived H01 historical-bank evidence proves that a 210-carrier x 8-member native physical bank existed on each seed0..9 OFF trajectory, and the frozen FULL final-prefix replay achieved Top10 6/10 with median rank 7. The Library package available in this session contains the mapping/manifests and NPZ hashes, not the ten NPZ payloads themselves; this branch therefore does not fabricate a new historical temporal experiment.
