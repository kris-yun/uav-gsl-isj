# Literature trace and claim boundary

Checked 2026-09-13.  Publisher or proceedings pages are preferred; publication
status is stated explicitly.

## Direct scientific anchors

1. Zhang et al., **Advanced electronic noses for future robotic olfaction**,
   *npj Robotics* 4, 11 (2026), DOI `10.1038/s44182-025-00071-y`.
   Publisher: https://www.nature.com/articles/s44182-025-00071-y
   The review explicitly calls for timing layers that model sensor hysteresis
   and recovery using deconvolution or state observers, align timestamps, and
   combine transport physics with wind/intermittency.  It supports the sensor-
   time layer, not the full LMBT estimator.

2. Kathman et al., **Neural dynamics for working memory and evidence integration
   during olfactory navigation in Drosophila**, *Nature Communications* 17,
   9082 (2026).
   Publisher: https://www.nature.com/articles/s41467-026-75945-2
   It shows that intermittent odor evidence is integrated over seconds and that
   useful persistence is plume-statistics dependent.  It supports retaining
   temporal evidence while warning against a universal instantaneous feature.

3. Dadheech and Turner, **Simulating out-of-sample atmospheric transport to
   enable flux inversions**, *Atmospheric Chemistry and Physics* 26, 427-441
   (2026), DOI `10.5194/acp-26-427-2026`.
   Publisher: https://acp.copernicus.org/articles/26/427/2026/index.html
   It frames upwind influence as source-receptor footprints and demonstrates
   out-of-region transport emulation.  It supports the footprint object and
   cross-domain portability requirement.  LMBT V1 does not adopt its network.

4. Huang et al., **Operator Learning with Domain Decomposition for Geometry
   Generalization in PDE Solving**, ICLR 2026.
   Proceedings: https://proceedings.iclr.cc/paper_files/paper/2026/hash/710445227fa8c1b6a9ceada902dd4741-Abstract-Conference.html
   It shows that geometry transfer requires explicit local-to-global domain
   structure.  It supports treating obstacles as part of the operator, not as a
   House ID.  The current project rule forbids adding a new network, so V1 uses
   the physical field directly.

5. Chen, Andreou and Bollt, **Assimilative causal inference**, *Nature
   Communications* (2026), DOI `10.1038/s41467-026-68568-0`.
   Publisher: https://www.nature.com/articles/s41467-026-68568-0
   It casts causal assessment as an inverse problem over stochastic dynamics.
   It supports the inverse-causal framing, but its assumptions do not prove
   source identification in this benchmark.

## Closest collision

Carbone and Piro, **Learning Backward Transport for Source Localization**,
arXiv `2607.26892` (29 July 2026), preprint; no peer-reviewed top venue was
verified.
https://arxiv.org/abs/2607.26892

It already uses backward passive-tracer propagators, a Schrodinger-bridge view,
multiple detections, and a learned Gaussian propagator to generate a search
drift in homogeneous 2-D turbulence.  Therefore the following claims are
forbidden:

- first backward-transport gas source localization;
- first use of multiple detections as backward endpoint evidence;
- novelty from the Schrodinger-bridge name alone.

The remaining testable difference is sensor-state-induced lag marginalization
plus obstacle/time-conditioned receptor footprints used as a source likelihood,
with no learned propagator, source bank, or planner change.

## Retrieval limitation

The local idea-spark multi-connector run was attempted, but arXiv and Semantic
Scholar were rate-limited and OpenAlex/Semantic Scholar output hit a Windows GBK
encoding failure.  The papers above were independently checked through live
publisher/proceedings pages.  The collision search is sufficient for a premise
test, not a final manuscript novelty claim.

