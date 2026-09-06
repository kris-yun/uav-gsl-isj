#!/usr/bin/env bash
set -euo pipefail

# Locate a checkout of kris-yun/uav-gsl-isj without assuming the obsolete
# /home/zyc/gsl_ws/src/GasSourceLocalization path.  This script is read-only.

candidates=()
[[ -n "${REPO_ROOT:-}" ]] && candidates+=("${REPO_ROOT}")
candidates+=("$PWD")
candidates+=(
  "/home/zyc/CTPI_G2_M12_SEED12_20260905/repo"
  "/home/zyc/uav-gsl-isj"
  "/home/zyc/GasSourceLocalization"
)

is_target_repo() {
  local d="$1"
  [[ -d "$d/.git" ]] || return 1
  local remote
  remote=$(git -C "$d" remote get-url origin 2>/dev/null || true)
  [[ "$remote" == *"kris-yun/uav-gsl-isj"* ]] || return 1
  git -C "$d" rev-parse --is-inside-work-tree >/dev/null 2>&1
}

for d in "${candidates[@]}"; do
  if is_target_repo "$d"; then
    realpath "$d"
    exit 0
  fi
done

# Bounded fallback: inspect plausible Git roots under /home/zyc only.  Do not
# traverse mounted experiment archives or mutate any checkout.
while IFS= read -r gitdir; do
  d=${gitdir%/.git}
  if is_target_repo "$d"; then
    realpath "$d"
    exit 0
  fi
done < <(find /home/zyc -maxdepth 5 -type d -name .git 2>/dev/null | sort)

echo "CSTAR_REPO_NOT_FOUND: set REPO_ROOT to a checkout whose origin is kris-yun/uav-gsl-isj" >&2
exit 2
