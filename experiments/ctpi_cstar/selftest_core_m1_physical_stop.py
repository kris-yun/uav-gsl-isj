"""Structural self-test for the M1P causal unit.

One navigation action fixes the sensing position for maxUpdatesPerStop internal
measurement blocks.  Only the terminal block is an independent position-level
intervention for M1P.
"""

import json
import math


blocks_per_stop = 8
stops = 4
recorded = [
    block
    for block in range(1, blocks_per_stop * stops + 1)
    if block % blocks_per_stop == 0
]

# A repeated within-stop likelihood ratio must not be exponentiated as if the
# robot had executed a fresh position intervention at every internal block.
per_block_ratio = 1.5
pseudo_replicated_odds = per_block_ratio ** (blocks_per_stop * stops)
physical_stop_odds = per_block_ratio ** stops

report = {
    "contract": "CSTAR_CORE_M1_PHYSICAL_STOP_UNIT_V1",
    "blocks_per_stop": blocks_per_stop,
    "physical_stops": stops,
    "recorded_terminal_blocks": recorded,
    "pseudo_replicated_odds": pseudo_replicated_odds,
    "physical_stop_odds": physical_stop_odds,
    "log_overconfidence": math.log(pseudo_replicated_odds / physical_stop_odds),
    "pass": recorded == [8, 16, 24, 32]
    and pseudo_replicated_odds > physical_stop_odds,
    "limits": [
        "structural causal-unit test only",
        "does not establish that the terminal block is fully independent",
        "does not establish closed-loop utility",
    ],
}

print(json.dumps(report, indent=2))
if not report["pass"]:
    raise SystemExit(1)
