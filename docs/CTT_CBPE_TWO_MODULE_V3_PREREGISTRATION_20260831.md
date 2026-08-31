# CTT-CBPE two-module V3 preregistration

V1 and V2 remain frozen NO-GO results.  Their positive 27/30 development signal
does not authorise closed loop because one H01 catastrophe remained and exact
stop identity was not robustly better than the exchangeable count control.

V3 changes only the temporal probability model.  M1 remains the native GADEN
`do(S=s)` physical response followed by the persistent sensor.  At each source
update, the three newly completed stops are reduced to one reached-stop count

\[
K_{srmj}=\sum_{b\in\mathcal B_j}E_{srmb}\in\{0,1,2,3\}.
\]

The three labels inside a block are exchangeable, but the five blocks remain
ordered.  One global 4-by-4 Jeffreys posterior-predictive kernel `Q` is estimated
only from ordered pairs of different frozen transport members over all simulated
Houses, sources, routes and blocks.  It reads no measured observation, native
PMFS posterior, truth or localization error.

For observed block counts `k_j`, the frozen source likelihood is

\[
L_s(k_{1:J})=
\frac{1}{8}\sum_{m=0}^{7}
\prod_{j=1}^{J}Q[K_{srmj},k_j].
\]

Thus one latent transport member persists across the complete ordered block
history and is marginalized once, after the product.  This replaces the V1
operation that marginalized a member independently inside every stop.  M1 is
the predictive generator for `K`; no separate M1 hit/count likelihood is
multiplied into `L_s`, so the same observation is not counted twice.

The carrier posterior is proportional to the frozen geometry prior times
`L_s`.  The already-preregistered V2 minimum-KL interface supplies native
PMFS's within-carrier conditional and changes no carrier evidence.  It is an
interface, not a third scientific module.

V3 is run once in two truth-separated stages on the already-opened 30
development trajectories.  It must beat PMFS by at least 10%, improve at least
20/30 pairs, avoid House degradation and every catastrophe, pass source-label
nulls, and be no worse than GLOBAL_COUNT, BLOCK_ORDER_PERMUTE and
INCOHERENT_PER_BLOCK in every primary endpoint.  Only a complete hard PASS
permits one immutable runtime pilot; it is not held-out paper evidence.
