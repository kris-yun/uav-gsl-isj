# Loop 10 — Event-Based / Neuromorphic Auxiliary Screen

Date: 2026-09-20
Branch: research/remote-paradigm-loop-20260919
Status: simple event feature candidate rejected; temporal-event principle remains under review.

## Remote-domain provenance

Recent top vision venues contain a strong event-representation line:

- ICCV 2025 — *TESPEC: Temporally-Enhanced Self-Supervised Pretraining for Event Cameras*.
  Core idea: event data are sparse/asynchronous; short-window SSL loses long-term temporal information; pretraining should explicitly reason over long event sequences.
- CVPR 2025 — *On-Device Self-Supervised Learning of Low-Latency Monocular Depth from Only Events*.
  Demonstrates efficient self-supervised event learning on a small drone.
- CVPR 2025 — *ETAP: Event-based Tracking of Any Point*.
  Uses high temporal resolution and global context to handle asynchronous sparse events.
- CVPR 2025 — *EZSR: Event-based Zero-Shot Recognition*.
  Shows sparse event representations need objectives tailored to event semantics rather than RGB-style reconstruction.

Potential GSL transfer:
- plume whiffs / threshold crossings / rises / falls = sparse asynchronous events;
- native event timing may carry source identity even when block aggregation does not.

## Offline handcrafted-event test

Using the existing 12 controlled histories, a fixed event descriptor was built from:
- first/last threshold crossing at the pre-existing 0.1 ppm physical floor;
- number of whiffs;
- whiff duration;
- blank duration;
- inter-whiff intervals;
- short post-onset rise.

Compared against 10 s and 20 s binary block-HIT representations.

## Result

The handcrafted event descriptor does **not** provide a stable advantage.

- Where physical support is absent, all representations are non-identifying.
- H01 240 s: event and block representations both identify 2/2.
- H02 180/240 s: all are 2/2; event descriptor is not consistently lower in wind/source ratio than block HIT.
- H03 120/180/240 s: all are 2/2; block representations are often at least as source-dominant as the handcrafted event descriptor.

Therefore:

```
HANDCRAFTED_WHiff_EVENT_FEATURES = NO_GO
EVENT_COUNT / DURATION MODULE = REJECT
```

## Important boundary

This does not contradict the prior CTT evidence that **native temporal ordering / first-passage phase** can be source-informative and that coarse temporal processing can destroy information.

The failure here says:
> compressing the native signal into a small manually designed event statistic is not enough.

The only event-vision idea still worth considering is a learned long-sequence temporal representation that preserves native event correspondence, analogous to TESPEC—not an event-feature engineering block.

That surviving idea substantially overlaps the current predictive M1, so it is not yet accepted as an independent M2.

## Current M2 status

- η rare-event weighting: demoted after mixed incremental gate.
- generic multiscale-history concatenation: mixed / not qualified.
- handcrafted event representation: rejected.
- long-sequence temporal correspondence: literature-supported but currently overlaps M1.

M2 remains OPEN.

Next search should prioritize a remote-domain principle solving a different failure than M1:
1. sensor-response distortion / hidden measurement dynamics;
2. missing physical support / censored evidence;
3. probability-map structural consistency;
rather than another variant of temporal representation.
