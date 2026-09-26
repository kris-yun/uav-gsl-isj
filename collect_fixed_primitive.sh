#!/usr/bin/env bash
set -Ee -o pipefail
out=/home/zyc/emission_transport_readonly_20260926
src=/home/zyc/hcmc_gaden_seed_build_20260922
{
  cat "$src/build_manifest.txt"
  cat "$src/seed_only_source.diff"
  find -L "$src/src" -maxdepth 10 -type f \( -name '*.cpp' -o -name '*.hpp' -o -name '*.h' \) -print
  printf '\nSOURCE ROOT LINKS\n'
  ls -la "$src/src"
  grep -E 'CMAKE_HOME_DIRECTORY|gaden_core' "$src/build/gaden_common/CMakeCache.txt" | head -30
} > "$out/source_inventory.txt"
cat "$out/source_inventory.txt"
tar -czhf "$out/fixed_source.tar.gz" -C "$src" src build_manifest.txt seed_only_source.diff
