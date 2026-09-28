# XHOC-R0 — cross-House observation-contract audit

**Decision: `XHOC_R0_COMMON_CONTRACT_PARTIAL`.** This was a read-only audit. It does not revise the TCMA STOP or authorize Ordinal D0, a new plume run, or a mechanism comparison.

## What is already comparable

The E1/E2 bank is a genuine common *virtual-probe* acquisition contract across all three Houses. Each House has six source positions selected by the same geometry-only rule, at `z=0.20 m`; 30 source-blind probes selected by the same rule, each a mean of four 0.1 m grid cells; and one GADEN concentration snapshot at each of ten identical saved-record IDs (`100,150,...,550`). There is no Native adaptive route or stop averaging in this bank. The exact probe coordinates differ by House, as the E1 rule requires. Seven wind environments hold `7 × 6 × 4 = 168` runs. One independent GADEN seed is assigned to each source, wind and replicate row.

I compared the E2 manifest with the VM files without decoding sealed concentration values. All **168 cube hashes and 168 run-metadata hashes match**. This includes OPEN 72, sealed DEV 48 and sealed House03 48. The House03 scientific arrays remain sealed; this audit records only file presence, byte count and SHA256. See `evidence/xhoc_r0/E2_REMOTE_HASH_VERIFICATION.json` and the archived E2 manifest hash in `evidence/xhoc_r0/ASSET_MANIFEST_SHA256.tsv`.

The standalone E1 review archive stores its source/probe TSVs with different line endings from the E2 repository snapshot. Parsed TSV rows are identical (`18/18` source rows and `90/90` probe rows). For exact run provenance, the authoritative bytes are the E2 snapshot hashes: source panel `e38bee4467fb9d98ab5ee48a6115eb1b3306df63cd3da409b9412b3032c4b06e`; probe contract `364c7a2f0333c95845cfb7a10dbb96ee8c5f30a47282e508e3961d4eec575812`.

E2 is already a useful cross-House *acquisition* substrate. It is **not** a single-UAV path experiment: the 30 probes are a fixed virtual sensor panel distributed through each House. Also, the numbers `100...550` are saved-record IDs in the extractor. The E2 manifest does not certify the exact physical simulator seconds or wind index of each record. Those must be mapped from writer metadata or reproducibly reconstructed before claiming a physical-time contract. Do not call `550` a 550-second observation: E2 simulation time was configured as 300 seconds.

## Why the full XHOC threshold is not met

The preregistered `COMMON_CONTRACT_AVAILABLE` threshold is at least **eight independent physical sources per House and four realizations per source**. E2 has four realizations, but only **six sources per House**. The exact gap is two source positions per House. At one wind per House, the arithmetic minimum to cross the count threshold is `3 Houses × 2 new sources × 4 seeds = 24` additional runs under the same operator. This is a lower bound on coverage, not an approved campaign or a sufficient untouched confirmation panel.

Other assets do not silently close the six-source gap:

| Asset | What it contributes | Why it cannot simply be pooled into E2 |
| --- | --- | --- |
| JTD E2 raw 180 cubes | Ten additional unique seeds per source in the three OPEN environments; its source-ID sets exactly match E1's six H01 and six H02 sources; zero seed overlap with E2 | Deeper replication, no new H01/H02 sources; needs extractor/provenance equality checked before joint statistical use |
| JTD E1 raw 36 cubes, BRG 72 continuous archives | Further H01/H02 raw assets; BRG is a rerun of historical seeds with native frames | No additional six-source panel; rerunning a seed is not a new independent realization |
| H02 R0 288 cubes and CESS D1R 2688 cubes | Many independent H02 source positions | Cannot cure H01 and H03 source deficits; their exact contract must be checked before reuse |
| H03 AOD F1 96 cubes | Twelve source positions with eight realizations each | Its signed snapshot IDs `91,174,265,...,965` and two fixed path positions differ from E2's time/probe operator. The 96 existing extracted cubes cannot be relabeled as E2 observations. |
| Native H01/H02 49 episodes | Real adaptive observation histories | Source- and action-dependent trajectories with stop averaging; cannot be pooled with fixed virtual probes merely by matching vector lengths |
| PMFS candidate forward | Model-side hit and count proxies | Not a raw GADEN concentration target in the same units; magnitude-residual adequacy comparison is invalid without a separate measurement model |

The E2 bank therefore provides a **partial** common contract, and historical enrichment is asymmetric across Houses. `CONTRACT_MATRIX.csv` records the matching and nonmatching dimensions. Candidate-source support is a separate, House-specific geometry issue; a common selection rule does not imply identical candidate IDs or counts.

## What to freeze before using or extending it

1. Preserve the E2 role split. H01/H02 OPEN may inform a development question; the two DEV environments and both House03 environments retain their declared sealing boundaries. A hash audit is not an unseal.
2. Recover or audit the saved-record-to-physical-time/wind-index mapping for E2 without examining scientific concentration patterns. Freeze a common physical-time statement before testing any temporal mechanism.
3. Define the independent unit as a physical source, with plume seed nested under source and wind. Reextractions, paths and reruns of the same seed are not new independent units.
4. If a source-count-complete benchmark is needed, first freeze an outcome-blind geometry panel for the missing sources and a separate discovery/confirmation source split. The 24-run lower bound only satisfies the numerical XHOC threshold. A stronger new benchmark would target **12 sources × 8 independent realizations per House**, split by physical source before generation. With six E2 sources × four existing realizations per House and compatible timing, the arithmetically smallest top-up is **216 new runs** (`3 × (6 × 4 + 6 × 8)`); if the existing E2 panel cannot serve the proposed split, use a new `3 × 12 × 8 = 288` campaign. Both figures are proposals, not authorization. Existing H03 E2 scientific data must remain sealed until its role is explicitly set.
5. Any future target-versus-simulator residual-magnitude statistic must compare the same physical observable and units, or prove invariance to arbitrary positive rescaling. A free fitted gain does not make the residual magnitudes commensurate.

**Stop:** no new simulation, method score, training, VGR run, or Ordinal D0 was performed for XHOC-R0.
