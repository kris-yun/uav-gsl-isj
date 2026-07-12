#!/bin/bash
for h in House02 House03 House04 House05 House06 House07 House08 House09 House10 House11 House12 House13 House14 House15 House16 House17 House18 House19 House20; do
    src="/home/zyc/vgr_data_scenarios/$h/$h/OccupancyGrid3D.csv"
    dst="/home/zyc/vgr_data_scenarios/$h/OccupancyGrid3D.csv"
    if [ -f "$src" ] && [ ! -f "$dst" ]; then
        ln -s "$src" "$dst"
        echo "Linked: $h"
    elif [ -f "$dst" ]; then
        echo "Exists: $h"
    else
        echo "No data: $h"
    fi
done
