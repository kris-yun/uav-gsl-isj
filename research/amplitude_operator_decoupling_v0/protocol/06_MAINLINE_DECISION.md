# Mainline decision

## What is demoted

- QA-PMFS remains a failed mainline for source discrimination.
- MaxCal / world model / temporal-correlation mainline remains demoted.
- broad “marked occurrence + amplitude” novelty is unavailable due to prior
  continuous-concentration GSL work.
- the raw PMFS conditional multiplicity M is not the main method.

## What is promoted to candidate mechanism

**Observation-operator mismatch / channel decoupling**

A robust binary hit-probability channel and a discriminative amplitude channel
do not necessarily require the same spatial operator.

The specific current failure mode is:
a Gaussian blur chosen for hit-map robustness is reused on amplitude evidence,
whose fine spatial differences are needed for neighboring-source
discrimination.

## What is still missing before calling it a main innovation

1. fresh House03 confirmation;
2. sparse single-UAV observation protocol;
3. one predeclared model-mismatch condition;
4. a calibrated/noise-aware probabilistic amplitude likelihood that maps the
   confirmed observation operator back into the source probability map;
5. broader near-domain prior-art audit of observation-operator / smoothing
   choices in concentration-based GSL.

Until those pass, call this a **main-innovation candidate mechanism**, not a
finished main innovation.
