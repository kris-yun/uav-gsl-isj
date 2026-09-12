# H03 rank-2 paired physical-measurement probe result

Date: 2026-09-13

## Frozen verdict

```text
PHYSICAL_SOURCE_OVER_TRANSPORT_CAPACITY=PASS
HELDOUT_PROVIDER_DIRECTION=PASS
ALL_SOURCES_ALL_TRANSPORTS_UNIQUE_FULL_SUPPORT_RANK1=FAIL
NO_GO_NO_CLOSED_LOOP_CURRENT_RANK2_OPERATOR
```

The frozen gate was evaluated once after all four H03 physical worlds completed.
No PMFS, posterior, planner or closed-loop arm ran.

## Integrity

- Pre-run commit: `22f9b93023adc047207f50cb72391556d9abbe97`
- Host-verified minimal source archive SHA-256:
  `5eed1013a873f8a77a4ea16dcba87180036e095112165412db487eecf2ddefac`
- Frozen route SHA-256:
  `42ea23f4d1753d489eba24455a5dc993f428f652c3ba3b4415dae2b43869489b`
- Four raw worlds and 24 pre-manifest files independently matched the VM
  `RAW_MANIFEST.json` hashes after transfer.
- Raw evidence archive SHA-256:
  `d800931018ca38c2767bb231674e10d31cdf97e2eceb2f2ed138ce6e6317b51d`

The four worlds share the same 657-sample route.  SA/HF within each fast or
slow transport share the same wind sequence.  GADEN RNG seed 1234, release,
sensor and map contracts are unchanged.  The only factorial variables are
source `(SA,HF)` and existing transport `(fast,slow)`.

## Positive premise evidence

The three-cycle physical source-difference vectors were:

```text
fast = [ 0.03635010, 0.00395045, -0.00183339 ] ppm
slow = [ 0.21647506, 0.05417676, -0.05917803 ] ppm
```

Their cosine is `0.969170`, so the new measurement operator observes a
transport-consistent source direction.  The source-main-effect norm is
`0.133250`, greater than the source-by-transport interaction norm `0.097796`.

The provider parameters were selected from H01+H02 before H03.  Its predicted
source-difference direction has cosine `0.994291` with fast physical response
and `0.940549` with slow response.  Thus the rank-2 action fixed the earlier
one-dimensional direction defect and the provider predicts the coarse response
direction correctly.

## Decisive failure

The complete 820-candidate score profiles one shared nonnegative amplitude.
It did not identify either physical source in all transports:

| actual source | transport | truth rank interval | best candidate | best-candidate error |
|---|---|---:|---|---:|
| SA `(-0.45,1.90)` | fast | 163--279 | `(5.6,0.987)` | 6.119 m |
| SA `(-0.45,1.90)` | slow | 158--253 | `(0.2,2.487)` | 0.876 m |
| HF `(8.15,-1.413)` | fast | 1--820 tie | `(1.1,0.987)` | 7.447 m |
| HF `(8.15,-1.413)` | slow | 1--820 tie | `(0.8,0.987)` | 7.732 m |

HF produces essentially zero paired response at the three cycles: magnitudes
are about `1e-11` or smaller in fast transport and `1e-9` or smaller in slow
transport.  Every source that also predicts zero is equally compatible.
The action is concentrated near the original H03 SA encounter and therefore
cannot identify a far source.  For SA, positive response exists, but the
provider's full spatial response shape remains wrong enough that many false
candidates beat the true point despite correct coarse direction.

This separates two conditions that were previously conflated:

1. independent measurement directions can create real source contrast;
2. local contrast does not supply global source support or a correct candidate
   response family.

The first is necessary and passed.  The second is required for localization
and failed.  Geometric rank alone therefore cannot establish the causal main
innovation.

## Scientific decision

The current rank-2 paired operator is frozen NO-GO.  It will not be rescued by
changing amplitude profiling, adding posterior weights, accepting a near-source
slow result, removing HF, or running the 240 s H03 closed loop.

The result leaves a narrower observation: a local paired response may estimate
an encounter-gradient direction when the route is already inside a plume.  It
cannot yet act as a global source likelihood.  Promoting that local observation
to a new active-search module would repeat the old Active Probe line unless a
source-independent rule covers remote zero-response candidates and a more
accurate response provider is established first.  Neither condition exists in
the current code/data.

Accordingly, under the current single-UAV, single-gas-channel and fixed
benchmark inputs, the causal line remains useful only as an audit and
measurement-design principle.  It is not supported as the paper's main
cross-dataset localization innovation.

## Files

- `FINAL_GATE.json`: complete numerical result and input hashes.
- `RAW.tar.gz`: all four transferred raw worlds and VM provenance.
- `route/`: frozen source-blind route and geometry contract.
- `EXPERIMENT_FREEZE.md`: criteria written before generation.
- `tools/evaluate_h03_rank2_paired_probe.py`: frozen evaluator.
