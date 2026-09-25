# DASN 0F — Second Readout-Family Replication

Date: 2026-09-25

Status: **SHARED_ERROR_REPLICATES_ACROSS_READOUT_FAMILIES**

## Readout 2

Replace ridge coordinate regression with an ordinary calibrated source-class prototype decoder.

For each odd/even probe view:
- use log(1+ppm) features;
- standardize from the training half only;
- build one prototype per source from the 8 training realizations;
- select a softmax inverse-temperature by leave-one-realization-out training-half log loss only;
- on the fresh half, produce a normalized posterior over all 168 source cells;
- use posterior-mean source position as the 2D readout.

No fresh-half target is used for calibration.

## Direction A

Train reps 1-8; diagnose reps 9-16.

Localization:
- odd mean/median/q90 error = 0.661 / 0.523 / 1.174 m;
- even mean/median/q90 = 0.830 / 0.676 / 1.663 m.

Shared error:
- T = 0.056160 m^2;
- centered x correlation = 0.2644;
- centered y correlation = 0.2550.

300 within-source pairing-destruction permutations:
- q2.5 = -0.01250 m^2;
- median = -0.00053 m^2;
- q97.5 = 0.01146 m^2;
- exceedance = 0/300.

## Direction B

Train reps 9-16; diagnose reps 1-8.

Localization:
- odd mean/median/q90 = 0.650 / 0.509 / 1.227 m;
- even mean/median/q90 = 0.826 / 0.648 / 1.633 m.

Shared error:
- T = 0.040926 m^2;
- centered x correlation = 0.2204;
- centered y correlation = 0.1881.

Permutation null:
- q2.5 = -0.00870 m^2;
- median = -0.00002 m^2;
- q97.5 = 0.00797 m^2;
- exceedance = 0/300.

## Decision

The same-realization shared localization-error signal is not specific to the ridge coordinate decoder.

Current evidence survives:
- realization-pairing destruction;
- common-gain removal;
- an equal-dimensional generic 2D factor control;
- a second ordinary readout family.

Still required before any displacement-specific interpretation:
- boundary audit;
- direct alignment with local source-sensitivity J;
- a final check against high-rank/nonidentifiable covariance explanations.