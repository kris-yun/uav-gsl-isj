# Reserve M1 Screen — State-first and Koopman/System-ID candidates

Date: 2026-09-19
Branch: research/remote-paradigm-loop-20260919
Status: INTERNAL SCREENING ONLY

## Candidate R1 — State-first inverse physical inference

### Recent remote-field provenance

Primary:
- Nature Machine Intelligence 2026 — Li et al., *Current-diffusion model for metasurface structure discoveries with spatial-frequency dynamics*.
- Nature Machine Intelligence 2026 News & Views — Chen, *Learning intermediate physical states for inverse metasurface design*.

Supporting:
- Nature Machine Intelligence 2025 — sparse high-dimensional field reconstruction with differentiable learning.
- Nature Communications 2025 — unseen nonlinear dynamics reconstruction from sparse observations.

Transferred principle:
> infer a physically meaningful intermediate response state before inferring the hidden source parameter.

GSL novelty collision:
- Advanced Robotics 2026 already performs unsupervised diffusion-state classification for OSL.
- Advanced Materials 2026 AROMA maps evolving plume dynamics into a unified latent representation for simultaneous odor identity and 3-D source localization.

Therefore “learn an intermediate plume/diffusion state, then localize” is not clean enough by itself.

### Existing-data proxy

A fixed transport-response state was formed from:
- first/last threshold arrival,
- exposure fraction,
- burst/blank statistics,
- upper-tail concentration statistics,
- low-order autoregressive dynamics.

Held-wind source identity:
- H01: 2/2 at 120 s, 1/2 at 180 s, 2/2 at 240 s.
- H02: 0/2 at 120 s, 2/2 at 180 s, 2/2 at 240 s.
- H03: 2/2 at 120 s, 2/2 at 180 s, 1/2 at 240 s.

Interpretation:
- state-first is useful after physical support appears;
- there is no single handcrafted intermediate state that is uniformly sufficient;
- latest OSL diffusion-state work increases direct novelty collision.

Verdict:
**R1 = AUXILIARY/RESERVE ONLY, NOT M1.**

---

## Candidate R2 — Koopman / dynamical-system spectral source identity

### Recent remote-field provenance

Primary:
- ICML 2025 — Xu et al., *ResKoopNet: Learning Koopman Representations for Complex Dynamics with Spectral Residuals*.
- Nature Communications 2026 — *Adversarial dynamical systems characterize when data-driven learning succeeds or fails*, with Koopman spectral learning used as the principal theoretical testbed.
- Nature Communications 2026 — Koopman global linearization for complex contact dynamics.

Scientific object:
- Koopman spectral/eigenfunction representation of nonlinear dynamics;
- spectral residual as a certification object.

Proposed GSL translation:
> source location is a persistent hidden parameter whose turbulent response induces source-specific dynamical spectral structure; infer source from that structure rather than instantaneous concentration.

### Existing-data proxy

A low-order AR model was used as a conservative proxy for local linear dynamical/spectral fingerprints.

AR-feature held-wind identity:
- H01: 2/2 at 120/180 s; mostly 2/2 at 240 s before feature standardization choices.
- H02: 0/2 at 120 s, 2/2 at 180/240 s.
- H03: often 2/2 at 120/180 s but degrades to 1/2 by 240 s.

A standardized AR + extreme-tail combination was then tested:
- H01 240 s: AR 1/2, extreme-tail 2/2, combined 2/2.
- H02 180/240 s: all 2/2 once support appears.
- H03 120/180 s: AR 1/2, extreme-tail 2/2, combined 2/2.
- H03 240 s: AR, extreme-tail and combined all fall to 1/2.

Interpretation:
- dynamical-system fingerprints contain source information;
- however they are not transport-stable in the difficult H03 late regime;
- the failure cannot be repaired by simply appending tail statistics.

Novelty:
- no direct 2025/2026 GSL Koopman source-localization paper was found in the focused search.
- nevertheless, the existing-data mechanism is weaker than the predictive/rare-event candidate because its strongest proxy still fails H03 late transport.

Verdict:
**R2 = RESERVE M1, CURRENT NO-GO FOR PROMOTION.**

---

## Important collision discovered during this screen

Advanced Materials 2026:
*Receptor-Mimetic Stereo Olfaction for Simultaneous Odor Recognition and Spatial Localization* (AROMA).

Relevant scope:
- receptor-mimetic multi-channel sensors;
- spatially separated “stereo” arrangement;
- onset/rise/amplitude plume dynamics;
- multi-task Transformer;
- unified latent representation for mixture identity + 3-D source localization;
- room-scale mobile-robot demonstration.

Consequence:
- generic claims such as “encode plume temporal dynamics in a latent space for localization” are already occupied.
- the active candidate must be distinguished by its **training principle and physical evidence semantics**, not merely by using temporal latent features.

The current predictive + extreme-event candidate survives only if:
1. latent prediction (not supervised temporal encoding) is load-bearing;
2. rare/extreme-event preservation is incremental and separately falsifiable;
3. output remains a source probability map under sparse single-UAV sensing;
4. cross-house / DNS / real-tunnel transfer is demonstrated.

