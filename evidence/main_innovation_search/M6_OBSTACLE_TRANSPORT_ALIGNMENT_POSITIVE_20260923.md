# M6 obstacle-mechanism alignment update

Date: 2026-09-23

Source-code comparison found a close structural match:

- GeoPT pretraining: directional particle walk, ray collision, truncate movement before geometry.
- Native PMFS: wind+noise directional filament step, sub-cell collision test, stop at last free position.
- GADEN: higher-fidelity extension that can remove wall-normal motion and continue tangentially.

This makes GeoPT's dynamics-lifted pretraining especially relevant to **PMFS filament transport**, not only generic CFD geometry.

Remaining GADEN-specific effects become low-data adaptation targets rather than reasons to train transport representation from scratch.

M5 generative filament dynamics is therefore less compelling as an independent main thesis; it remains a possible stochastic/high-fidelity extension if M6 passes.
