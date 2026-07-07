#!/bin/bash
OUT=/tmp/v2_exp
mkdir -p $OUT
echo "method,scenario,seed,final_error,localized,steps,type" > $OUT/results_v2.csv
SRC_X="-0.60"
SRC_Y="1.95"

for SEED in 0 1 2 3 4 5 6 7 8 9; do
    echo "=== Running seed $SEED ===" | tee -a /tmp/v2_run.log
    bash /tmp/run_single.sh $SEED

    LOG=$OUT/v2_s${SEED}.log

    if grep -q "FAST EXIT" $LOG; then
        ERR=$(grep "FAST EXIT" $LOG | tail -1 | sed "s/.*map_dist=\([0-9.]*\).*/\1/")
        STP=$(grep "FAST EXIT" $LOG | tail -1 | sed "s/.*step=\([0-9]*\).*/\1/")
        echo "ED_Bayes_V2,2,4-1_fast,$SEED,$ERR,1,$STP,fast_exit" >> $OUT/results_v2.csv
        echo "  FAST EXIT: error=${ERR}m steps=${STP}" | tee -a /tmp/v2_run.log
    elif grep -q "OPGSL-SDNBV RESULT" $LOG; then
        MAP_LINE=$(grep "OPGSL-SDNBV RESULT" $LOG | head -1)
        MX=$(echo "$MAP_LINE" | sed "s/.*MAP=(\([^,]*\),.*/\1/")
        MY=$(echo "$MAP_LINE" | sed "s/.*MAP=([^,]*,\([^,]*\),.*/\1/")
        STP=$(echo "$MAP_LINE" | sed "s/.*steps=\([0-9]*\).*/\1/")
        ERR=$(python3 -c "import math; print(round(math.sqrt(($MX - $SRC_X)**2 + ($MY - $SRC_Y)**2),3))")
        LOC=$(python3 -c "print(1 if float(\"$ERR\") < 2.0 else 0)")
        echo "ED_Bayes_V2,2,4-1_fast,$SEED,$ERR,$LOC,$STP,timeout" >> $OUT/results_v2.csv
        echo "  RESULT: MAP=($MX,$MY) error=${ERR}m steps=${STP}" | tee -a /tmp/v2_run.log
    else
        echo "ED_Bayes_V2,2,4-1_fast,$SEED,99.0,0,0,failed" >> $OUT/results_v2.csv
        echo "  FAILED" | tee -a /tmp/v2_run.log
    fi
done

echo "=== ALL DONE ===" | tee -a /tmp/v2_run.log
cat $OUT/results_v2.csv
