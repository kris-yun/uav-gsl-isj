# Source-blind local prediction diagnostic

Fixed ridge=1; ten past frames; fit on the other two Houses; all 84 route cases
per held-out House. No source coordinates/identity, absolute map coordinates,
future gas or future wind enter the features. FROZEN_CONFIG was written before
fitting. Raw predictions and fitted coefficients are included.

| House | persistence log-ppm MSE | history-only | with route |
|---|---:|---:|---:|
| H01 | 0.025706 | 0.020251 | 0.023442 |
| H02 | 0.063971 | 0.062534 | 0.061982 |
| H03 | 0.032228 | 0.027580 | 0.027011 |

With-route beats persistence by 8.8%, 3.1%, 16.2%, respectively. The route
increment over history-only fails H01, so the declared all-House screen is
LOCAL_ROUTE_SCREEN_NO_GO. Do not weaken it after seeing the results. This
baseline has no source-hypothesis effect and predicts marginal means only;
it does not constitute a full CPO/first-passage law or causal innovation.

Reproduce with `python experiments/ctpi_cstar/screen_m2_local_prediction.py
--out NEW_EMPTY_OUTPUT`. Existing repeated-use development data do not provide
virgin confirmation. Closed-loop gains have not been tested.
