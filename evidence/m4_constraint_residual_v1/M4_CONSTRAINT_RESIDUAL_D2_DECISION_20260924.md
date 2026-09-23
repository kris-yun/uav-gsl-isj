# M4 Constraint-Active Residual D2 Decision — STOP

Date: 2026-09-24
Branch: `research/m4-constraint-residual-v1`
Workflow run: `35914760433`
Decision: **CONSTRAINT_LOCAL_RESIDUAL_NO_GO**

## Frozen question

Can an extremely small source-blind Eulerian residual, conditioned on the
pre-registered boundary/strain/vertical-wind mechanisms, repair M4-v3's wrong
W1→W2 response geometry without replacing the coarse transport?

## Models

All correctors have exactly 64 parameters (Conv2d 7→1, 3×3).

- **gated**: physical features; correction active only in
  wall<=1 downsampled cell OR top-25% strain OR top-25% |Wz|.
- **global**: same physical features and capacity; correction allowed globally.
- **agnostic**: same capacity, but all physical context channels are zeroed.

Frozen M4-v3 checkpoints: 1729 and 2718.
Training cells: S1-W1, S2-W1, S1-W2.
Held-out development cell: S2-W2.
No source ID/location enters the corrector.

## Result

### Physically gated residual

- field MSE improves in 4/4;
- mean wind-cosine gain = **-0.00316**;
- held-out wind cosines remain approximately **0.336–0.381**;
- correction/base norm ≈ **0.415**;
- 0/4 pass wind-cosine > 0.5.

This is decisive negative evidence for the simple localized-residual hypothesis.

### Global physical-context residual

- field MSE improves in 4/4;
- mean wind-cosine gain = **+0.09107**;
- held-out wind cosines improve to approximately **0.432–0.475**;
- still 0/4 pass >0.5;
- correction/base norm ≈ **0.510**, violating the predeclared <=0.5
  non-dominance guard.

This is a real weak signal that physical context contains useful information,
but the field-level residual has to become too large and still does not recover
the required intervention geometry.

### Agnostic residual

- field MSE improves in 4/4;
- mean wind-cosine gain = **-0.01196**;
- held-out wind cosines approximately **0.330–0.370**.

Therefore the +0.09 signal of the global model is not reproduced by a
coarse-field-only residual. Physical context matters, but this implementation
is insufficient.

## Relation to earlier oracle and controls

Earlier source-blind oracle attribution found that ideal correction restricted
to near-wall, high-strain, or high-|Wz| regions can cross the 0.5 cosine gate.
However:

- explicit wall-slide surgery produced essentially no improvement;
- simple vertical exchange reduced field MSE but degraded wind-response
  amplitude/cosine;
- the present learned hard-gated residual also fails.

Thus the oracle result identifies **where error concentrates**, not a sufficient
Eulerian correction law.

## Stop rule

Do not:
- increase corrector width/depth on S2-W2;
- alter the physical mask against this opened holdout;
- relax the 0.5 wind-cosine gate;
- integrate this residual into PMFS/ROS;
- run closed loop.

## Scientific consequence

M5 is not promoted by this test.

If M5 is revisited, it must be tested at its native Lagrangian object:
**source-agnostic particle/filament transition supervision**, with real saved
GADEN trajectories and downstream candidate rank. Field-level residual rescue is
closed.

Current compute priority moves to M6 GeoPT, whose prior blocker was checkpoint
access rather than a scientific NO-GO.
