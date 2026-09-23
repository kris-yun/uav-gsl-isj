# M6 mechanistic confidence update

Date: 2026-09-23

A source-code audit of GeoPT's released pretraining generator materially strengthens M6.

GeoPT is not pretrained only on static geometry.

Its dynamics-lifted self-supervision:
- samples 3-D volume particles;
- assigns each a direction + step length;
- performs multi-step Lagrangian walks;
- ray-tests movement against geometry;
- truncates movement at collisions;
- learns geometry-constrained particle-trajectory structure.

This has a direct structural analogue in PMFS:
- filament particle;
- wind direction;
- advective displacement;
- obstacle-constrained motion.

Revised gas dynamics prompt should therefore preserve GeoPT's original semantics:

`[wind_unit_vector, geometry_scaled_advective_displacement]`

rather than treating wind as arbitrary feature channels.

Candidate source remains a post-projection localized injection/birth adapter.

This does not prove transfer performance, but it makes M6 substantially more physically grounded and less like a generic PINO transplant.

Primary gate remains GeoPT-vs-scratch low-data truth-source rank.
