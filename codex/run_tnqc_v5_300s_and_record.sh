#!/usr/bin/env bash
set -Eeuo pipefail

EXPECTED_BRANCH="codex/tnqc-v5-300s-offline-20260921"
FROZEN_ANCESTOR="9d3d21e7a7fdea0946e29d313ea9073ce63d2bab"
ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "${ROOT_DIR}"

RESULT_DIR="${ROOT_DIR}/codex_results/tnqc_v5_300s_20260921"
RUN_ROOT="/dev/shm/tnqc_v5_codex_300s_20260921"
BUILD_ROOT="/dev/shm/tnqc_v5_codex_build_20260921"
LAUNCH_FILE="${LAUNCH_FILE:-/dev/shm/meaci_online_20260824/launch/vgr_gsl_pmfs_pfdi.launch.py}"
MANIFEST="evidence/TNQC_V5_IMPLEMENTATION_MANIFEST_20260921.json"
RUNNER="reference/run_tnqc_vgr_offline_gate_20260920.sh"
VERIFY="reference/verify_tnqc_v5_manifest.py"

branch="$(git branch --show-current)"
if [[ "${branch}" != "${EXPECTED_BRANCH}" ]]; then
  echo "ERROR: wrong branch: ${branch}; expected ${EXPECTED_BRANCH}" >&2
  exit 90
fi
if ! git merge-base --is-ancestor "${FROZEN_ANCESTOR}" HEAD; then
  echo "ERROR: frozen checkpoint is not an ancestor of HEAD" >&2
  exit 91
fi

# The execution branch may contain this recorder/runbook, but execution starts
# from a clean checkout. Refuse arbitrary pre-run edits.
if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
  echo "ERROR: working tree is not clean before the run" >&2
  git status --short --untracked-files=all >&2
  exit 92
fi

rm -rf "${RESULT_DIR}" "${RUN_ROOT}" "${BUILD_ROOT}"
mkdir -p "${RESULT_DIR}/preflight" "${RESULT_DIR}/cases"

date -u +%Y-%m-%dT%H:%M:%SZ > "${RESULT_DIR}/preflight/start_utc.txt"
git rev-parse HEAD > "${RESULT_DIR}/preflight/git_head.txt"
git rev-parse HEAD:ros2_package > "${RESULT_DIR}/preflight/ros2_package_tree.txt"
git status --porcelain --untracked-files=all > "${RESULT_DIR}/preflight/git_status_before.txt"
git log -1 --format=fuller > "${RESULT_DIR}/preflight/git_log_head.txt"
uname -a > "${RESULT_DIR}/preflight/uname.txt"
{
  echo "python=$(python3 --version 2>&1)"
  echo "g++=$(g++ --version | head -n 1)"
  echo "git=$(git --version)"
  echo "branch=${branch}"
  echo "frozen_ancestor=${FROZEN_ANCESTOR}"
  echo "launch_file=${LAUNCH_FILE}"
} > "${RESULT_DIR}/preflight/environment.txt"

set +e
python3 "${VERIFY}" --root "${ROOT_DIR}" --manifest "${MANIFEST}"   > "${RESULT_DIR}/preflight/manifest_verify.log" 2>&1
verify_rc=$?
set -e
echo "${verify_rc}" > "${RESULT_DIR}/preflight/manifest_verify_rc.txt"
cat "${RESULT_DIR}/preflight/manifest_verify.log"
if [[ "${verify_rc}" -ne 0 ]]; then
  echo "ERROR: manifest verification failed; do not run House truth" >&2
  exit 93
fi

for p in   "${LAUNCH_FILE}"   "/mnt/hgfs/workspace/GADEN_files/scenarios/House01"   "/mnt/hgfs/workspace/GADEN_files/scenarios/House02"   "/mnt/hgfs/workspace/GADEN_files/scenarios/House03"
do
  if [[ ! -e "${p}" ]]; then
    echo "ERROR: required VM path missing: ${p}" >&2
    exit 94
  fi
done

sha256sum "${LAUNCH_FILE}" > "${RESULT_DIR}/preflight/external_launch_sha256.txt"

echo "=== TNQC V5 frozen 300-s run starts ==="
set +e
RUN_ROOT="${RUN_ROOT}" TNQC_BUILD_ROOT="${BUILD_ROOT}" LAUNCH_FILE="${LAUNCH_FILE}" bash "${RUNNER}" 2>&1 | tee "${RESULT_DIR}/full_run.log"
runner_rc=${PIPESTATUS[0]}
set -e

