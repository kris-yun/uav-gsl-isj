#!/usr/bin/env bash
set -Ee -o pipefail
out=/home/zyc/emission_transport_readonly_20260926/open_inputs
mkdir -p "$out"
cp /mnt/hgfs/workspace/GADEN_files/scenarios/House02/OccupancyGrid3D.csv "$out/OccupancyGrid3D.csv"
wind=/mnt/hgfs/workspace/GADEN_files/scenarios/House02/gas_simulations/3,5-1_slow/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind
for k in {0..10}; do cp "$wind/wind_iteration_$k" "$out/wind_iteration_$k"; done
cp /home/zyc/rmfe_filament_extractor_omp.cpp "$out/extractor.cpp"
cp /home/zyc/cess_d1r_168x16_reference_20260925/pmfs_1_12/rep_01_seed_2026105001/spatial/metadata.json "$out/cube_metadata.json"
cp /home/zyc/cess_d1r_168x16_reference_20260925/pmfs_1_12/rep_01_seed_2026105001/manifest.tsv "$out/run_manifest.tsv"
cp /home/zyc/cess_d1r_168x16_reference_20260925/pmfs_1_12/rep_01_seed_2026105001/generation.log "$out/generation.log"
cp /home/zyc/emission_transport_readonly_20260926/inventory.txt "$out/vm_inventory.txt"
sha256sum "$out"/* > /home/zyc/emission_transport_readonly_20260926/open_inputs_sha256.txt
tar -czf /home/zyc/emission_transport_readonly_20260926/open_inputs.tar.gz -C "$out" .
