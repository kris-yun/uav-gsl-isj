#!/bin/bash
# Collect and summarize ablation results
RESULTS_DIR="/tmp/ablation_v2"

echo "=== Ablation Results Summary ==="
echo "Condition | House | Seed | FinalDist | Status"
echo "----------|-------|------|-----------|-------"

for f in $RESULTS_DIR/*_server.csv; do
    [ -f "$f" ] || continue
    fname=$(basename "$f" _server.csv)
    house=$(echo $fname | cut -d_ -f1)
    cond=$(echo $fname | cut -d_ -f2)
    seed=$(echo $fname | sed 's/.*_s//')
    
    if [ -s "$f" ]; then
        # Read last line of server results
        last=$(tail -1 "$f")
        # Format: FAILED/SUCCESS nav_time search_time errorAll error iterations variance
        status=$(echo "$last" | awk '{print $1}')
        if [ "$status" = "FAILED" ]; then
            dist=$(echo "$last" | awk '{print $5}')
        else
            dist=$(echo "$last" | awk '{print $5}')
        fi
        echo "$cond | $house | $seed | $dist | $status"
    else
        echo "$cond | $house | $seed | - | EMPTY"
    fi
done

# Compute averages per condition
echo ""
echo "=== Per-Condition Statistics ==="
for cond in baseline pwc mac pwc_mac sdr full; do
    vals=""
    for f in $RESULTS_DIR/*_${cond}_*_server.csv; do
        [ -f "$f" ] || continue
        if [ -s "$f" ]; then
            last=$(tail -1 "$f")
            status=$(echo "$last" | awk '{print $1}')
            if [ "$status" != "FAILED" ]; then
                dist=$(echo "$last" | awk '{print $5}')
                vals="$vals $dist"
            fi
        fi
    done
    if [ -n "$vals" ]; then
        count=$(echo "$vals" | wc -w)
        mean=$(echo "$vals" | tr ' ' '\n' | awk '{s+=$1} END {printf "%.3f", s/NR}')
        echo "$cond: n=$count mean=$mean"
    fi
done
