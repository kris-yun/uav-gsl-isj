# Why the single-channel repairs kept failing

## Supported diagnosis

The repeated failure is not mainly a bad weight, threshold, or optimizer.  The
failure occurs before posterior updating: PMFS assigns the measured block to
the wrong source-conditioned response law.

The physical chain is

`source -> turbulent transport -> local exposure -> delayed sensor state -> measured sample`.

Four losses occur in the current pipeline.

1. **Statistic mismatch.**  PMFS compares a measured, delayed block statistic
   with simulated filament occupancy or hit frequency.  These are not calibrated
   observations of the same random variable.
2. **Time-to-place misassignment.**  The sensor has a 0.4 s dead time and a
   1.2 s state constant.  A value measured at the current pose can have been
   created at an earlier pose.  Existing evidence shows inherited state alone
   can force the next hit in 22.7% of H02 transitions and 40.6% of H03
   transitions.
3. **Missing transport topology.**  A local wind vector is not a source-receptor
   map in rooms with obstacles and recirculation.  On the saved traces, simple
   concentration/rise/intermittency features change sign or lose discrimination
   between Houses.  The released candidate provider predicts zero before
   clipping for 59/59 positive H01 blocks, 88/88 H02 blocks, and 66/70 H03
   blocks at the true-source leaf.
4. **Posterior-only repairs cannot create a missing likelihood.**  M1R, CCDE,
   and metric-consistent SCSP can redistribute or protect existing scores.  They
   cannot recover source evidence that the response family assigned zero.  This
   explains the recurring pattern: uncertainty diagnostics improve while source
   rank or endpoint error does not.

## What the negative results rule out

- another scalar reweighting of hit/miss evidence;
- using concentration amplitude, derivative, whiff duration, or rolling
  variability as a universal distance-to-source proxy;
- a straight local-upwind ray in every House;
- another posterior blend or House-triggered fallback;
- calling the current M1R effect a transportable causal source estimator.

The exact physical response ensembles previously contained source information,
so one gas channel is not the fundamental impossibility.  The missing object is
a source-receptor likelihood that preserves transport history and sensor time.

## Decisive next question

Before building a deployable sparse-wind model, test one narrower premise:

> If the correct historical wind field is supplied, does assigning each measured
> signal to a distribution over its earlier receptor time and then transporting
> that evidence backward place the true H03 source above the controls?

If the answer is no, the proposed mechanism is wrong even under privileged
transport information and must be retired.  If yes, the remaining problem is
explicitly the online wind-field provider, not the gas channel or posterior.

