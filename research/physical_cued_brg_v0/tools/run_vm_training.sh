#!/usr/bin/env bash
set -Ee -o pipefail
export PATH=/home/zyc/brg_closedloop_20260927/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export MARKED_REVIEW=/home/zyc/marked_encounter_pmfs_d0_20260927/MARKED_ENCOUNTER_PMFS_D0_REVIEW_20260927.zip
cd /home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927
bash tools/start_open.sh
