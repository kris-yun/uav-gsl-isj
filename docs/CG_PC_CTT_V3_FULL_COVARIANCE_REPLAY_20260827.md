# CG-PC-CTT V3 full-covariance replay — 2026-08-27

Status: **DIAGNOSTIC REPLAY BEFORE H02_RECONSTRUCTED_CHALLENGE outcomes**

## Why this replay was required

Early V3 sparse-support diagnostics reused the diagonal per-feature nuisance scale from frozen Gate V2. That was useful for discovering the observation-conditioned rank-loss phenomenon but is not an ideal final V3 geometry metric because exact duplicated feature encodings can change diagonal-whitened information.

V3 now uses the full pair-difference nuisance covariance and its Moore-Penrose precision:

`Sigma_tr = mean_{s,m<n} 0.5 (z_sm-z_sn)(z_sm-z_sn)^T`

and

`F_s = sum_{m!=n} J_sm^T Sigma_tr^+ J_sn / [M(M-1)]`.

Formula-level self-tests confirm that exact feature duplication does not change the resulting pair/tangent information.

## Replayed real House02 V12 response bank

Input is the recovered frozen V12 House02 hit-probability bank:

- bank magic: `V12BNKR1`;
- physical candidates: 201 unique coordinates;
- members: 8;
- free response cells: 631;
- timesteps: 200;
- method seed: 20260818;
- transport substream: 6077111455669390931;
- delta time: 0.2 s;
- noise standard deviation: 0.5.

Scientific boundary: this bank is **not** a CTT first-passage bank and is not the lost historical hard-28.

## Full-covariance sparse-support result

Fixed random support subsets were used only as a representation diagnostic. Five subsets were used except full support.

| support cells Q | fraction lambda_min(F_s)>0 | mean median gamma_xy |
|---:|---:|---:|
| 1 | 0.0179 | 0.0000 |
| 2 | 0.0100 | 0.0000 |
| 4 | 0.0955 | 0.0000 |
| 8 | 0.2498 | 0.0124 |
| 16 | 0.6587 | 0.1592 |
| 32 | 0.8318 | 0.3405 |
| 64 | 0.9512 | 0.4425 |
| 128 | 0.9652 | 0.4891 |
| 256 | 1.0000 | 0.5149 |
| 631 | 1.0000 | 0.5425 |

The qualitative conclusion therefore survives the stronger nuisance metric:

`few observed response locations -> frequent loss of the second physical source-information direction`.

At full support every one of the 201 physical source positions has positive replicated second-direction information.

## Real-data representation invariance stress

A fixed 32-cell slice of the real V12 bank was used to test whether the new metric counts encoding redundancy as physical information.

### Exact feature duplication

Eight of the 32 response features were duplicated five times each. The transformed representation therefore contained many exact copies of already-existing information.

Across six spread-out physical source candidates, the maximum absolute change in the 2x2 local tangent matrix was approximately

`1.14e-13`.

Thus duplicated feature columns do not create extra V3 local source information beyond numerical roundoff.

### Orthogonal feature re-expression

The same 32-dimensional response slice was multiplied by a fixed random orthogonal matrix. Across the same candidate set, the maximum absolute change in the local tangent matrix was approximately

`1.42e-13`.

Thus the metric is effectively invariant to an orthogonal change of response basis.

These tests address a known weakness of diagonal whitening: V3 information should describe the physical inverse problem, not how many times a response coordinate is copied or which orthogonal basis is used to express it.

## Evidence-version consequence

The earlier diagonal-whitening H03/V12 sparse-support numbers remain useful as historical diagnostics but are not the final V3 metric values.

- V12 has now been replayed with the canonical full-covariance V3 mathematics.
- H03 must be replayed with the same mathematics when its frozen `phi[10,206,8,626]` artifact is available again.
- No H02_RECONSTRUCTED_CHALLENGE outcome may be used to alter the new covariance/pseudoinverse definition.

Canonical code:

- `experiments/cg_pc_ctt/v3_math.py`
- `experiments/cg_pc_ctt/v12_response_bank_tangent_audit.py`
- `experiments/cg_pc_ctt/selftest_v3_math.py`
