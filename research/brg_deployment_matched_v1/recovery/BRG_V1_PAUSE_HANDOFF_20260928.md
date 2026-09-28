# BRG V1 pause and independent review handoff

The user paused the campaign after the current VGR run completed. All VGR,
PMFS, GADEN player, and host collector processes are stopped. No model has
been trained and no four-arm evaluation has run. Do not interpret any training
collection source estimate as a comparative result.

## Completed assets at pause

| Stage | Completed | Contract |
| --- | ---: | --- |
| Continuous OPEN GADEN state archives | 72/72 | 24 H01 and 48 H02, historical seeds; 72 actual reruns, zero new independent seeds |
| Native VGR/PMFS event trajectories | 48/48 | 40 train, 8 dev; 300 s each, full raw logs archived |
| V3 source-blind stop-and-sample coverage trajectories | 4/48 | 1 train and 3 dev; 300 s each, full raw logs archived |
| GPU warm training | 0/3 models | Not started |
| Warm-model self trajectories | 0/120 | Not started |
| GPU final training | 0/3 models | Not started |
| Frozen four-arm final evaluation | 0/32 | Not started |

The frozen split is 6 physical training sources, 2 development sources, and
4 untouched evaluation sources. The eight final evaluation plume cases and
four arms were fixed before looking at evaluation outcomes in
`V1_EVAL8_FROZEN_MANIFEST.json` (SHA256
`6cd4768c52c135649ad72e526c14b5816ba120b860d565aa5bc630f4d9ee2ef8`).
The current 52-event-path host inventory contains 40+8 Native and 1+3
coverage episodes, with one policy trajectory per archived run. It does not
turn paths, windows, or the same historical seed into independent plumes.

## Coverage implementation failure and correction

The first source-blind V2 open-loop pilot was rejected as input data. VGR kept
moving during a ten-reading PMFS measurement window while PMFS assigned the
whole block to one stale pose. All 25 blocks lacked ten distinct VGR
publications within 0.02 m of their recorded block pose. The raw rejected
pilot is preserved (SHA256
`fd86348bbf9c9f7965ed3b0b8cb4e2f82704ed3a303411b2c632a319a0b1c911`).
Its outcome was not used to select a route or tune the model.

The V3 correction freezes 12 source-blind target locations per OPEN
environment from the already frozen legal-cell V2 path. An opt-in VGR branch
substitutes the next fixed target only when PMFS requests navigation, then
executes the normal NavigateToPose action and lets PMFS sample after arrival.
The default Native and learned-arm navigation branches remain unchanged.
The exact V3 goal contract SHA256 is
`645df8e8f2b8527eb17d4daa65a055bfdaa18e8042fbf6d31b55b2b60bbc2261`.

V3 pilot case 013 completed 300 s, executed four frozen goals, and produced
25 valid measurement events. The ten-publication check passed. Offline and
online six-channel observation and candidate-cue arrays agreed exactly over
all 25 events and 596 legal candidates (maximum absolute difference 0).
The other three V3 runs passed the same raw-publication encoding gate; they
have not been used in model training. This establishes software/input
parity for the pilot, not BRG localization value.

The four V3 paths have 25/28/27/26 events and **one source-update prefix
each**, versus 3--4 update prefixes in the Native collection. This is a
material sampling-rate difference for the planned development NLL and should
be assessed before collecting the remaining 44 coverage paths. The result
comes from the actual run logs; no event or update was removed in encoding.

## Provenance and storage

- GADEN acquisition result SHA256:
  `b77423e40976d228c9336a55c98c1ecdd5e2da17ce7e48065f69145e4e0be501`.
- Current extracted episode inventory SHA256:
  `5bfbae018805d061da30e95a3ab08914b8c81d907d05447a4f692f6fd56459d2`.
- VGR V3 opt-in patch output SHA256:
  `39d76be1642bd1070db159953c4795930c9e4076e40c2799cba817b91bd12ea9`.
- Three Native legal template banks remain at 596/630/630 candidates and are
  included in the compact review package.
- The 72 full native GADEN archives remain separately on the host at
  `C:\Users\50176\Desktop\vm数据\BRG_V1_OPEN_CONTINUOUS_20260928`.
  Their paths, byte counts, and SHA256 hashes are in the review inventory.

The compact review package includes every available Native and V3 VGR raw
log archive, the invalid V2 pilot, 52 extracted feature/metadata pairs,
the three candidate banks, all frozen contracts, code, VM patch manifests,
and SHA256SUMS. The much larger 72 continuous GADEN archives remain available
as a separate ZIP without changing their bytes.

**Review question:** Is this V3 goal substitution a valid source-blind
training coverage policy that preserves the deployed stop-and-sample sensor
process? If yes, the remaining 44 coverage paths can be collected under the
same frozen policy before warm training. If not, revise the collection
contract before training; do not treat the moving V2 pilot as usable data.