echo "${runner_rc}" > "${RESULT_DIR}/authoritative_runner_exit_code.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "${RESULT_DIR}/end_utc.txt"

for f in   tnqc_build_provenance.json   tnqc_batch_provenance.json   tnqc_vgr_300s_offline_gate.json   frozen_vgr_launch_overlay.py
do
  if [[ -f "${RUN_ROOT}/${f}" ]]; then
    cp -f "${RUN_ROOT}/${f}" "${RESULT_DIR}/${f}"
  fi
done

for house in House01 House02 House03; do
  for seed in 0 1; do
    name="${house}_seed${seed}"
    src="${RUN_ROOT}/${house}_seed${seed}_off_off"
    dst="${RESULT_DIR}/cases/${name}"
    mkdir -p "${dst}"
    for f in       runtime_manifest.json       run_status.json       tnqc_fixed_trajectory_evaluation.json
    do
      [[ -f "${src}/${f}" ]] && cp -f "${src}/${f}" "${dst}/${f}"
    done
    if [[ -f "${src}/launch.log" ]]; then
      grep -F 'RESULT IS:' "${src}/launch.log" > "${dst}/result_lines.txt" || true
      tail -n 250 "${src}/launch.log" > "${dst}/launch_tail_250.txt" || true
    fi
    if [[ -f "${src}/context_bank/source_update_timing.csv" ]]; then
      cp -f "${src}/context_bank/source_update_timing.csv"         "${dst}/source_update_timing.csv"
    fi
  done
done

# The authoritative runner must never rewrite tracked repository files.
# Untracked evidence under codex_results is expected; tracked changes are not.
git diff --name-only > "${RESULT_DIR}/preflight/tracked_changes_after_run.txt"
postrun_integrity_rc=0
if [[ -s "${RESULT_DIR}/preflight/tracked_changes_after_run.txt" ]]; then
  echo "ERROR: tracked repository files changed during execution" >&2
  cat "${RESULT_DIR}/preflight/tracked_changes_after_run.txt" >&2
  git diff > "${RESULT_DIR}/preflight/tracked_changes_after_run.patch"
  postrun_integrity_rc=95
fi

python3 - "${RESULT_DIR}" "${runner_rc}" <<'PY'
import json
import math
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
runner_rc = int(sys.argv[2])
aggregate_path = root / "tnqc_vgr_300s_offline_gate.json"

summary = {
    "contract": "CODEX_TNQC_V5_300S_EXECUTION_RECORD_V1",
    "runner_exit_code": runner_rc,
    "aggregate_present": aggregate_path.is_file(),
    "cases": [],
}

if aggregate_path.is_file():
    agg = json.loads(aggregate_path.read_text(encoding="utf-8"))
    summary["aggregate"] = {
        k: agg.get(k) for k in [
            "contract", "valid", "invalid_reason", "go_for_closed_loop",
            "verdict", "pooled_native_error_m",
            "pooled_tnqc_fused_error_m",
            "pooled_improvement_fraction", "improved_pairs",
            "worst_pair_degradation_fraction",
            "false_confident_collapse_cases",
        ]
    }

