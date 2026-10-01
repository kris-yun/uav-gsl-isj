# H0 INVALID recovery note — exact snapshot differencing

Date: 2026-10-01

Parent decision remains:

\`TS_P3T_H0_INVALID_STOP\`

Do not relabel or overwrite that decision.

## What the P0 audit actually found

The authoritative TNQC archive is intact and its selected hashes pass. The failure is narrower:

- the exact completed measurement-block event stream was not retained;
- therefore an arbitrary simulator-time window such as terminal-minus-40 s cannot be rebuilt at 1e-10 map parity from rounded traces/logs.

However, the archive **does retain the full PMFS measured map at every source update**, including update4 and update5 for all four R1 cases.

This creates a new exact route that does not require event reconstruction.

## Why snapshot differencing is exact for the PMFS observation state

For every measurement event and free cell, Native PMFS updates

\[
L \leftarrow L + a - L_0
\]

where \(L\) is log-odds, \(a\) is the event's propagated auxiliary log-odds and \(L_0\) is the fixed prior log-odds.

It also updates

\[
\omega \leftarrow \omega + q
\]

and computes confidence from

\[
c=1-\exp(-\omega/\sigma_\omega^2).
\]

Therefore the contribution of all events between two archived snapshots A and B is exactly

\[
\Delta L=L_B-L_A,\qquad
\Delta\omega=\omega_B-\omega_A.
\]

A map containing **only** that interval, initialized from the original prior, is

\[
L_{\rm interval}=L_0+\Delta L,
\qquad
\omega_{\rm interval}=\Delta\omega,
\qquad
c_{\rm interval}=1-\exp(-\Delta\omega/\sigma_\omega^2).
\]

No rounded gas/wind trace and no callback-boundary guess is needed.

The fields \`distanceFromRobot\` and \`originalPropagationDirection\` are not used by \`sourceProbFromMaps\`; only measured probability and confidence enter the source score.

## What can and cannot be recovered

Can be recovered exactly:
- the last **source-update interval** observation state, update4 -> update5;
- its exact log-odds contribution;
- its exact omega/confidence contribution;
- the fraction of terminal omega inherited from earlier updates.

Cannot be recovered exactly:
- the originally preregistered terminal-minus-40 s arbitrary window.

Thus H0 stays INVALID. A separate H0-R experiment is permitted to test the algorithm-native last-update interval without changing H0 retrospectively.

## Why H0-R is scientifically useful

The four last-update durations are about 50–53 s, close to the frozen candidate forward horizon of 40 s and defined entirely by the historical PMFS scheduler.

H0-R asks only whether removing older observation memory makes the already-saved candidate predictions more source-compatible.

A positive H0-R is evidence of a temporal-state mismatch. It is **not** evidence that forgetting is the final method.

Only after a positive H0-R may H1 compare:
- recency forgetting, versus
- a persistent hidden transport state that retains and evolves old plume information.
