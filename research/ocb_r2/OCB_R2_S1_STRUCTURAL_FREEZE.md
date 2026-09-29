# OCB-R2 S1 H01/H02 structural smoke freeze

Only the eight H01/H02 original source×wind configurations (indices 0–7)
are authorized. Each gets its first previously frozen master seed, replicate
1. `OCB_R2_S1_RUNLIST_8.tsv` and the full inherited 96-row master manifest
are committed before any S1 output. House03 indices 8–11 have undergone only
a read-only input/launch/hash audit; they remain `SEALED_NOT_RUN`.

The frozen binary SHA256 is
`ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688`.
Each S1 run checks it before starting. It must not be rebuilt or changed.
The prospective generator uses current native time/save/wind semantics and a
single OpenMP worker, as qualified by A(S1), B(S2), C(S1). The complete source
and instrumentation provenance is in `evidence/ocb_r2/BUILD_PROVENANCE.md`.

Parameters are inherited from the audited OCB-R1 command contract. Runtime
changes are limited to output path, a lossless-layout wind bridge path, and
making the simulator's already-false `pre_calculate_concentrations` default
explicit. The four House02 winds use the already audited reconstructed input
staging; seven wind bundles required a new storage conversion, while config 5
reuses the qualification wind bytes. No original wind or occupancy file was
modified. Conversion input/output hashes are frozen in
`S1_WIND_LAYOUT_CONVERSION_SUMMARY.json` and the seven per-config manifests.

One seed (config 5, replicate 1) was also used in the prior generator-only
qualification. Its selection in S1 follows the pre-existing replicate-1 rule,
not a plume outcome. S1 reruns it in a distinct output leaf and performs only
structural checks. No source localization or method statistic is computed.

Per-run gates: successful process exit; exact frozen binary/seed/params;
occupancy, launch, source, wind input and converted-output hashes; 1803
parseable nonempty result files; first/last native record times 0 and
999.502991 s; strictly increasing timeline; legal wind index transitions;
finite filament coordinates, positive sigma, finite positive native Gaussian
center concentration; complete manifest and SHA inventory. A failure stops
the campaign without seed replacement or configuration edits.

VM disk safety: qualification A/B/C full outputs were first copied to
`C:\GADEN_OCB_R2_ARCHIVE\qualification`, with 5451/5451 complete copied
files checked against VM SHA256 before VM raw deletion. For S1, run one,
validate, copy the full raw directory to the same C archive, independently
verify every copied file, then remove only that validated VM raw directory.
Retain at least about 1 GiB VM root free space. No batch accumulation.

S1 PASS requires 8/8 structural, provenance, asset and basic scientific
sanity gates. Even if PASS, stop: no remaining seeds, House03 plume, PMFS,
ranking, localization metric, or innovation method runs are authorized.
