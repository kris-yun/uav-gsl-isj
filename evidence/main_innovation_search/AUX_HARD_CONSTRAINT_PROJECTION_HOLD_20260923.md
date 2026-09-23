# Auxiliary Audit — Hard-Constraint Projection (ProbHardE2E / PCFM)

Date: 2026-09-23  
Status: **HOLD — do not add to the current 2-D PMFS world model yet**

## 1. Attractive remote-field ideas

Two recent top-venue methods are relevant:

- PCFM, NeurIPS 2025:
  hard physical constraint enforcement for flow-based generative models;
- ProbHardE2E, ICLR 2026:
  model-agnostic differentiable probabilistic projection for linear/nonlinear hard constraints and UQ.

These are scientifically stronger than generic PINN soft penalties.

## 2. Exact GADEN semantics audited

Current GADEN core source shows:

- every filament is born with a fixed total amount of target gas;
- filament growth increases sigma while preserving per-filament total moles;
- wind advects filament centers;
- stochastic displacement is added;
- obstacle collisions are handled by rejecting the wall-normal motion and sliding;
- filaments reaching an `Outlet` are removed from the active population;
- concentration is calculated from active Gaussian filaments;
- contributions are only added when line-of-sight through free space exists.

Therefore the full 3-D filament system has a clear source-injection / active-mass / outlet-removal accounting.

## 3. Why hard global mass conservation is invalid for the current 2-D target

The proposed first world-model target is a **sensor-height 2-D concentration/hit field**.

A 2-D slice does not observe:

- total 3-D gas mass;
- vertical transport;
- buoyancy;
- outlet flux;
- gas outside the slice.

Therefore imposing a hard equality such as

[
sum_{xin	ext{2-D slice}} C(x)
=
	ext{injected mass}
]

would be physically unjustified.

Do not use it.

## 4. Exact constraints that are available in 2-D

The following are safe:

- concentration non-negativity;
- hit probability in [0,1];
- zero/undefined prediction on obstacle cells;
- candidate-source injection locality in the source representation.

But these are mostly easy to enforce architecturally with:
- softplus/log concentration;
- sigmoid/logit hit probability;
- obstacle masking;
- localized source injection.

A sophisticated hard-projection method would currently add complexity without enough scientific value.

## 5. When to reconsider

Hard-constraint projection becomes interesting if a later model predicts:

- full 3-D concentration/filament density; or
- a control-volume state with explicit source and outlet flux.

Then exact/near-exact constraints could include:

- source injection balance;
- outlet flux;
- mass conservation;
- no-through-wall flux;
- positivity.

At that point ProbHardE2E/PCFM can be revisited as a real auxiliary.

## 6. Current decision

`HOLD AS AUXILIARY`

Do not use hard-constraint projection merely to create a third module.

Current stronger auxiliary hypotheses remain:
- counterfactual/compositional source injection (M4);
- stochastic residual/function-space modeling (M3);
- Lagrangian filament dynamics (M5).

The auxiliary modules should be selected only after the main candidate shows a source-rank signal.
