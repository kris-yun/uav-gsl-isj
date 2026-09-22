# HCMC V1 data-independence audit

## Finding

The historical H01/H02/H03 discovery matrix contains one gas realization per House. Navigation seeds only change the replay offset and trajectory. With approximately 2000 stored frames and a 1500-sample mission, seed windows overlap heavily; therefore seed 2/3 alone is `TRAJECTORY_HOLDOUT_ONLY`, not independent plume evidence.

The independent gate uses six newly generated stochastic GADEN realizations listed in `INDEPENDENT_DATA_FREEZE_20260922.json`. Plume seed and navigation seed are separate fields. Discovery realization directories are excluded.

## Generator audit

- The authoritative VM GADEN source was copied into `/home/zyc/hcmc_gaden_seed_build_20260922/src/GADEN`.
- `seed_only_source.diff` contains exactly one changed file: `gaden_common/third_party/gaden_core/include/gaden/internal/MathUtils.hpp`.
- The change adds optional `GADEN_RNG_SEED` binding to the two historical `std::mt19937` streams. With the variable absent, the historical default seed remains 5489.
- Same-seed generation was byte-identical across saved frame payloads; a different seed produced different payload hashes.
- Geometry, source coordinates, emission parameters, canonical wind files, occupancy, and the Native PMFS/sensor/launch contracts are fixed across the two realizations of each House.
- The current simulator writes 1803 contiguous frames for the frozen 1000-s generation call. This exceeds the 1500-sample mission requirement. The exact available range is frozen instead of changing simulation duration to manufacture a historical 2000-frame count.

## Backend binding

- H01 keeps `raw_house1_snapshot`; `raw_gas_results` points directly to the frozen new realization.
- H02/H03 keep `gaden_player`. A case-local read-only scenario view binds `vgr_sim_node` discovery and its replay modulus to the new realization while symlinking the canonical occupancy and wind configuration.
- No House backend is substituted for code uniformity.
