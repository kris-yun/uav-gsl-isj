Offline PMFS Native candidate replay data for **one accepted run**, `H01_R2026092201`, source update 1.

- Static parity: 152/152 evaluated candidates; first sampled point, 32,224 observed-support hit probabilities, and Native scores match exactly.
- Offline trace parity: 152/152 candidate full final hit maps match the uninstrumented compiled PMFS kernel bitwise.
- Data: 30,400 internal step summaries, 15,474,729 filament XY positions, 1,579,830 unique occupied-cell events, and aligned cell transitions.
- Effective PMFS candidate RNG seed is 0. Navigation seed in the run manifest is 2; the frozen launch passed `random_seed` while PMFS reads `seed`.
- No live PMFS code was changed. No transfer-operator, localization, or cross-realization mechanism test was performed.

SHA-256 of attached `H01_R2026092201_native_candidate_dynamics_v2.tar.zst`:
`46bbfd8aff2d6203dd4046c754b2885273b8f5b94e4643a9dec0946279e2b71f`

See `evidence/standalone_candidate_replay/README.md` and `REPLAY_VERDICT_20260923.json` on branch `research/standalone-candidate-replay-20260923` for the frozen inputs, verification boundaries and reproduction steps.
