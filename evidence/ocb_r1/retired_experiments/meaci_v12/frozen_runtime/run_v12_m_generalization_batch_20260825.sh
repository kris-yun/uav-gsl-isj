#!/usr/bin/env bash
set -Eeuo pipefail

freeze=/home/zyc/meaci_v12_m_freeze_20260825
case_runner="$freeze/run_v12_qualification_case_20260825.sh"
expected_case_runner=c8c3f3c62a539b721c5e9716b4c25648193428579a19fb81865dcb920e3f319f
[[ "$(sha256sum "$case_runner" | awk '{print $1}')" == "$expected_case_runner" ]]
[[ ! -e /home/zyc/meaci_v12_generalization_20260825_r1 ]]

run_case() {
  local house="$1" seed="$2" arm="$3" domain="$4" bank="$5" bank_sha="$6"
  printf 'FROZEN_CASE_START house=%s seed=%s arm=%s domain=%s\n' "$house" "$seed" "$arm" "$domain"
  if [[ "$arm" == on ]]; then
    HOUSE="$house" SEED="$seed" ARM="$arm" DOMAIN_ID="$domain" \
      freeze_bank_path="$bank" freeze_bank_sha256="$bank_sha" "$case_runner"
  else
    HOUSE="$house" SEED="$seed" ARM="$arm" DOMAIN_ID="$domain" "$case_runner"
  fi
  printf 'FROZEN_CASE_PASS house=%s seed=%s arm=%s domain=%s\n' "$house" "$seed" "$arm" "$domain"
}

run_case House01 418310734 off 211 /dev/null unused
run_case House01 418310734 on  212 /home/zyc/meaci_v12_banks_20260825/House01/v12_response_bank.bin a6f9336f4440aafeb9c0bb75246a9fb941497ec8fab5ceb83fac2f0b7bcdddb9
run_case House02 661532441 on  213 /home/zyc/meaci_v12_banks_20260825/House02/v12_response_bank.bin c5b768a5b8123d0736048c601fe6534293b12aaed3e5e84140d9e527c83bdf6e
run_case House02 661532441 off 214 /dev/null unused
run_case House03 538848658 off 215 /dev/null unused
run_case House03 538848658 on  216 /home/zyc/meaci_v12_banks_20260825/House03/v12_response_bank.bin bd0a5472ac11a259d7638e7fe19d8b6776f8d93391c6f19655eb80d859930b3b

printf 'V12_M_ALL_SIX_RUNTIME_INTEGRITY_PASS\n'
