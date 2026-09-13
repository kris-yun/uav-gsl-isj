# MC-SCSP H03 seed11 one-shot verdict

Status: `MC_SCSP_H03_SEED11_NO_GO`

The preregistered one-shot development replay was executed once after commit
`e651e77` had been pushed. It used H03 seed11 and the first three native source
updates from the immutable CCDE archive.

## Primary result at update 2

| arm | MAP error (m) | medoid error (m) | candidate rank | 90% coverage | high-confidence wrong mass |
|---|---:|---:|---:|---:|---:|
| Native PMFS | 11.416 | 10.866 | 16 | false | 1.000000 |
| Plain matched-source filter | 12.004 | 12.600 | 20 | false | 0.999999 |
| Legacy SCSP | 12.093 | 12.358 | 22 | false | 0.999825 |
| Metric-consistent SCSP | 12.093 | 11.498 | 22 | true | 0.997357 |

The corrected geometry passed its mathematical property check: the maximum
weighted source/nuisance orthogonality error across the three updates was
`1.56e-14`. It improved 90% coverage and high-confidence wrong mass relative
to legacy SCSP and did not materially underperform the plain matched-source
filter.

It failed the primary localization condition. Its best final error ratio to
native PMFS was `1.058`, so neither MAP nor medoid error improved, let alone by
the preregistered 20%. Metric consistency repaired the implementation but did
not recover missing source-location information.

## Scientific decision

Stop this mechanism. Do not tune the energy threshold, lambda, alpha, rank
tolerance or nuisance set on H03 seed11, and do not expand it to another seed.
The previous causal line and direct CCDE wind deprojection are also retained as
negative evidence.

For the planned small flight, proceed only with a fair single-channel PMFS
baseline/measurement study using ethanol and the VOC output. Treat the flight
as a sensor/forward-model transfer test until the vendor supplies the raw
channel and timing contract. A smoke-cake/PM2.5 run remains a separate aerosol
robustness study.
