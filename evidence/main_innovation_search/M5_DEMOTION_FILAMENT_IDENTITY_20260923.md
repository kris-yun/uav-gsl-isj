# M5 Priority Update — filament identity audit

Date: 2026-09-23

Official GADEN `Filament` has only position and sigma; it has no persistent ID or birth time.

Survivors are compacted after each step:
- relative order is preserved;
- inactive/outlet filaments are removed;
- later filament array indices therefore shift.

Consecutive snapshot index is not a safe trajectory label.

M5 must not train fake `i→i` trajectory supervision.

If revisited, use particle-cloud / empirical-measure dynamics or first instrument IDs only after a source-blind set-statistics diagnostic shows a real non-Gaussian transport gap.

Therefore current priority is:

1. M4 / M6;
2. M3 if stochastic modeling proves necessary;
3. M5 as HOLD/auxiliary.

This further concentrates resources on M4 and M6.
