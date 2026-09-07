# CSTAR reusable environment evidence

`PREFLIGHT.json`: 12 realizations, 132 wind files, 3 maps; code/input bindings,
resolved sensor and explicit 2.5x field-replay clock; 8,640 stored physical wind
frames independently agree exactly. No gas body decoded or new trajectory sampled.

`selftests.log`: 22 Windows/VM-compatible synthetic regression tests (this log
is the actual VM run).

`live/H01`, `live/H02`, `live/H03`: three real stationary VGR input probes using
the newly mandatory preflight and explicit qualified numeric helper.

`INDEPENDENT_LIVE_VERIFICATION.json`: 24 positive ROS frames checked against
numeric raw wind files, dual-clock stamps and resolved live sensor parameters.
Maximum wind component error across Houses is 7.180059963252106e-09 m/s.

Execution commit: `a16ffa346a0d643c73c21591d4694f4e4413a106`.
The VM used a git archive on tmpfs because its system disk was full. Bindings
record that actual path and the actual source bytes. See the environment document
for reproduction and scope limits. No production closed-loop or model claim.
