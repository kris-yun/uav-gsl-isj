"""Independently check retained P0 evidence and report the input-gate STOP.

This program deliberately performs no observation-map or candidate scoring.
Missing event inputs must never be replaced by fitting archived terminal maps.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re

LABEL = "TS_P3T_H0_INVALID_STOP"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def finalize(root):
    audit = json.loads((root / "P0_ARCHIVE_AUDIT.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader((root / "P0_VERIFIED_INPUTS.tsv").open(encoding="utf-8"), delimiter="\t"))
    checked = []
    for row in rows:
        if row["path"] == "freeze/exact_b24_source.tar.gz":
            continue
        content = (root / "retained_inputs" / row["path"]).read_bytes()
        checked.append(digest(content) == row["archive_sha256"] == row["manifest_sha256"] == row["extracted_sha256"])
    sources = {}
    for name, expected in audit["frozen_source_sha256"].items():
        path = root / "retained_inputs/frozen_code" / name
        assert digest(path.read_bytes()) == expected
        sources[name] = path.read_text(encoding="utf-8")
    stop = next(s for n, s in sources.items() if n.endswith("StopAndMeasureState.cpp"))
    pmfs = next(s for n, s in sources.items() if n.endswith("/PMFS.cpp"))
    lib = next(s for n, s in sources.items() if n.endswith("PMFSLib.cpp"))
    code_checks = {
        "trace_path_defaults_empty": 'getParam<std::string>("measurement_trace_file", "")' in stop,
        "sample_trace_path_defaults_empty": 'getParam<std::string>("continuous_measurement_samples_file", "")' in stop,
        "log_wind_uses_two_significant_digits": 'avg_windSpeed={:.2}' in stop and 'avg_wind_dir={:.2}' in stop,
        "trace_requires_nonempty_path": 'if (!filepath.empty())' in stop,
        "pcaci_event_record_requires_tadm": re.search(r'if \(tadmEnabled && .*?recordPCACIEvent', pmfs, re.S) is not None,
        "measurement_map_uses_wind_speed": 'settings.kernelStretchConstant * windSpeed' in lib,
        "measurement_map_uses_wind_direction": 'downwindDirection' in lib,
        "logodds_and_omega_updated_each_event": 'cell.logOdds +=' in lib and 'cell.omega +=' in lib,
        "callback_vectors_are_state_gated": 'getCurrentState() != this' in stop,
    }
    assert all(code_checks.values()), code_checks
    case_checks, parity, memory, case_table = {}, {}, {}, []
    for case, record in audit["cases"].items():
        folder = root / "retained_inputs/native" / case
        manifest = json.loads((folder / "runtime_manifest.json").read_text())
        runtime_files = list((folder / "resolved_runtime").glob("launch_params_*"))
        runtime = next(f.read_text() for f in runtime_files if "pfdi_mode:" in f.read_text())
        files = [r["archive_relative_path"] for r in csv.DictReader((root / "P0_ARCHIVE_INVENTORY.tsv").open(), delimiter="\t") if r["case"] == case]
        event_files = [n for n in files if re.search(r'event|measurement[_-](trace|samples)|continuous_measurement', Path(n).name, re.I)]
        case_checks[case] = {
            "native_mode_off": manifest["pfdi_mode"] == "off",
            "tadm_disabled": re.search(r'^\s*tadm_enabled:\s*false\s*$', runtime, re.M) is not None,
            "measurement_trace_parameter_absent": re.search(r'^\s*measurement_trace_file:', runtime, re.M) is None,
            "continuous_trace_parameter_absent": re.search(r'^\s*continuous_measurement_samples_file:', runtime, re.M) is None,
            "no_event_archive_member": not event_files,
        }
        assert all(case_checks[case].values()), case_checks[case]
        last = record["source_updates"][-1]
        map_path = folder / "context_bank" / f'source_update_{last["id"]:04d}' / "measured_hit_probability.csv"
        map_rows = list(csv.DictReader(map_path.open()))
        occupancy = [r["occupancy"] for r in map_rows]
        parity[case] = {
            "status": "NOT_COMPUTABLE_MISSING_EXACT_EVENTS", "pass": False,
            "terminal_time_s": record["terminal_time"],
            "archived_terminal_map_sha256": digest(map_path.read_bytes()),
            "archived_map_rows": len(map_rows), "archived_free_cells": occupancy.count("Free"),
            "archived_occupancy_vector_sha256": digest("\n".join(occupancy).encode()),
            "required_max_abs_error": 1e-10,
            "logOdds_max_abs_error": None, "omega_max_abs_error": None, "confidence_max_abs_error": None,
            "reconstructed_support_equal": None, "reconstructed_source_update_time_equal": None,
            "reconstruction_attempted": False,
            "reason": "The exact completed-block input stream is absent/ambiguous. Snapshot hash equality is not reconstruction parity.",
        }
        memory[case] = {
            "status": "NOT_RUN_P0_FAILED",
            "O_full_exact_event_count": None,
            "logged_completed_block_average_lines_before_terminal": record["logged_average_records_before_terminal_update"],
            "O_40_bounds_s": record["O40_requested_bounds"], "O_40_duration_s": 40,
            "O_update_bounds_s": record["Oupdate_requested_bounds"], "O_update_duration_s": round(record["Oupdate_duration"], 10),
            "O_40_exact_event_count": None, "O_update_exact_event_count": None,
            "older_than_40s_omega_fraction": None, "older_than_40s_confidence_fraction": None,
            "P3_truth_scores_ranks_margins": None, "G3_truth_scores_ranks_margins": None,
        }
        case_table.append([case, record["terminal_time"], 40, round(record["Oupdate_duration"], 10), "", "", "", "NOT_RUN_P0_FAILED"])
    independent = {
        "audit_scope": "Independent local check of retained historical inputs, runtime/source logging gates, and archive inventories; H0 reconstruction/scoring not possible.",
        "retained_input_files_rehashed": len(checked), "retained_input_hashes_all_match": all(checked),
        "source_files_rehashed": len(sources), "code_checks": code_checks, "case_checks": case_checks,
        "archive_identity_pass": audit["archive_sidecar_match"],
        "P0_event_sufficiency_pass": False, "H0_reconstruction_and_score_audit": "NOT_RUN_MISSING_INPUTS",
        "conclusion": LABEL,
    }
    assert all(checked) and audit["archive_sidecar_match"] and audit["all_selected_manifest_hashes_match"] and audit["all_selected_extracted_bytes_match"]
    save(root / "INDEPENDENT_H0_AUDIT.json", independent)
    save(root / "P0_TERMINAL_MAP_PARITY.json", {"P0_pass": False, "status": "MISSING_EXACT_EVENT_STREAM", "cases": parity})
    save(root / "H0_OBSERVATION_MEMORY.json", {"status": "NOT_RUN_P0_FAILED", "cases": memory})
    result = {
        "decision": LABEL, "stage": "P0", "historical_archive_identity_pass": True,
        "P0_terminal_map_reconstruction_pass": False,
        "reason": "Four exact R1-parent cases have no retained completed-block event stream; rounded traces/logs do not uniquely encode consumed block inputs.",
        "science_evaluated": False, "historical_D0_STOP_preserved": True,
        "source_ownership_loaded_for_evaluation": False,
        "candidate_scores_computed": 0, "observation_maps_reconstructed": 0,
        "execution_counts": audit["execution"],
        "next_stage_authorized_or_started": False,
        "cases": memory,
        "interpretation": "Input-provenance stop, not a negative result for temporal closure or persistent transport state.",
    }
    save(root / "H0_RESULT.json", result)
    with (root / "H0_CASES.tsv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["case", "terminal_time_s", "O40_requested_duration_s", "Oupdate_requested_duration_s", "O40_event_count", "Oupdate_event_count", "older40_omega_fraction", "status"])
        w.writerows(case_table)
    (root / "H0_CANDIDATE_SCORES.tsv").write_text("case\tarm\tobservation_memory\tcandidate_id\tlog_score\n", encoding="utf-8")
    (root / "P0_PROVENANCE.md").write_text(f'''# H0 P0 historical-event provenance

## Verified identity

- Branch: `research/ts-p3t-h0-temporal-closure-20261001`.
- Frozen handoff base: `b51aaa979e1e303fbb1457ba87244f21574a6d4c`.
- Authoritative archive: `{audit['archive_path']}`.
- Archive bytes: {audit['archive_bytes']}.
- Archive SHA256: `{audit['archive_sha256']}`; exact match to its historical sidecar.
- All {len(rows)} selected artifacts match the archive manifest and extracted VM copy.
- {len(checked)} retained files and {len(sources)} frozen source files were independently rehashed locally.
- No HCMC, recovery run, or later repeated run was substituted.

## Missing completed-block inputs

All four cases ran `pfdi_mode=off`, `tadm_enabled=false`. Their resolved parameters contain no `measurement_trace_file` or `continuous_measurement_samples_file`. The archive inventories contain no measurement/event export for these cases.

The exact source archive verifies two independent disabled logging paths:

1. `Common/States/StopAndMeasureState.cpp`: measurement and sample trace paths default to the empty string; output requires a nonempty path. Console averages use `{{:.2}}`, i.e. two significant digits, not full float precision.
2. `PMFS/PMFS.cpp`: `recordPCACIEvent` requires `tadmEnabled` and a supported non-off mode. Neither condition is satisfied here.

The GSL log does retain 128 completed-block average lines before the terminal source update in each case. These establish that measurements occurred; they are not a full-precision event stream. The log timestamp is wall time, while the requested windows use simulator time. Source-update timing is retained only at the five source updates.

`sensor_trace.csv` and `wind_trace.csv` record simulator publication steps, with six decimal places for sensor/wind values and four for pose. They omit callback-to-measurement-block membership and the exact transformed/circular-averaged wind consumed by Native. State gating, independent gas/wind callbacks, and timer boundaries are part of the archived `StopAndMeasureState` code. Ten samples per block alone does not uniquely recover those inputs.

## Why rounding matters for this contract

Native `EstimateHitProbabilities` depends on wind speed and direction, as well as hit and robot grid cell. `sigma_y = 0.5 + 1.5 * windSpeed` and the kernel rotation depends on downwind direction. For example the log display `0.027` permits multiple wind speeds at two significant digits; it cannot establish an input error small enough for `1e-10` logOdds parity. The six-decimal publication trace supplies more information, but does not provide the missing block membership or full-precision callback values.

No map was reconstructed using guessed windows, rounded log means, or parameters fitted to the saved terminal map. Copying the saved map and reporting zero difference would be a circular parity check.

## Gate result

`{LABEL}`.

The archived terminal maps, masks, times and hashes are available. Reconstruction parity is **not computable**, so all max-absolute-error values are null, not zero. This is an input sufficiency failure; no measured numerical mismatch was claimed.

O40 and Oupdate bounds can be reported from source-update timing. Their exact event counts, memory-age fractions, maps, candidate scores, truth ranks and margins remain unavailable. The empty score TSV is intentionally header-only.

## Execution boundary

New GADEN=0; new candidate forward=0; training=0; H03 observation content=0; closed loop=0; truth scientific evaluation=0. Existing ROS2 src/build/install and historical archives were not changed. H1 and subsequent methods were not started.
''', encoding="utf-8")
    (root / "H0_DECISION.md").write_text(f'''# H0 decision

**`{LABEL}`**

P0 verified the exact historical archive and 61 selected input hashes, but could not recover the full-precision completed-measurement event stream for any of the four R1 cases. The requested `1e-10` terminal map reconstruction parity therefore cannot be established.

Following the frozen handoff, H0 stops before O40/Oupdate reconstruction and scientific scoring. No candidate rankings or truth evidence were recomputed. The historical P3T D0 STOP is unchanged.

This decision does not reject the temporal-closure hypothesis or establish a persistent world model. It establishes that this historical asset cannot support the preregistered exact replay. No replacement run or new simulator execution was performed.

The independent audit validates input hashes and the disabled logging paths. It explicitly marks map/scoring replication as not run; it does not manufacture a parity PASS.
''', encoding="utf-8")
    print(json.dumps({"decision": LABEL, "verified_retained_files": len(checked), "result_sha256": digest((root / "H0_RESULT.json").read_bytes())}, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("evidence_root", type=Path)
    finalize(p.parse_args().evidence_root)
