# Implementation-only freeze

## Required software behavior

Create a development amplitude-readout interface with four explicit arms:

- `u_nearest`
- `u_footprint`
- `rawu_nearest`
- `rawu_footprint`

The implementation MUST make it impossible to confuse:
- native hit-map smoothing,
- amplitude-map smoothing,
- physical/sampling projection.

## Native occurrence channel

No changes:
- native `p`;
- Gaussian blur;
- obstacles;
- wind mixing;
- planner;
- threshold;
- source candidates.

## Amplitude channel

Default development candidate:
`rawu_footprint`.

However, because OPEN ranking is identical for rawu nearest/footprint, this
choice is an interface/physical-observation definition, NOT a claim that
footprint averaging created the observed improvement.

Use the frozen probe contract to compute rectangular area weights.
Do not silently renormalize footprint support outside the map.

## Score

Keep the archived B2 rule unchanged:

`g_hat_s = max(0, m_s^T y / m_s^T m_s)`

`SSE_s = ||y - g_hat_s m_s||^2`.

No mark profile.
No B0+B2 fusion.
No temperature.
No softmax posterior.
No change of tie rules.

## Reproduction

Implementation must reproduce all four OPEN arms byte/numerically consistently
with the supplied Pro development package.

Expected summary:

env0:
- all 4 arms: rank 1.333333 / Top1 .75

env1:
- u_*: 1.500000 / .583333
- rawu_*: 1.291667 / .791667

env2:
- u_*: 1.458333 / .583333
- rawu_*: 1.208333 / .791667

If these do not reproduce, fix only data-axis / implementation mismatch.

## Output interface

Save:
- projection matrix;
- template map type (`u` or `rawu`);
- template vector per candidate/probe;
- gain per candidate/target;
- SSE per candidate/target;
- rank, unique Top1, paired-neighbor margin;
- offline template-build time;
- per-target online scoring time;
- memory cost.

This implementation task creates NO scientific PASS label.
