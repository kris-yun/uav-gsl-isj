# M6 G0.5 runtime result

Date: 2026-09-23

M6 passed the runtime/interface portion of G0.5.

Key numbers:

- official 8-layer architecture reconstructed from released source:
  - 3,865,673 parameters;
  - 15.46 MB FP32, consistent with the public ~15.6 MB checkpoint.
- real House02 PMFS grid:
  - 1053 total cells;
  - 631 free-space tokens;
  - GeoPT-compatible 11-D geometry+dynamics tensor constructed successfully.
- CPU random-weight forward:
  - ~0.11–0.15 s for 631 tokens;
  - ~1.1 s for a conservative 83×119=9877-token sensor-height grid.
- official fine-tune exclusion of final norm/output head corresponds to only 2,825 params;
- architecture-derived transferable fraction is ~99.927%, pending actual checkpoint load verification.

Important limitation:
checkpoint bytes could not be downloaded in the current analysis runtime because of network/Xet/DNS restrictions. This is infrastructure HOLD only. Codex must verify actual tensor load on its VM.

Scientific status remains:

`M6 ADVANCE — no plume/source-rank claim yet`.
