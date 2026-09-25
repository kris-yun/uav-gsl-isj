# E4A implementation before target unseal

The E4A scorer has two explicit stages. `prepare` reads only the E2 OPEN array
and final E1 contracts; it saves the top-two right singular vectors, hashes the
basis and scorer, computes the frozen W0/W2 2+2 seed-half noise norms, and writes
an immutable pre-unseal lock. The lock is committed before `score` is allowed.

`score` verifies that same lock and code hash, then reads exactly the 24 H02
`3,5-1_fast` concentration cubes listed as environment index 4 in the E2 DEV
hash manifest. It never opens House01 DEV or House03 raw cubes. Pooling is the
same 2x2 mean at the E1 House02 probe locations. Each 300-D vector is
`log1p` transformed before source-replicate means and source-common shift
removal. The two target deformations are W1-W0 and W1-W2.

Within-wind controls are centered source-wise differences of first-two versus
last-two realization means for W0 and W2. As frozen in the charter, HOLD applies
only if both target Frobenius norms fall below the maximum of those two control
norms. G1/G2/G3 are evaluated with the exact registered 0.70/0.55/0.80 cutoffs.
Zero-norm target matrices have capture and top-two energy defined as zero, so
they cannot accidentally pass. No rank, posterior, MSE, or alternative feature
is computed.
