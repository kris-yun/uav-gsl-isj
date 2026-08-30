#!/usr/bin/env bash
set -euo pipefail

bank_tag=${CTT_H01_BANK_TAG:-R2}
source_root=/dev/shm/CTT_H01_WIND_BANK_FULL_20260830_${bank_tag}
target_root=/home/zyc/CTT_H01_WIND_BANK_FULL_20260830_${bank_tag}_PERSISTED
copy_root=/home/zyc/CTT_H01_WIND_BANK_FULL_20260830_${bank_tag}_PERSISTING
manifest_root=/home/zyc/CTT_H01_WIND_BANK_FULL_20260830_${bank_tag}_PERSIST_MANIFEST

test -f "$source_root/bank_summary.json"
test ! -f "$source_root/IN_PROGRESS"
test ! -e "$target_root"
test ! -e "$copy_root"
test ! -e "$manifest_root"

mkdir "$manifest_root"
(
  cd "$source_root"
  find . -type f ! -name '*.tmp.*' -print0 | sort -z | xargs -0 sha256sum
) > "$manifest_root/source_tree_sha256.tsv"

cp -a "$source_root" "$copy_root"
(
  cd "$copy_root"
  find . -type f ! -name '*.tmp.*' -print0 | sort -z | xargs -0 sha256sum
) > "$manifest_root/copied_tree_sha256.tsv"
cmp "$manifest_root/source_tree_sha256.tsv" "$manifest_root/copied_tree_sha256.tsv"

test "$(find "$copy_root" -type f -path '*/member_*/*.bin' | wc -l)" -eq 16800
test "$(find "$copy_root" -type f -name 'exact_wind_routes.bin' | wc -l)" -eq 10
mv "$copy_root" "$target_root"
sha256sum "$manifest_root/source_tree_sha256.tsv" > "$manifest_root/MANIFEST_SHA256.txt"
echo CTT_H01_BANK_PERSIST=PASS
