# E4B implementation before W3 generation

The stopped E4A gate is unchanged. This is the separately frozen E4B 2x2
factorial-corner test. Only H02 `4,5-3_fast` is acquired as the fourth corner;
H01 DEV and all H03 data remain sealed.

`e4b_factorial_gate.py prepare` uses only the existing E2 OPEN W0/W2 array
and already consumed E4A H02/W1 array. It recomputes the source-centered
speed/family effects in the frozen 300-D log1p representation, saves two
top-right-singular-vector bases with deterministic sign convention, and hashes
them. It verifies all eleven canonical wind files for each of W0/W1/W2/W3,
the final E1 source/probe contracts, and the simulator/extractor. The lock
records scorer/acquisition code hashes, G1-G5 thresholds and the HOLD rule.
The lock is committed before the first W3 run.

W3 is assigned the next unused E2-style environment index 7. Seeds are exactly
`2026110000 + 1000*7 + 10*source_index + replicate_index`, source indices 0..5
in E1 row order and replicates 0..3. This yields 24 distinct requested seeds
from 2026117000 through 2026117053. Each run uses the frozen GADEN parameters
and retains its complete 10x83x119 concentration cube with SHA256 and seed
provenance. The temporary filament files are removed only after cube QC.

The scorer reads those 24 W3 cubes after acquisition, pools the E1 probes, and
evaluates the exact G1-G5 and effect-size rules. No source rank, posterior,
alternate representation, or field MSE is computed. The review package
contains W0/W1/W2 predata vectors and all 24 W3 raw cubes, but no H01 DEV or
H03 raw or scientific data.
