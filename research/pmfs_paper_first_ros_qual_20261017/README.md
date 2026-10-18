# Complete PMFS ROS build and bounded A2/B2 qualification

Read `验收结论_zh.md`, `analysis/FINAL_VERDICT.json`, and the final `PATCH_CLASSIFICATION.json` first. The retained BEFORE_RECTANGULAR table is an earlier construction stage.

This is the human-approved paper-first reconstruction of the pinned September18 author implementation. Eq6, source-score coefficient1 and declaration variance1m² follow explicit paper operations. Unknown details use the pinned GitHub source. Age-growth coverage is not invented; the centre-cell event fallback is disclosed. This is not an untouched author release or a proven exact reconstruction of the paper experiment.

The package contains the complete committed PMFS server/action source scope, pinned source dependencies, runtime adapters, compiler commands/exit codes, actual Linux ELF, two completed robot episodes and two retained technical attempts, raw CDR/queries, observation windows, posterior/Omega and independent readout checks. The optional other localization algorithms were disabled using the author's build switches; all required PMFS/Common components and the action server were built from new objects.

No new GADEN world was generated; the existing3606frames were SHA-verified. Their full bytes and a portable ROS installation are not in this focused package. `world_provenance/` identifies the existing worlds and every frame hash. Existing player/GMRF dependency binaries were reused with live SHA checks, not rebuilt in this stage. Do not treat the old July/2026 results as outputs of this new binary.

Offline checks need only Python standard library:

    python portable_replay.py --verify-only
    python portable_replay.py --out /tmp/pmfs_qualified_replay_01

The latter checks saved unit mass, complete variance and Eq6 using the recorded Omega; it does not generate new robot observations or reproduce source forward maps. Native C++ readout can be recompiled using the supplied pinned DDA headers:

    g++ -std=c++20 -O2 -Idependencies/DDA/include native_readout_check.cpp -o native_readout_check
    ./native_readout_check analysis/native_readout_input.txt

Actual ROS build commands, dependency paths and environment sourcing are preserved in the scripts, CMakeCache, compile_commands and run shells. Re-running them requires a suitably configured Linux ROS2 Humble installation and the separately identified world/runtime dependencies. These scripts never claim to be a self-contained cloud simulator.

Native search seconds use PMFS node system time (`use_sim_time=false`). They are distinct from the BasicSim5x ROS clock and recorded physical gas-world seconds. The300s cap is the pinned GitHub launch default, not a claim of a universal paper cutoff. Every completed episode has a native variance declaration, but the4.85m/4.37m errors are not accurate-source successes or statistical reproduction of30paper trials. No AIMMD comparison was run.
