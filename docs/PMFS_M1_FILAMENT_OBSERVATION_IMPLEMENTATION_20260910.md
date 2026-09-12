# M1 chronological concentration observation component

## Implemented and tested

`experiments/ctpi_cstar/m1_causal/filament_observation.py` implements the
inspected GADEN CPU concentration kernel for supplied candidate filament
snapshots. Position uses metres, width uses centimetres, filament mass uses
moles, ambient density uses mol/cm3, output uses ppm:

    ppm = 1e6 * mass / ((2*pi)^(3/2) * sigma_cm^3 * air_density)
          * exp(-distance_cm^2 / (2*sigma_cm^2))

Like the inspected native implementation, contributions outside the strict
3-sigma radius or without line of sight are zero. The cutoff is not
renormalized. Map visibility is a required caller function, not an assumed
free-space default. Double-precision analytic agreement is not native
float/binary parity, and callback correctness still needs a map-level audit.

Prefix frames enforce candidate/member/fixed-source identity, finite ordered
timestamps and absence of explicitly future inputs. This does not certify an
external producer's declarations; the producer must still prove provenance.

The analytic test passes centre value, 1-sigma decay, strict cutoff,
occlusion, empty plume, linear mass addition, cubic sigma scaling, vertical
distance, prefix consistency, rejection of source changes/future inputs, and
synthetic integration through the existing delayed sensor/likelihood.

Synthetic mechanism counterexample: a filament of sigma=10 cm with normalized
centre concentration=1 ppm contributes 0.32465246735834974 ppm at 15 cm.
Its centre and sample are in different 10 cm cells. Thus centre-occupancy zero
does not imply concentration zero. This is NOT a measured House result and
does not prove the cause of the 41 positive records.

## Reference binding

Inspected on reachable VM, 2026-09-10:
/home/zyc/ros2_ws/src/GADEN/gaden_common/third_party/gaden_core/src/Simulation.cpp
SHA256 d7617d52326ac5dc699567826916ade9a0ba43e4aaf75847fadf512fd10704fb.
Read-only copied reference is in
evidence/cstar_m1_filament_kernel_reference_20260910/Simulation.cpp.
This is the currently inspected source, not a claim of historic runtime
binary equivalence or verification of every GADEN precomputed-field backend.

## Still missing before real-trajectory/full-map validation

This component OBSERVES snapshots; it does not generate trajectories of
filaments. Need source-conditioned state production with audited mass,
release schedule, growth, 3D geometry, initial state and available wind.
Do not invent source height or gas constants, substitute full ground-truth
wind for estimates, or resample a fixed source position at every emission.
The existing 2D PMFS point particles lack the physical parameters required
by this component and cannot just be relabeled as these states.

Run same-trajectory prediction diagnostics after that bridge exists, before
any House123 seed12 closed loop. No new seeds, ROS builds, or controller edits
were made in this checkpoint. Observation correctness alone is not the
causal main innovation or evidence of cross-dataset utility.

Reproduce:

    python experiments/ctpi_cstar/selftest_m1_filament_observation.py
    python experiments/ctpi_cstar/selftest_m1_causal_counterfactual_likelihood.py
