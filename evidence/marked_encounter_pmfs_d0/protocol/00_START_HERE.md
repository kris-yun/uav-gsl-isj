# Marked-Encounter PMFS D0 — 2026-09-27

Status: **OPEN development bridge; no new GADEN plume; no closed loop.**

Input QA/JTD review SHA256:
`20dd51ce283449e68b644245dec9306005de73a0e0f27504ebc95bbe186b1d35`

## Why this is the next knife

Fresh three-environment analysis established that binary occurrence loses
source-discriminative information carried by positive concentration amplitude.
However, simply using continuous concentration is not novel: continuous-value
STE/GSL is established, and ICRA 2026 explicitly compares gas value, gas hit
and concentration-rank features.

The deployment question is therefore sharper:

> Can the **existing PMFS filament forward simulator itself** provide a
> source-discriminative positive-event mark, without requiring an online
> GADEN realization bank?

The current PMFS simulator already propagates individual filaments. During
recording it deliberately suppresses multiplicity:

```
if (updated[index] < t) {
    hitMap[index]++;
    updated[index] = t;
}
```

Thus several filaments occupying the same cell in the same timestep become one
binary hit.

D0 adds a read-only counter before that suppression and estimates:

- `p_s(x) = P(N_t(x)>0)`  — current PMFS presence probability;
- `m_s(x) = E[N_t(x) | N_t(x)>0]` — conditional filament multiplicity mark.

No planner/posterior/source update is modified.
