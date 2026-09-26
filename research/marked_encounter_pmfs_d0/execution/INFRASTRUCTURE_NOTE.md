# Infrastructure preparation repair — no forwards or target scoring yet

The first preparation attempt located House01 and House02 3,5-1_slow but
stopped at missing top-level House02/wind_simulations/4,5-3_slow.
The exact existing family is under House02/House02/wind_simulations/4,5-3_slow.
The adapter now accepts that audited existing nested scenario path.
It does not synthesize, scale, or substitute wind assets.

Preparation is restartable at the same frozen input contract. Nearest-row
lookup uses an exact KD-tree with full argmin on ambiguous ties; the first two
already exported wind families are independently checked byte-identical on
restart. No scientific run or target statistics existed before this repair.
