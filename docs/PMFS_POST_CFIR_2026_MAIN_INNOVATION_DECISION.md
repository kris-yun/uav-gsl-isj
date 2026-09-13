# PMFS post-CFIR 2026 main-innovation decision

Date: 2026-09-13

## Decision

The single-channel causal line has established a physical action-response
effect, but it has not established causal source localization.  The latest
CFIR result closes the remaining passive time-arrow variant.  Under the current
measurement and benchmark constraints, another score, contrast, projection,
window, threshold, or fixed route is not a scientifically admissible next main
mechanism.

```text
CAUSAL_ACTION_RESPONSE_EXISTS
GLOBAL_TIME_ARROW_EXISTS
CAUSAL_SOURCE_IDENTITY_NOT_IDENTIFIED
CFIR_H03_ORACLE_PREMISE_NO_GO
CCDE_HELDOUT_ALREADY_NO_GO
NO_UNTESTED_INFORMATION_ADDING_SINGLE_CHANNEL_MODULE
```

## Evidence chain

1. M1R changes candidate-relative PMFS likelihood before Bayes and improved the
   endpoint in H01/H02, degraded H03, and improved AUC in all three exposed
   development cases.  It is a real 2/3 correction, not cross-dataset causal
   identification.
2. Rank-2 and DPISC source-blind physical motion probes created repeatable
   source effects across transport changes.  They did not map those effects to
   a unique source over the candidate support; remote zero-response sources
   remained unidentifiable and the full response shape was wrong.
3. LMBT used the strongest available oracle input, the full spatial CFD wind,
   and reached 1.6004 m on H03.  Reversed wind performed slightly better, so
   chronological transport was not source-specific.
4. CTAER's ordinal time-arrow contrast changed MAP by only 0.0294 m and failed
   its rank gate.
5. CFIR combined backward physical footprints with a candidate-wise
   forward/reverse log ratio.  The correct sign strongly beat the sign-reversed
   control, proving detectable irreversibility, but truth rank worsened from
   790 to 1,075 and MAP error worsened from 1.6004 m to 1.9810 m.

Together these results show that intervention effects and a time arrow exist,
but neither is uniquely attached to source identity in the available data.

## What the newest 2026 distant-field work changes

Gumaste et al., *Mammalian odour-guided navigation behaviour and neural
processing in relation to the odour environment*, Biological Reviews (2026),
DOI `10.1002/brv.70189`, emphasizes active sampling and plume intermittency as
navigation information:
https://pubmed.ncbi.nlm.nih.gov/42220174/

The transferable principle is to make motion create informative temporal
variation.  Rank-2 and DPISC already instantiated that principle with
source-blind physical movement, including several directions and distributed
stations.  Their failure means the review does not authorize a renamed active
sampling module on the same H03 setup.

Jones et al., *Capturing multiscale interactions in fluid flow via Lagrangian
coherent structures and modal analysis*, Physical Review Fluids 11, 094902
(2026), DOI `10.1103/kgw4-ywtm`, shows that time-resolved flow structure can
organize Lagrangian transport across scales:
https://journals.aps.org/prfluids/abstract/10.1103/kgw4-ywtm

That route needs resolved time-dependent velocity structure.  CFIR already used
simulation-known full CFD wind, which is stronger than the deployment input,
and still failed source identification.  It therefore cannot be reduced to a
single-channel real-flight module without inventing unavailable information.

The 2026 PRL time-arrow ratio, 2026 AIAA backward domain-of-dependence source
inversion, 2026 Scientific Data turbulent-intermittency database, and 2026
Nature Reviews Physics coarse-observation bound are frozen in the CFIR
literature trace.  CFIR is their direct composed test and is now NO-GO.

## CCDE status correction

The older root project instruction says CCDE held-out verification is pending.
The current repository contains the later completed evidence in
`experiments/single_channel_scsp_v1/evidence/prior_ccde_negative/` and the
archive `CCDE_HELDOUT_EVIDENCE_V3_20260807.tar.gz`.  Six held-out H01/H03 cases
ended with `CCDE_WIND_MOMENT_NOT_PHYSICALLY_SPECIFIC`; matched filtering
captured its apparent gain.  Re-running CCDE would repeat a completed negative
gate.

## Smallest condition that can reopen a causal main claim

At least one new independent physical input is required:

- a second informative chemical/sensor response kernel;
- a controlled reference-tracer excitation;
- simultaneous spatial receivers; or
- an independently qualified candidate-by-transport physical response family.

The current single-channel choice excludes the first, the factory scenario
excludes source control, the single-UAV setup excludes simultaneous receivers,
and the no-library rule excludes the fourth.  With all four excluded, causal
source identity is not identifiable from the current experiments.

## Paper-level route

Keep M1R as a transparent PMFS correction and report the 2/3 endpoint plus 3/3
AUC development result without a cross-dataset claim.  Use the intervention,
rank-2, DPISC, LMBT, CTAER and CFIR results as a rigorous identifiability study
showing why improved posterior behaviour is insufficient for causal source
attribution.  A performance paper still needs a different main algorithm with
new information or a relaxed claim; the current evidence cannot support a
causal-localization main innovation.

