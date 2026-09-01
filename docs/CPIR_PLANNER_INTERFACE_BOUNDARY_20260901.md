# CPIR planner-interface boundary — 2026-09-01

Status: `FROZEN_CONTROLLED_PLANNER_INTERFACE`

## Decision

CPIR M1/M2/M3 is an **inference innovation**, not a fourth active-planning module. Formal A0/A1/A2/A3 experiments therefore retain the authoritative PMFS navigation/controller policy as a controlled common component.

At a source-update boundary the implementation may run the native PMFS forward simulation to refresh controller-only predictive products (`resultsFirstLevel`, `varianceOfHitProb`). Its transient native source posterior is then discarded and overwritten by the CPIR posterior before estimation/evaluation output.

The CPIR posterior is **not blended, gated, temperature-scaled or otherwise injected into the planner**. `posterior_guidance_weight` remains exactly zero.

## Why this boundary is necessary

`MovingStatePMFS` currently evaluates motion using PMFS forward predictive quantities. Those quantities must not be left zero or stale merely because CPIR replaces the source-likelihood channel. Conversely, inventing a CPIR-specific goal modulation after seeing localization results would create an unregistered fourth module and contaminate the M1/M2/M3 ablation.

The current interface therefore separates:

```text
measurement -> PMFS hit/wind state -> native forward predictive controller state -> navigation
measurement -> CPIR M1 -> M2 -> M3 -> source posterior / source estimate
```

Both branches share the same online measurements and robot trajectory history, but CPIR owns only the source-inference branch.

## Experimental consequence

Under identical observation-world realization, seed, timing, navigation parameters and deterministic native-forward contract, A0/A1/A2/A3 are expected to use the **same baseline controller policy**. Any trajectory divergence must be diagnosed as scheduler/navigation nondeterminism or an unintended estimator-to-planner leak before it is interpreted as scientific gain.

Required paired diagnostic:

- compare commanded-goal sequence;
- compare accepted navigation goals;
- compare pose trace after time alignment;
- compare native planner `varianceOfHitProb` hashes/summaries at each source update;
- compare PMFS hit-map state used by the controller;
- fail if CPIR mode changes the controller through `sourceProbability`, posterior guidance, stopping, or truth access.

## Claim boundary

A successful experiment may be described as:

> **online/closed-loop robotic evaluation of CPIR source inference under a common PMFS active-sensing controller**.

It must **not** be described as a new CPIR active-planning policy or as evidence that the CPIR posterior itself improves trajectory selection.

If a later paper version requires CPIR-driven active planning, that must be separately derived, preregistered and ablated; it cannot be silently added to the present three-module method.

## Why the full-grid bank is still needed

Even with a controlled common planner, a new online seed produces a trajectory that is not known in advance. The full-grid bank allows M1/M2/M3 to query every visited free cell without using the hidden observation field or regenerating route-specific candidate simulations. Therefore the H01/H02/H03 full-grid banks remain valid and necessary runtime assets; no regeneration is implied by this planner boundary.
