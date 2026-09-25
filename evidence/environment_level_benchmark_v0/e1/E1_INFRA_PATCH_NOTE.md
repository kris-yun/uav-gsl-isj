# E1 evidence rerun infrastructure patch

The first E1 run succeeded in a new output directory and passed independent
geometry verification. After the branch acquired the separately frozen
`z_source=0.20 m` charter amendment, E1 was rerun to refresh charter hashes.
The rerun encountered a SHA-manifest self-reference because the existing
output directory already contained `SHA256SUMS.txt`.

The only code change excludes `SHA256SUMS.txt` from its own input list. Probe
selection, source selection, E1A/E1B criterion, source height, environment
roles, reuse joins, and budget calculation were unchanged. The corrected rerun
must reproduce the same 90 probes, 18 source cells, E1A decision, and 168-run
provisional budget, then pass the independent checker again.
