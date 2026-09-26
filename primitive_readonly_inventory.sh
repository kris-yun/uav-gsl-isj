#!/usr/bin/env bash
set -Ee -o pipefail
out=/home/zyc/emission_transport_readonly_20260926
mkdir -p "$out"
{
  hostname
  date -u +%FT%TZ
  for root in /home/zyc/hcmc_gaden_seed_build_20260922 /home/zyc/ros2_ws/src/gaden /home/zyc/ros2_ws/src/GADEN /home/zyc/ros2_ws/src/GSL; do
    if [ -d "$root" ]; then
      printf '\nROOT %s\n' "$root"
      find "$root" -maxdepth 5 -type f \( -name 'Filament*.cpp' -o -name '*Simulation*.cpp' -o -name 'MathUtils.hpp' -o -name 'Filament*.hpp' -o -name '*Concentration*.cpp' -o -name '*World*.cpp' \) -print
    fi
  done
  printf '\nKNOWN BANK PROVENANCE\n'
  sed -n '1,100p' /home/zyc/cess_d1r_168x16_reference_20260925/pmfs_1_12/rep_01_seed_2026105001/manifest.tsv
  sed -n '1,110p' /home/zyc/cess_d1r_168x16_reference_20260925/pmfs_1_12/rep_01_seed_2026105001/spatial/metadata.json
  printf '\nBINARY\n'
  sha256sum /home/zyc/hcmc_gaden_seed_build_20260922/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator
  printf '\nHOST\n'
  free -b
  df -h /home/zyc
} > "$out/inventory.txt"
cat "$out/inventory.txt"
