# Gate 1A review-package integrity repair

The Gate 1A exact-physics result and its evidence commit `adf0e91e66aba66c06c1161f4e6b7fe7352ff6ea` were complete before packaging. The first archive was rejected by an independent `sha256sum -c SHA256SUMS.txt` check because the packaging script's `find` included the `SHA256SUMS.txt` file while redirecting output into that same file. The resulting self-hash cannot match the completed manifest.

The packaging-only repair excludes `SHA256SUMS.txt` from its own list. It changes no source, target, wind, prediction vector, score, rank, scientific threshold, or Gate 1A decision. The failed package is preserved with a `_FAILED_SELFHASH` suffix; the review package is rebuilt from the same frozen data and independently checked again.
