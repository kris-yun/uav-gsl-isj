# Reproducibility contract

## Frozen boundary

The reported result is tied to the exact binary and source hashes listed in `VERSION`. The authoritative archive is `evidence/MEACI_V10_MAIN_INNOVATION_HOUSE123_SEED01_6OF6_20260824.zip`.

Before any confirmatory run, freeze and record:

1. source and online-binary SHA-256 values;
2. `PFDI_MODE=me_aci` and `RUN_CONTRACT=MEACI_SEQUENTIAL_SPATIAL_REPLICATION_V4`;
3. `STEPS_SOURCE_UPDATE=3`, `TIMEOUT_SEC=300` and first-accepted-update stopping;
4. House/seed assignment and output root before reading source truth;
5. the original PMFS top-5% expected-location endpoint.

Do not tune the gate, likelihood, nuisance family, temperature, posterior, planner or stopping time by House or seed.

## Evidence verification

First run the repository-level check:

```bash
python3 verify_repository.py
```

For the complete audit, extract the evidence archive and run its bundled verifier from the extracted `FREEZE_MEACI_V10_20260824` directory:

```bash
python3 verify_freeze.py
```

Expected status is `MEACI_V10_FROZEN_EVIDENCE_VERIFICATION_V1`, `PASS`, `6/6`, pooled improvement `0.40990003161275385`, and minimum gain `0.22377802587772533`.

## ROS 2 package

The captured package targets ROS 2 Humble and depends on the MAPIRlab GSL/PMFS runtime plus VGR/GADEN scenario data.

```bash
mkdir -p /tmp/meaci_ws/src
cp -a ros2_package /tmp/meaci_ws/src/gsl_server
cd /tmp/meaci_ws
colcon build --packages-select gsl_server --cmake-args -DCMAKE_BUILD_TYPE=Release
```

Adjusting filesystem prefixes for another machine is infrastructure adaptation. Changing the formula, cadence, gate, nuisance family or evaluation boundary creates a new method version.

## Frozen closed-loop invocation

On the qualified VM environment, the intended arm is equivalent to:

```bash
HOUSE=House01 \
SEED=0 \
ARM=on \
PFDI_MODE=me_aci \
RUN_CONTRACT=MEACI_SEQUENTIAL_SPATIAL_REPLICATION_V4 \
STEPS_SOURCE_UPDATE=3 \
TIMEOUT_SEC=300 \
TARGET_ACCEPTED_UPDATES=1 \
RUN_ROOT=/dev/shm/meaci_v10_confirmatory \
bash reference/run_meaci_case_20260824.sh
```

Change only `HOUSE`, `SEED`, domain/output isolation and machine-specific paths for a preregistered confirmatory batch.

