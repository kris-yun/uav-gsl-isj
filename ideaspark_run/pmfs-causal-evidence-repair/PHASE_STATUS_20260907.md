# Idea-spark phase status — 2026-09-07

This run is retained as a bounded literature-grounding artifact for the CSTAR
M1/M2 revision. It is not a completed idea card and does not authorize a model
or closed-loop experiment.

## Completed

- Phase 0 connector retrieval completed in `real` mode.
- OpenAlex and Semantic Scholar supplied 115 records after deduplication.
- Relevance partition completed: 48 core, 29 adjacent and 38 off-topic. The
  off-topic records are preserved in `phase0/off_topic.md`.
- The user query, connector-degradation marker, retrieval outputs and partition
  are committed with the code/evidence snapshot.

## Incomplete / honest limits

- The arXiv connector returned no records after rate limiting/timeout retries.
- The OpenReview connector was skipped because credentials were absent.
- Semantic Scholar was intermittently rate limited; its recent-window retry did
  return records, but the full configured source coverage was not available.
- The host fast classifier command (`NOVELTY_LLM_CLASSIFY_FAST_CMD`) is not
  configured. Therefore `lit_table.md`, Phase 0 pattern tagging and all later
  idea-spark candidate/collision phases are intentionally not claimed complete.
  The `.pattern_summary_pending` sentinel remains.

## Scientific consequence

The retrieved primary sources can support a mechanism review, not a novelty or
performance guarantee. The repository review already records the transferable
principles and their limits in `docs/CSTAR_M1_M2_MECHANISM_REVIEW_20260907.md`.
The prospective implementation boundary is in
`docs/CSTAR_M1_M2_REVISION_PROTOCOL_V1_20260907.md`.

## Resume condition

Resume only with the same fresh run directory after configuring a real fast
classifier and, if desired, OpenReview credentials. Then classify all retained
records conservatively, run mandatory full-text retrieval, and continue the
skill's collision/falsification gates. Do not replace this phase with hand-made
pattern tags or web-search snippets and do not use it to justify rescue tuning.
