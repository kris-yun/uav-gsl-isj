# WIND-ALIGNMENT D0 — height vs dynamic-transport mechanism screen

Status: **offline mechanism screen only**. This is not a main innovation and
does not authorize closed-loop experiments.

The previous two hypotheses are frozen negative:
- persistent-source marginalization: null/adverse;
- evidence pseudoreplication removal: null/adverse.

The wind-contract audit established:
- observation wind uses the same underlying numbered House01 wind family;
- observation sensor height = 0.30 m;
- historical Native forward queried z = 0 m because `anemometer_frame="map"`;
- historical `/wind_value` server always selected wind state 0;
- each PMFS event averages 10 wind readings and can mix multiple wind states.

New source-blind recovery in this package adds one fact:
although the absolute receipt window repeats periodically, **all numerical
receipt-window matches for each of the 20 events correspond to exactly one
10-state wind-ID sequence**. Thus event-specific wind-state composition is
identifiable even when absolute cycle number is not.

D0 isolates two different mechanisms:
1. height mismatch (baseline/adaptation defect);
2. event-to-forward dynamic wind mismatch (scientific mechanism candidate).
