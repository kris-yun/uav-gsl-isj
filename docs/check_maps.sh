for s in 0 1 2 3 4 5 6 7 8 9; do
  echo -n "H02_s${s}: "
  grep "RESULT" /tmp/cp_sbd_exp_clean/Clean_House02_s${s}.log 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | tail -1
done
echo "---"
for s in 0 1 2 3 4 5 6 7 8 9; do
  echo -n "H03_s${s}: "
  grep "RESULT" /tmp/cp_sbd_exp_clean/Clean_House03_s${s}.log 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | tail -1
done