for house in ("House01", "House02", "House03"):
    for seed in (0, 1):
        p = root / "cases" / f"{house}_seed{seed}" /             "tnqc_fixed_trajectory_evaluation.json"
        row = {"house": house, "seed": seed, "evaluation_present": p.is_file()}
        if p.is_file():
            e = json.loads(p.read_text(encoding="utf-8"))
            gate = e.get("tnqc_candidate_bank_gate", {})
            endpoint = e.get("endpoint_evaluator", {})
            native_audit = e.get("native_reconstruction_audit", {})
            cpp_audit = e.get("native_cpp_endpoint_audit", {})
            tie = e.get("endpoint_tie_diagnostics", {})
            row.update({
                "replay_contract": e.get("contract"),
                "valid_for_gate": e.get("valid_for_gate"),
                "candidate_gate_scope": e.get("candidate_gate_scope"),
                "native_reconstruction_pass": native_audit.get("pass"),
                "native_cpp_endpoint_pass": cpp_audit.get("pass"),
                "endpoint_engine": endpoint.get("engine"),
                "endpoint_engine_integrity_pass":
                    endpoint.get("engine_integrity_pass"),
                "native_error_m":
                    e.get("native_exported", {}).get("pmfs_top5_error_m"),
                "tnqc_fused_error_m":
                    e.get("tnqc_fused", {}).get("pmfs_top5_error_m"),
                "fused_improvement_fraction_vs_native":
                    e.get("fused_improvement_fraction_vs_native"),
                "selected_source_update_id":
                    e.get("selected_source_update_id"),
                "selected_source_update_sim_time":
                    e.get("selected_source_update_sim_time"),
                "budget_to_last_update_gap_s":
                    e.get("budget_to_last_update_gap_s"),
                "total_evaluated_candidate_count":
                    e.get("total_evaluated_candidate_count"),
                "final_leaf_candidate_count":
                    e.get("final_leaf_candidate_count"),
                "gate_strength": gate.get("strength"),
                "gate_conditional_concordance": gate.get("concordance"),
                "gate_informative_coverage":
                    gate.get("informative_coverage"),
                "gate_reference_pair_weight":
                    gate.get("reference_pair_weight"),
                "gate_informative_pair_weight":
                    gate.get("pair_weight"),
                "native_cpp_minus_python_error_m":
                    tie.get("native_cpp_minus_python_error_m"),
                "fused_cpp_minus_python_error_m":
                    tie.get("fused_cpp_minus_python_error_m"),
            })
        summary["cases"].append(row)

(root / "results_summary.json").write_text(
    json.dumps(summary, indent=2, sort_keys=True) + "\n",
    encoding="utf-8")

lines = [
    "# TNQC V5 300-s Codex execution summary",
    "",
    f"- Runner exit code: `{runner_rc}`",
    f"- Aggregate present: `{summary['aggregate_present']}`",
]
agg = summary.get("aggregate")
if agg:
    for key in [
        "contract", "valid", "invalid_reason", "go_for_closed_loop",
        "verdict", "pooled_native_error_m", "pooled_tnqc_fused_error_m",
        "pooled_improvement_fraction", "improved_pairs",
        "worst_pair_degradation_fraction",
        "false_confident_collapse_cases",
    ]:
        lines.append(f"- {key}: `{agg.get(key)}`")

lines += [
    "",
    "## Six cases",
    "",
    "| Case | Valid | Native m | TNQC fused m | Improvement | Endpoint | Recon | C++ anchor | Coverage | g | Last update s |",
    "|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|",
]
for row in summary["cases"]:
    case = f"{row['house']}/seed{row['seed']}"
    def v(k):
        x = row.get(k)
        if isinstance(x, float):
            return f"{x:.6g}"
        return str(x)
    lines.append(
        f"| {case} | {v('valid_for_gate')} | {v('native_error_m')} | "
        f"{v('tnqc_fused_error_m')} | "
        f"{v('fused_improvement_fraction_vs_native')} | "
        f"{v('endpoint_engine')} | {v('native_reconstruction_pass')} | "
        f"{v('native_cpp_endpoint_pass')} | "
        f"{v('gate_informative_coverage')} | {v('gate_strength')} | "
        f"{v('selected_source_update_sim_time')} |"
    )

lines += [
    "",
    "## Interpretation rule",
    "",
    "Do not tune V5 after reading this batch. HOLD is a result. INVALID is an "
    "execution/integrity state that must be diagnosed without changing the "
    "frozen method.",
]
(root / "RESULTS_SUMMARY.md").write_text(
    "\n".join(lines) + "\n", encoding="utf-8")
PY

git status --porcelain --untracked-files=all > "${RESULT_DIR}/git_status_after.txt"

final_rc="${runner_rc}"
if [[ "${postrun_integrity_rc}" -ne 0 ]]; then
  final_rc="${postrun_integrity_rc}"
fi
echo "${final_rc}" > "${RESULT_DIR}/recorder_exit_code.txt"

(
  cd "${RESULT_DIR}"
  find . -type f ! -name SHA256SUMS.txt -print0 \
    | sort -z \
    | xargs -0 sha256sum > SHA256SUMS.txt
)

echo "=== Recorder completed: runner_rc=${runner_rc} final_rc=${final_rc} ==="
echo "Evidence directory: ${RESULT_DIR}"
echo "Review: ${RESULT_DIR}/RESULTS_SUMMARY.md"

# Preserve the scientific runner status unless the recorder detects a
# repository-integrity violation:
# 0 = GO; 10 = HOLD; other = execution/infrastructure/integrity failure.
exit "${final_rc}"
