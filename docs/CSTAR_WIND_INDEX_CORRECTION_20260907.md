# Raw-query wind-index contradiction found before controlled extraction

The extraction adapter preflight at source `14fe15b` rejected H02/H03:
maximum archived gas/wind discrepancy 0.003761199890725781 and
0.04369001081885038 respectively. It did not extract any controlled histories.

Root cause: archived `house1_raw_query.cpp` explicitly sorted wind filenames
lexicographically. The sequence becomes 0,1,10,2,...,9. GADEN
`PlaybackSimulation` reads the numeric wind index from each gas frame header
and `WindSequence` uses that index directly in its input vector. The actual
player's `PathUtils.hpp` already sorts numeric wind suffixes. Thus helper and
player were not interchangeable. Example: header index 6 selected file 5 in
the helper, but file 6 in the player.

The previously accepted H01 environment probe used this helper. Its map,
stamps and sensor-input delivery checks remain valid, but bridge-to-receiver
wind equality alone did **not** establish correct physical wind-index binding.
Do not claim that old H01 wind semantics are fully qualified. Preserve the old
audit and attach this correction, not silently overwrite its raw evidence.
Raw generator provenance and numeric wind fingerprints remain unchanged.

The new `cstar_numeric_wind_raw_query.cpp` changes only wind ordering, checks
contiguous numeric names, and builds to a new executable. It does not replace
the old binary or modify ROS/GADEN source. Controlled extraction independently
reads each gas header's index and the matching original numeric wind file to
check every sampled vector. H02/H03 must also match archived ROS frames.
For H01 the historical gas must match, while the wrong archived wind is kept
as an explicit counterexample. Before production closed loop, use the new
helper in a targeted H01 live input probe; the old executable is prohibited.

Routes, seeds, source positions, release fingerprints and split are unchanged.
This is a reproducible implementation contradiction, not outcome-based tuning.
