# Loop 13 — Full-Spectrum Enhancement and Task-Preserving Nuisance Removal: NO-GO

Date: 2026-09-20
Branch: research/remote-paradigm-loop-20260919
Status: two recent remote-domain auxiliary candidates screened and rejected.

## A. Full-spectrum multi-resolution enhancement

Remote anchor:
- Nature Machine Intelligence 2026 — Ni et al., *Multi-resolution enhancement for full-spectrum neural representations* (WIEN-INR).
- The paper addresses a real limitation of compact scientific neural representations: high-frequency/fine-scale information is often over-smoothed, and uses wavelet-domain hierarchical encoding plus selective enhancement to retain full spectral content under a small parameter budget.

GSL motivation:
- project evidence shows generic predictive compression can discard fine intermittent source evidence.

### Offline proxy
- M1 proxy: source-blind next-window predictive representation.
- auxiliary proxy: compact Haar full-spectrum descriptor from eight detail bands.
- compare predictive-only, wavelet-only, and concatenated representations at 240 s.

### Result
No stable incremental benefit:
- H01: predictive ratio 0.306, wavelet 0.724, combined 0.529; predictive identity 2/2, wavelet 1/2.
- H02: predictive 0.253, wavelet 0.423, combined 0.395; all 2/2.
- H03: predictive 0.926, wavelet 0.811, combined 0.840; all remain only 1/2 in this fixed proxy.

Decision:
```
FULL_SPECTRUM_WAVELET_AUXILIARY = NO_GO_IN_CURRENT_FORM
```

The physical lesson that fine scales may matter remains valid, but adding a full-spectrum branch is not justified by current source evidence.

## B. Task-preserving nuisance removal (SPLINCE-style)

Remote anchor:
- NeurIPS 2025 — Holstege, Ravfogel, Wouters, *Preserving Task-Relevant Information Under Linear Concept Removal*.
- SPLINCE uses an oblique projection to erase an unwanted concept while exactly preserving covariance with the target task.

This was an unusually direct match to a known project failure:
ordinary nuisance projection can remove source-relevant signal.

### Offline premise
On 10 s source/wind feature windows from 120–240 s:
- nuisance concept = fast vs slow transport;
- task = SA vs SB source;
- compare:
  1. raw representation;
  2. ordinary orthogonal wind-concept projection;
  3. task-preserving oblique projection.

### Result
Transport/source directions in this proxy are already nearly orthogonal:
- H01 cosine ≈ 0.041;
- H02 ≈ -0.111;
- H03 ≈ -0.079.

Consequently SPLINCE gives essentially no incremental benefit over ordinary projection:
- H01 ratio: orth 0.6284, SPLINCE 0.6282; pair correctness both 16/26.
- H02: 0.1356 vs 0.1352; both 13/26.
- H03: 0.3228 vs 0.3224; both 25/26.

Decision:
```
TASK_PRESERVING_CONCEPT_REMOVAL_AS_M2 = NO_INCREMENTAL_MECHANISM
```

It is an elegant recent idea, but the current data do not need its unique task-preservation geometry.

## Current M2 status

Still OPEN.

The screening now strongly suggests M2 should not be another representation transform.
The remaining recurring project failure is upstream:

> when the current finite-horizon sensing history does not physically expose/distinguish source hypotheses, any forced source update is semantically wrong.

Next candidate class:
**selective prediction / abstention / evidence qualification** — an inference gate that decides whether source evidence is admissible before the probability map is sharpened.

This must be distinct from M3:
- M2 would qualify whether the current physical observation contains source-discriminative support before update.
- M3 would calibrate the final source region under dataset/environment shift.

