# E2 pre-run implementation note

The authoritative E2 charter and E1 geometry are unchanged. This runner uses
the same seed-enabled GADEN binary, gas parameters, ten extraction times, and
spatial extractor as the frozen D1R and LSC acquisition scripts. Source and
probe rows are read verbatim from the final E1 TSV files, whose SHA256 values
are checked before any simulation. All eleven wind iterations for each of the
seven authorized environments are checked against the pre-existing canonical
wind inventory before any simulation. Seed uniqueness and all 168 exact run
identities are also checked before the first simulation.

Each run retains its full 10-by-native-grid concentration cube and per-run
provenance in its role-specific VM directory. The transient filament files are
removed only after cube extraction, infrastructure QC and hashes succeed.
Sealed cubes are read by automated QC for shape, finite/nonnegative values and
hashes only. Only the three OPEN_DISCOVERY environments are pooled into 10x30
vectors. The review package contains OPEN raw cubes and vectors, plus sealed
hash manifests; it excludes sealed raw cubes and scientific summaries.

The patched seed source maps the requested decimal GADEN_RNG_SEED to uint32
base and salted Gaussian/uniform engine seeds; these values and source SHA256
are recorded for every run. No scientific mechanism is evaluated in E2.
