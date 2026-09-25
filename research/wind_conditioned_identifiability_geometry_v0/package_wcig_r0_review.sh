#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(git rev-parse --show-toplevel)"
R="$ROOT/research/wind_conditioned_identifiability_geometry_v0"
E="$ROOT/evidence/wind_conditioned_identifiability_geometry_v0/r0"
PKG="/home/zyc/WCIG_R0_ZERO_PLUME_REVIEW_20260925"
ARCHIVE="/home/zyc/WCIG_R0_ZERO_PLUME_REVIEW_20260925.tar.gz"
[[ -f "$E/WCIG_R0_RESULT.json" ]] || { echo "missing WCIG result" >&2; exit 2; }
[[ -f "$E/WCIG_R0_LOCAL_WIND_SAMPLES_4x10x11x3x3.npy" ]] || exit 3
rm -rf "$PKG"
mkdir -p "$PKG"/{repo,data}
cp "$R/WCIG_R0_ZERO_PLUME_CHARTER_20260925.md" \
   "$R/WCIG_R0_IMPLEMENTATION_FREEZE_20260925.md" \
   "$R/analyze_wcig_r0.py" "$R/package_wcig_r0_review.sh" "$PKG/repo/"
cp "$ROOT/01_idea/GENERALIZATION_REFOUNDATION_POSTMORTEM_20260925.md" "$PKG/repo/"
cp "$ROOT/evidence/local_stochastic_confusability_v0/crosswind_d0/LSC_CROSSWIND_D0_RESULT.json" "$PKG/repo/"
cp "$ROOT/evidence/local_stochastic_confusability_v0/crosswind_d0/LSC_CROSSWIND_D0_SOURCE_PANEL.tsv" "$PKG/repo/"
cp "$ROOT/evidence/causal_compositional_plume_world_model_v1/C0_5_HOUSE_WIND_INVENTORY_20260923.json" "$PKG/repo/"
cp "$ROOT/research/source_lineage_lagrangian_v2/export_gaden_wind_3d.py" \
   "$ROOT/research/source_lineage_lagrangian_v2/l1_filament_transition_audit.py" \
   "$ROOT/research/local_stochastic_confusability_v0/analyze_lsc_crosswind_d0.py" \
   "$PKG/repo/"
cp "$E"/WCIG_R0_* "$PKG/repo/"
cp "/home/zyc/LSC_CROSSWIND_D0_REVIEW_20260925.tar.gz" \
   "$PKG/data/upstream_lsc_crosswind_d0_review.tar.gz"
{
  echo "branch=$(git branch --show-current)"
  echo "head=$(git rev-parse HEAD)"
  echo "status:"
  git status --short
} > "$PKG/repo/package_git_state.txt"
(cd "$PKG"; find . -type f ! -name SHA256SUMS.txt -print0 | sort -z |
  xargs -0 sha256sum > SHA256SUMS.txt; sha256sum -c SHA256SUMS.txt --quiet)
rm -f "$ARCHIVE"
tar -C /home/zyc -czf "$ARCHIVE" "$(basename "$PKG")"
echo "archive=$ARCHIVE"
stat -c 'bytes=%s' "$ARCHIVE"
sha256sum "$ARCHIVE"
