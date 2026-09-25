# E0 provenance and counting rules

Read-only scan; no GADEN executable invoked; no source asset modified.
N_environment is 12 canonical House x wind operators, never edge x wind or seed count.
Unique realization key = House, wind, source xyz rounded to 0.1 mm, gas type, RNG seed.
Unrecorded canonical seed is retained as one physical run with weak provenance.
House02 D1R contract SHA256: 68121bc9225646e37fcf0233e769b694d9dbaec382723f45b8e80ffc73cea334
10 frozen indices: 100,150,200,250,300,350,400,450,500,550

## Source files and SHA256

- `/home/zyc/bigreen_gate1a_exact_20260924/source_bank.tsv`: `0e835c3a3d0f4651f9c4aa87b28a34892589cfb073a73daf6a84896d081824fb`
- `/home/zyc/bigreen_gate1a_exact_20260924/gate1a_contract.json`: `68121bc9225646e37fcf0233e769b694d9dbaec382723f45b8e80ffc73cea334`
- `/home/zyc/cess_d1r_reference_repo_20260925/evidence/causal_emergent_source_scale_v0/d1r/CESS_D1R_ARTIFACT_SHA256.tsv`: `3540c6a734c7d7c4714793bd504ae246277d2563eff9346514d3f9d761372b1d`
- `/home/zyc/lsc_crosswind_d0_repo_20260925/evidence/local_stochastic_confusability_v0/crosswind_d0/LSC_CROSSWIND_D0_ARTIFACT_SHA256.tsv`: `10b9cc4786a1c1d321ed80a480f32cef0f629b90cd639e93ba92363920829a82`
- `/home/zyc/SCTT_DISCOVERY_DATASET_V2_20260817/collection_manifest.json`: `0af58d7ad078aa9fb3f168a9e4877f257f5197bb3a06370f97fe4bf1488af032`

Each inventory row also carries its own artifact or sidecar SHA256.
Raw canonical/HCMC rows hash iteration_100 as a representative content check.
The E0 result does not claim full byte verification of every raw iteration.
