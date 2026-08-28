#!/usr/bin/env bash
set -euo pipefail

target=/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/synthetic_native
expected=/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/synthetic_native
resolved=$(realpath "$target")

[[ "$resolved" == "$expected" ]]
if find "$target" -type f -print -quit | grep -q .; then
    echo "PF_DEI_REFUSE_NONEMPTY_SYNTHETIC_CLEAN=$target" >&2
    exit 6
fi

rm -rf -- "$target"
echo "PF_DEI_REMOVED_EMPTY_FAILED_OUTPUT=$target"
