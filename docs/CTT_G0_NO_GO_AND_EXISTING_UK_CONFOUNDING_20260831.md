# CTT G0 NO-GO and existing U/K confounding

Date: 2026-08-31
Status: frozen finding; no closed-loop authorization

## Executive conclusion

The H01 fixed-trajectory shadow retains an apparently large formal localization
improvement, but it failed the preregistered G0 validity contract. The correct
terminal state is therefore:

```text
CTT_SHADOW_METRIC_OR_RECURRENCE_NO_GO
CLOSED_LOOP_AUTHORIZED=false
```

The existing PF-DEI/CTT member library also cannot isolate placement nuisance
`U` from transport realization `K`. Every H01 carrier lacks an exact
same-`U`/different-`K` pair. Consequently, the existing bank is suitable for a
joint-member premise result only; it cannot support a transport-only causal
attribution or a 210-carrier M2 Gate without one deliberately completed
fixed-`U` transport crossing.

## G0 outcome

The development shadow produced:

| quantity | value |
|---|---:|
| native PMFS mean formal error | 5.0013027324 m |
| CTT shadow mean formal error | 2.8206468312 m |
| apparent pooled improvement versus PMFS | 43.60175774% (43.6018%) |
| improved pairs | 10/10 |

This number is not valid evidence that CTT improves source identification. Four
mandatory preregistered checks failed:

| check | observed result | frozen requirement | verdict |
|---|---:|---:|---|
| cell-row-order invariance | maximum formal-error range 2.2982713685 m | at most 1e-10 m | FAIL |
| tie-aware metric invariance | maximum formal-error difference 1.7957230888 m | at most 1e-10 m | FAIL |
| source-label destruction | one-sided permutation p = 0.0615384615 | at most 0.025 | FAIL |
| observation-to-stop pairing destruction | one-sided permutation p = 0.1692307692 | at most 0.025 | FAIL |

The apparent metric gain is therefore compatible with row/tie handling and
with nuisance or recurrence structure that survives destruction of source
identity or observation pairing. It must not be presented as a likelihood,
source-ordering, or closed-loop result.

The integration arithmetic itself was reproducible:

| parity check | maximum absolute difference | tolerance | verdict |
|---|---:|---:|---|
| online posterior versus batch posterior | 5.4123372450e-16 | 1e-12 | PASS |
| joint online versus batch posterior | 4.9960036108e-16 | 1e-12 | PASS |

This PASS only proves implementation parity. It does not rescue the four failed
scientific validity checks.

## Carrier-rank contradiction

The formal-error gain does not track true-carrier evidence. In the development
record, raw true-carrier rank improved in only 4/10 final cases and posterior
true-carrier rank improved in only 2/10. Seed 9 is the clearest contradiction:

- native PMFS true-carrier rank: 25 (previous frozen comparison);
- final raw CTT true-carrier rank: 172, midrank 173.5;
- final posterior CTT true-carrier rank: 208/210, midrank 208;
- final posterior true-carrier mass: 8.0336341483e-05;
- nevertheless, its formal localization error was reported as 2.4333598061 m.

Thus a basin-level top-5% coordinate statistic can improve while the method
nearly rejects the true carrier. The 43.6018% result is a metric/recurrence
diagnostic, not proof that the source likelihood is correct.

## Existing U/K factorization audit

The frozen H01 placement manifest contains a diagonal joint-member design:

```text
member m = (placement U_m, transport seed K_m)
```

It does not contain a crossed factorial design. Exact serialized 3-D
coordinates and transport seeds were audited carrier by carrier:

| H01 scope | carriers | carriers with at least two K at the exact same U | carriers with at least two U at the same K |
|---|---:|---:|---:|
| training members | 210 | 0 | 0 |
| reserved members | 210 | 0 | 0 |
| all frozen members | 210 | 0 | 0 |

Equivalently, **210/210 H01 carriers lack a same-`U`/different-`K` pair**. The
maximum number of distinct transport seeds observed at any exact placement is
one. Placement and transport identity are therefore perfectly confounded in
the existing member axis.

This means that the previously positive coherent-versus-stopwise result can
only be described as a joint-member coherence premise. It cannot establish
that persistence of `K`, rather than persistence of `U` or their interaction,
caused the ordering change.

## Required next premise, and nothing more

The first eight-transport draft was superseded before execution because K6/K7
and routes 4004/4005 had already participated in development, two transport
realizations cannot support a one-sided exact test at alpha 0.01, and candidate
ranks sharing the same worlds are not independent replicates. The minimum
prospective repair is one fixed-placement crossing for every H01 carrier:

```text
U0 = exact member-0 placement coordinate
predictive realizations P0..P5 = seeds 101,211,307,401,503,601
prospective observation realizations O0..O6 = seven SHA-256-derived seeds
all 13 realizations regenerated at U0 in the byte-parity-closed OMP=4 environment
all 210 regenerated P0 worlds byte-identical to old context-0/member-0 worlds
```

No diagonal K1..K7 world is reused because its placement is U1..U7. The new
bank contains `210 * 13 = 2730` worlds. The seven prospective observation
transport realizations are the independent inference units; 210 source ranks
and two already-used routes are aggregated within each realization. Seven
strictly positive realization-level effects yield the smallest possible exact
one-sided sign p-value, `1/128 = 0.0078125`. The preregistration is
`CTT_M2_FIXED_U_PROSPECTIVE_K_PREMISE_PREREGISTRATION_20260831.json`.

The old V1 file is preserved as
`CTT_M2_FIXED_U_EIGHT_K_PREMISE_V1_SUPERSEDED_20260831.json`; no V1 physical
outcome was generated or read.

Until that Gate passes, the following remain prohibited:

- transport-only causal attribution;
- calling M2 independently validated;
- C++ runtime takeover;
- planner feedback or a 300 s OFF/ON experiment;
- reporting 43.6018% as a method improvement;
- tuning a score, threshold, temperature, blend, or source-specific rule to
  recover the failed G0 result.

No experiment was run to create this finding document.
