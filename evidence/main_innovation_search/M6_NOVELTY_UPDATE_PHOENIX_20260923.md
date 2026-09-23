# M6 novelty update — PHOENIX near-neighbor

Date: 2026-09-23

PHOENIX-UNet (Building and Environment 2026) is a strong near-neighbor:
- obstacle-resolved gas concentration prediction;
- building geometry;
- physics prior;
- meteorological conditioning;
- source conditioning;
- unseen wind/source generalization;
- public code and ~4000-case dataset.

Therefore M6 cannot claim a generic physics-enhanced gas surrogate.

M6 remains open only under the narrower claim:

**cross-domain geometry–dynamics foundation pretraining reduces gas-specific data requirements and improves PMFS source-identification fidelity.**

Hard control:
- official GeoPT pretrained;
- identical Transolver from scratch;
- gas-specific physics surrogate;
- fixed low-data scaling curve;
- truth-source candidate rank as final gate.

If pretraining does not materially help in the low-data regime, M6 is NO-GO as the main innovation.
