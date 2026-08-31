# CTT dynamic-transport two-module V4 result

## Frozen terminal verdict

`CTT_DYNAMIC_TRANSPORT_M2_PREMISE_NO_GO`

The final permitted M2 revision stopped at the simulation-only, strict
member-leave-one-out premise Gate. No measured historical tape posterior,
native PMFS posterior, truth coordinate, localization error, runtime code, or
closed-loop experiment was used after this failure. M2 is therefore retired;
the frozen causal M1 is preserved as the main mechanism.

This result does not overwrite the V3 development evidence (49.4218% pooled
fixed-trajectory improvement and 27/30 wins), nor does it convert that
development evidence into a two-module or closed-loop claim. The V3 NO-GO
remains valid.

## Integrity

- Preregistration commit: `a51dc5b`
- Frozen method implementation commit: `a8ef1bc`
- Execution-freeze commit: `195b6d96a6820146420287de2cf2ff01bb400e9b`
- Evaluator SHA-256: `75b001d97c1a40ddeb01af5c683a872f56c9cb924194a4663a28088dfe61881b`
- Preregistration SHA-256: `d56dd03059c3290dce295ce945532ad661b2f312b874e37dd9e3fae7a70dbdd1`
- Selftest: `CTT_DYNAMIC_TRANSPORT_TWO_MODULE_V4_SELFTEST=PASS`
- Premise summary SHA-256: `a0f920a0696aeac96dcb85c467ed6daf59d911c713b0c4cfad03f68ecfd2ba76`
- Premise verdict SHA-256: `0cee3c89e9eba0ded429286df02d0e280df8ecc4ef277840dedc4000d18d41ff`
- Input-freeze SHA-256: `1e453a2da2c8a65bca1ea9146d904a46a76460f08b4e22fb20b4073031cc81ff`
- Evidence archive SHA-256: `bfd240f7650e0fd05003fa2aa4dbf1536497e1798e806cb79e8def3aba29c8c6`
- New GADEN simulations: 0
- Neural training: none
- Closed-loop runs: 0

## Frozen dynamic model

The transport state used the preregistered exchangeable stay-or-redraw kernel

\[
A_{mm'}=\rho\mathbf 1[m=m']+(1-\rho)/M.
\]

The globally estimated, zero-tuning persistence was

\[
\rho=0.0502312254.
\]

It came exclusively from chance-corrected adjacent-block agreement in the
frozen physical simulation bank. The eight strict member-LOO estimates ranged
from 0.048324 to 0.052249. This narrow range is useful negative evidence: the
failure is not caused by one exceptional transport member.

## Premise results

The independent inferential unit was one House-by-route cluster (`n=30`). The
240 held-out-member folds were averaged within those clusters before exact
sign tests.

| Comparator | Dynamic mean rank delta | Wins/losses/ties | One-sided exact p | Result |
|---|---:|---:|---:|---|
| M1 causal-only | -0.051138 | 30/0/0 | 9.31e-10 | PASS |
| Time shuffle | -0.176873 | 30/0/0 | 9.31e-10 | PASS |
| IID transport | -0.000451 | 29/1/0 | 2.89e-8 | PASS |
| Fixed transport | +0.004645 | 2/28/0 | 0.99999997 | **FAIL** |

Dynamic source evidence itself remained non-random:

- mean normalized true-source rank: `0.149216`;
- deterministic source-label randomization p: `1/257 = 0.003891`.

However, dynamic transport was worse than fixed transport in all three Houses:

| House | Dynamic minus fixed normalized rank |
|---|---:|
| H01 | +0.001889 |
| H02 | +0.009292 |
| H03 | +0.002752 |

Therefore two hard rules failed:

1. dynamic must beat fixed transport on the 30 route units;
2. no House may reverse against any temporal comparator.

## Scientific interpretation

The bank contains ordered causal source information, and a very small amount
of same-realization temporal persistence above the cross-realization baseline.
But that persistence is only about 5%; the dynamic filter is consequently
close to IID. It improves slightly over IID but discards enough coherent
whole-run information to rank sources worse than the fixed model. The data do
not support claiming that an evolving discrete transport member is the stable
incremental M2 mechanism.

This does not say that real plume transport is fixed. It says that the eight
frozen Monte Carlo member identities do not form an empirically validated
Markov state variable for this localization problem. Learning an unrestricted
transition matrix or tuning persistence from localization results would change
the scientific method and is forbidden after this final Gate.

## Terminal policy

- Do not modify or rerun M2.
- Do not open V4 Stage 1 or Stage 2.
- Do not authorize the nine M1+M2 closed-loop pairs.
- Preserve M1 as the causal main mechanism.
- Any future closed-loop qualification must be explicitly defined as an M1
  method, not as evidence for the rejected two-module temporal claim.
