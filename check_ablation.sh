cat /tmp/v8_exp/ablation/ablation_results.csv 2>/dev/null
echo "---"
tail -5 /tmp/v8_exp/ablation/run.log 2>/dev/null
echo "---"
wc -l /tmp/v8_exp/ablation/ablation_results.csv 2>/dev/null