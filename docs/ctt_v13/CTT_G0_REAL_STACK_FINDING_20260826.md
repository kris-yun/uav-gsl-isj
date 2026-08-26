# CTT G0 Real-Stack Finding (House03)

## Outcome

`G0_PASS__FREE_SUPPORT_STATIC_BANK_CONTEXT_MISMATCH_CONFIRMED`

This is a mechanism/data-contract result, not a localization-performance result.

## Frozen checks

The CTT recorder was added only in an isolated source tree. The V12 freeze,
V12 bank, launch file, runner, PMFS planner, and truth evaluator were not
modified.

The real House03 stack used:

- House03, seed 0;
- source update 1 only;
- native PMFS time grid: 200 simulation steps at 0.2 s;
- V12 method seed 20260818, transport member 0;
- frozen House03 V12 bank SHA-256
  `bd0a5472ac11a259d7638e7fe19d8b6776f8d93391c6f19655eb80d859930b3b`.

## Result

The first diagnostic compared the whole storage array. This was too broad:
native PMFS divides cumulative counts by the time horizon only on Free cells,
and inference never consumes obstacle cells. A filament can numerically touch a
wall-boundary obstacle cell, leaving a raw diagnostic count there. CTT instead
defines arrival only on the Free support.

The earlier 0.065/0.08 whole-array discrepancies are therefore retained as an
engineering diagnostic but must not be cited as physical response mismatch.
The formal candidate 0 / transport member 0 result must be recomputed on the
Free support before the static-bank verdict is finalized:

| Check | Result |
|---|---:|
| repeat A vs repeat B | byte-identical |
| trace occupancy -> cumulative frequency map | max abs = 0 |
| current physical replay -> frozen V12 bank, Free support | max abs = 0.15 |

The formal Free-support recheck therefore confirms that the mismatch is not an
obstacle-storage artefact.  This is a forward-operator context mismatch result;
it is not yet a localization-performance result.

Carrier identity is not the cause: the old bank-build carrier manifest and the
new diagnostic carrier manifest have identical SHA-256
`5415cf6219f47f695e2da8f8d584c5491bac16d995da683a8f91d3a52047be37`.

## Wind-context comparison

The bank-build and current House03 wind grids have the same 626 free cells, but
428/626 wind vectors differ. Across common free cells:

- maximum vector difference: 0.00233943;
- mean vector difference: 0.0000965916;
- median vector difference: approximately 1.05e-9.

The wind perturbation is numerically small but coincides with a much larger
change in intermittent cell-hit frequencies. This is consistent with nonlinear
first-passage sensitivity in obstacle-constrained stochastic transport.

The original V12 response-bank header validates geometry, time step, diffusion
noise, blur settings, method seed, and transport substream, but it does not
store or validate the estimated wind field or a wind-context hash. Therefore a
bank generated under one online wind estimate can be silently accepted under a
different estimate.

## Scientific interpretation

This finding explains a plausible failure mode behind apparently strong
single-seed/offline evidence followed by weak multi-seed closed-loop
generalization: the likelihood is evaluated using a physical response operator
that is deterministic internally but conditionally misspecified for the
current trajectory-dependent wind estimate.

This does not prove that wind mismatch is the only cause of V12's NO-GO.
However, it falsifies the assumption that one static per-House response bank is
the same forward operator across closed-loop realizations.

## Design decision

The CTT main path must not use one unconditioned static response bank. M1 is
upgraded to a wind-conditioned first-passage neural field trained solely as a
surrogate of the physical filament simulator:

`(geometry, current wind field, source, query cell, transport key) -> first-arrival distribution and causal-front occupancy`.

The network may approximate the expensive physical solver, but it may not see
real source truth, PMFS posterior mass, final localization error, module gates,
or planner decisions.

M2 and M3 remain exact probabilistic inference layers. Network confidence is
not used as an evidence weight or accept/reject gate.

## Evidence paths

- VM diagnostic root:
  `/home/zyc/ctt_v13_g0_house03_20260826_r4/House03_seed0_on_rc_sd_tfei_v12`
- parity CSV SHA-256:
  `0f815a8e42765574446bcabe9715ea15249821445721040fddeae0a64ef7c742`
- current wind CSV SHA-256:
  `94cb5c31308ca7428c92b0a88b506609cf3a1ded5670544bcfb72b4b87a46f71`
- diagnostic binary SHA-256:
  `9fbe9a03805722841521cd1cfd1c41cd7cf951bc05e9fdaab56ed4aea0b9908c`

The wrapper ended at its outer diagnostic time limit because the G0 run
deliberately used no truth evaluator.  The required source-update parity CSV
was already flushed; this timeout is not classified as a scientific failure or
as a completed 300 s localization arm.
