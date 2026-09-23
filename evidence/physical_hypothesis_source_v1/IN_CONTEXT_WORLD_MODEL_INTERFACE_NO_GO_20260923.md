# In-context world-model / operator-learning interface kill

Date: 2026-09-23

Status: **NO-GO AS DIRECT MAIN TRANSFER**

## Mother idea screened

Recent ICLR-2026 work on in-context world models distinguishes environment recognition from environment learning and shows that a world model can adapt to a novel system from a sufficiently long and diverse interaction context. Related in-context operator learning learns a new differential operator from prompted input-output examples without weight updates.

This is scientifically attractive because PMFS currently assumes a fixed transport world model.

## Interface audit for mobile GSL

The mobile GSL interaction interface is not the same as the system-identification interface required by those methods.

Online, the robot controls its **observation location**. Its motion does not perturb:
- the gas source,
- the wind field,
- the plume transport dynamics,
- or a known forcing/boundary condition of the plume.

The run contains one unknown source and one plume realization. Historical samples provide many pairs
`(measurement position, observed gas)`, but they are samples of one unknown output field, not prompted pairs
`(known source/forcing, resulting plume field)` from which a source-to-field operator can be identified.

Therefore:
- environment **learning** of the source-to-plume operator from the online context is not identified by the current interaction contract;
- environment **recognition** from map/wind context is possible, but reduces to selecting/conditioning on previously learned environments and does not solve the novel-environment model-reality gap by itself.

This is the same category of semantic-interface failure that invalidated direct ANI transfer: the external mother method assumes a controllable/observed system-identification interface that PMFS GSL does not possess.

## Decision

Do not build a large in-context neural world model yet. It would require either:
1. known calibration releases / controlled plume interventions, or
2. a large offline meta-training corpus rich enough that map/wind context alone identifies the transport operator in held-out environments.

Neither is established by the six authoritative R2 runs.

## Productive consequence

The UAV *does* control the observation operator: it chooses where to sample next.

Therefore the next mother-idea screen should target **active identifiability / experimental design**: use movement to acquire measurements that break source equivalence under forward-model uncertainty, rather than trying to infer more from an already non-identifying support set.

This is not yet a method proposal. It is the next mechanism question:
> do there exist reachable measurement locations at which the currently confused source candidates become strongly separable in a way that is stable across independent plume realizations?

If not, active design cannot rescue PMFS either.
