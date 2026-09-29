# 2026-09-29 Addendum — AOD-R2 F0 Outcome and Next Mainline

## AOD-R2 F0 outcome

Branch with evidence:

`codex/aod-r2-transfer-audit-20260929`

Final evidence commit:

`005ba6a34d95fdfe340050df96fe30a688fa71bf`

Frozen decision:

`AOD_R2_F0_NO_SIGNAL`

The prospective OCB-R2 matched-source local mechanism test did not reproduce a
stable incremental `rawu-u` discrimination signal.

Reported frozen results:

- House01 median group-mean Delta_D: `-0.02774144`
- House02 median group-mean Delta_D: `+0.07973757`
- overall median group-mean Delta_D: `-0.00732356`
- positive source-context groups: `8/16`
- u neighborhood wins: `64/64`
- rawu neighborhood wins: `64/64`
- rescue/harm: `0/0`
- two complete scoring passes: byte-identical

The F0 positive gate therefore failed and the full 596/630-candidate AOD-R2
bank must **not** be generated under this frozen protocol.

Important interpretation:

This is a NO-SIGNAL result for the **local two-source neighborhood mechanism
gate**. Both arms hit a 64/64 local discrimination ceiling, so this test cannot
falsify the historical House03 full-map AOD result. The historical
`AOD_F1_FULL624_CONFIRMED_STRESS_NONINFERIOR` result remains legacy evidence
under a different generator/acquisition contract. It is not promoted by OCB-R2.

AOD status after this addendum:

- legacy signal retained as historical evidence;
- prospective promotion gate not passed;
- AOD mainline parked;
- no centered/filter/post-hoc rescue;
- no 268,224 full-support forward expansion.

## Why the next route is marginal-preserving temporal dependence

Before OCB-R2, the dependence route had one real development signal:

`DEPENDENCE_D0_CROSS_TIME_SIGNAL`

but it was not ready for promotion because:

1. the old representation compressed the full 10x30 field to a 10-D count
   trajectory;
2. the complete 300-D marginal Brier evidence was stronger;
3. OCB-R2 S2 initially lacked source comparability within fixed wind/gas.

S2X repaired item 3.

Combined S2+S2X now provides, for each of eight fixed
House-wind-gas-occupancy-generator-timebase contexts:

`2 source positions x 4 independent stochastic realizations/source`

Therefore the next mainline is **not** a new arbitrary route. It is a fresh,
prospective test of the earlier dependence signal on the repaired benchmark.

## Immediate next step

First rerun D0A on S2+S2X metadata only.

Expected contract to verify:

- 8/8 fixed non-source strata;
- two source positions per stratum;
- four independent realizations per source;
- identical House, wind, gas, occupancy, generator and native-time contract
  within each source comparison.

If this fails, stop.

If it passes, record:

`OCB_R2_D0A_SOURCE_COMPARABILITY_PASS`

Then resume the already-preregistered
`OCB_R2_D0_MARGINAL_PRESERVING_DEPENDENCE_GATE`.

## Observation contract for resumed D0

To avoid introducing new degrees of freedom after AOD-R2 F0, reuse the exact
source-blind observation contract already frozen before AOD target extraction:

- H01/H02 E1 30 probes;
- observation plane z=0.20 m;
- requested physical times 50,100,...,500 s;
- the already-frozen nearest-native-record mapping;
- the already-frozen native concentration extractor;
- the already-extracted 64 discovery target tensors if hashes match.

Do not choose new probes, times or extractor settings.

For the dependence gate, derive the binary encounter tensor exactly as in the
older dependence work:

`B[t,q] = 1[C[t,q] > 0]`

No threshold fitting.

## Fair leave-one-realization-out rule

Each source/context has four realizations.

For target replicate index r:

- target = source-truth realization r;
- for **every candidate source** in that same context, use reference
  realizations with replicate indices other than r;
- therefore each candidate source has exactly K=3 reference realizations.

This keeps ensemble size equal across the truth and alternative source and
does not rely on common RNG seeds.

Do not use confirmation realizations to increase K.

## Scientific layers

### M0 — full spatial marginal field

Use the complete 10x30 binary field:

`p_hat_s(t,q) = mean reference B_s(i,t,q)`

and marginal Brier loss over all 300 coordinates.

This is the strong baseline that the dependence layer must not replace.

### P — intact full-tensor realizations

Keep the original realization pairing across all ten times.

### Q-time — marginal-preserving cross-time destruction

At each time t, permute the three complete 30-D snapshots across the reference
realization labels independently.

This preserves:

- every empirical coordinate marginal;
- every complete spatial snapshot at each time;
- every each-time count/support distribution.

It destroys only which snapshots belong to the same stochastic realization
across time.

Use the fair U-statistic Energy Score on the **full 10x30 tensor**, not on the
10-D count trajectory.

## Main question

Do not ask whether a dependence-only model beats M0.

Ask:

> after preserving the full spatial marginal source evidence, does intact
> cross-time realization pairing add source-discriminative information that is
> lost under Q-time?

Use the existing preregistered residual logic and destructive controls.

If M0 is already ceiling-level and therefore no correction cases exist, report
that honestly. Margin-only improvement is a mechanism diagnostic, not a
localization PASS.

## Decision discipline

Possible outcomes remain:

- `OCB_R2_D0_DEPENDENCE_INCREMENTAL_POSITIVE`
- `OCB_R2_D0_DEPENDENCE_PRESENT_NOT_INCREMENTAL`
- `OCB_R2_D0_NO_DEPENDENCE_SIGNAL`
- `OCB_R2_D0_HOLD_COMPARABILITY`

Only the first permits dependence-method construction.

If positive:

- first try the simplest density-ratio / classifier formulation that learns
  only the dependence residual;
- preserve the full marginal source evidence;
- only consider larger diffusion/flow-copula machinery if the simple residual
  model cannot represent a confirmed dependence object.

If not incremental:

- stop this route;
- do not replace the stronger marginal model with a weaker joint model.

## Benchmark seals

Throughout resumed D0:

- H01/H02 confirmation remains sealed;
- House03 prospective confirmation remains sealed;
- no new GADEN;
- no closed loop;
- no method tuning using confirmation/H03;
- stop after the D0 scientific decision.

## Current project state in one line

> The baseline has been repaired, AOD failed its prospective local promotion
> gate without invalidating its historical full-map result, and the next
> justified mainline is the previously observed cross-time dependence signal,
> now retested prospectively on the S2+S2X matched-source benchmark while
> preserving the full spatial marginal evidence.
