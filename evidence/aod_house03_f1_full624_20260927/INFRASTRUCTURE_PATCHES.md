# Infrastructure-only patches

## Logging node compression-library linkage

The first isolated logging-node build failed at link time with unresolved
`bsc_init` and `bsc_compress` from the existing seeded `libgaden.so`.
No fresh GADEN run had started and no target concentration was read.

The build command now explicitly links the already built historical `libbsc.so`
and records its path and SHA256. The seeded GADEN numerical library, compression
implementation, RNG, parameters, currentTime, save schedule and wind schedule
are unchanged. The failed build directory is preserved as
`timebase_logger_compile_attempt_1`.

This is a build/dependency repair only. It does not authorize any timebase
adaptation, nearest-frame substitution, retiming or additional plume budget.

## Compression-library runtime search path

The isolated node then built successfully, but the dynamic loader could not
locate the transitive `libbsc.so` dependency. The simulator main function was
not entered, and no realization directory, time map or plume was generated.
That loader attempt is preserved separately.

The launch environment now includes the existing codec directory in
`LD_LIBRARY_PATH`, checks that `ldd` has no missing libraries, and verifies both
the loaded seeded GADEN library and codec paths and hashes. No numerical code,
parameters, time clock or save schedule changed.
