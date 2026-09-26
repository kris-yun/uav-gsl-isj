# Event wind-state recovery result

Source-blind result from the uploaded wind-contract review assets:

- 20 events inspected.
- Match criterion: 10 consecutive trace rows at the event site, speed absolute
  error <= 1e-6 m/s and circular-direction error <= 1e-6 rad.
- Absolute matching windows are periodic and non-unique.
- For **every one of the 20 events**, all matching absolute windows map to
  exactly **one** 10-state ID sequence.
- Therefore absolute cycle number is unresolved, but event-specific wind-state
  composition/order is identified for the D0 mixture diagnostic.

This does not retroactively change the prior audit's frozen decision. It is a
new derived source-blind observation used only to define the next offline gate.
