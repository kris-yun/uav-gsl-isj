# BRG V1 deployment event time audit

The 72 archived OPEN GADEN realizations remain unchanged. This note concerns
only VGR/PMFS observation timestamps during later Native training collection.

The first valid 300 s Native pilot (frozen case 013) produced 53 ten-reading
measurement events after the paused-clock observation gate was repaired. Its
offline six-channel features and an online replay through `V1Session` agreed
exactly: maximum absolute difference was zero for both observation and
candidate-cue arrays over all 53 events and 596 legal candidates.

Native case 003 completed its 300 s VGR run, but the first encoder rejected
one duplicated PMFS callback `/clock` stamp: event 36 recorded two different
gas readings at 195.6 s. The immutable VGR sensor trace records those readings
as two successive publications at 195.4 and 195.6 s. The 10 readings in that
block can each be matched to a distinct ordered VGR publication. The duplicate
is a callback clock logging lag, not evidence that the same sensor reading was
used twice. We preserved the raw run, added an explicit ordered value/time
match against VGR publications, and resumed only the encoder/archiver. PMFS
gas averages, its planner, the model feature formula, the split, and the
underlying plume were not changed. All ten callbacks remain in the block.

Case 003 also passed online/offline feature replay over all 57 events and 596
legal candidates with maximum absolute difference zero. The validated feature
channels use the recorded window start/end, event gas average, and pose. The
individual publication-time check is an input integrity gate. Both original
PMFS and VGR timestamp traces remain in the host log archive.

The host episode extractor independently repeats the ordered matching for
every archived case, including early runs encoded before this checker was
installed. In the first 18 archived Native episodes, cases 003, 004, 005,
017, 025, and 026 had at least one repeated callback clock stamp; all 18
mapped every event to ten distinct VGR publications, and observed callback
clock lag was at most 0.2 s. The original PMFS event averages are retained.

The model-facing V1 sidecar reads only the current PMFS measurement block and
its raw samples, plus VGR sensor rows published by that time. It never reads
source truth or a future measurement. The original C++ `STEP` protocol and
Native candidate support remain unchanged.
