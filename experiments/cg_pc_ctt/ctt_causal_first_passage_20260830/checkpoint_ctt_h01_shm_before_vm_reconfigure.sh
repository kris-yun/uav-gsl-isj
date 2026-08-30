#!/usr/bin/env bash
set -euo pipefail

source_root=/dev/shm/CTT_H01_WIND_BANK_FULL_20260830_R1
checkpoint_root=/home/zyc/CTT_H01_WIND_BANK_FULL_20260830_R1_PRE_VCPU_CHECKPOINT
manifest_root=/home/zyc/CTT_H01_WIND_BANK_FULL_20260830_R1_PRE_VCPU_MANIFEST

test -f "$source_root/IN_PROGRESS"
if [[ -e "$checkpoint_root" || -e "$manifest_root" ]]; then
  echo CTT_H01_PRE_VCPU_CHECKPOINT_REFUSE_EXISTING
  exit 2
fi

mkdir "$manifest_root"
(
  cd "$source_root"
  find . -type f -name '*.bin' -print0 | sort -z | xargs -0 sha256sum
) > "$manifest_root/source_sha256.tsv"
find "$source_root" -type f -name '*.bin' | wc -l > "$manifest_root/source_count.txt"

cp -a "$source_root" "$checkpoint_root"
(
  cd "$checkpoint_root"
  find . -type f -name '*.bin' -print0 | sort -z | xargs -0 sha256sum
) > "$manifest_root/checkpoint_sha256.tsv"
find "$checkpoint_root" -type f -name '*.bin' | wc -l > "$manifest_root/checkpoint_count.txt"

cmp "$manifest_root/source_sha256.tsv" "$manifest_root/checkpoint_sha256.tsv"
cmp "$manifest_root/source_count.txt" "$manifest_root/checkpoint_count.txt"
cat "$manifest_root/source_count.txt"
echo CTT_H01_PRE_VCPU_CHECKPOINT=PASS
