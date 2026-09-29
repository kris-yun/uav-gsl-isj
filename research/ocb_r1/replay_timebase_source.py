#!/usr/bin/env python3
"""Read-only numerical replay of the two documented GADEN writer clocks."""
from __future__ import annotations

import bisect
import csv
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "e2c_r1"))
from audit_e2_timebase import reconstruct  # noqa: E402

OUT = ROOT / "evidence" / "ocb_r1" / "timebase"
TARGETS = tuple(range(100, 551, 50))


def old_records() -> list[dict]:
    # 2021 ROS1 CFilamentSimulator: double sim_time, floor quotient writer,
    # fixed numSteps=floor(max_sim_time/time_step), then double clock update.
    t = 0.0
    last_saved_step = -1
    last_wind_time = -2.0
    next_wind = 0
    active_wind = -1
    result = []
    for step in range(int(1000.0 / 0.1)):
        if t - last_wind_time >= 1.0:
            last_wind_time = t
            active_wind = next_wind
            next_wind = 1 if next_wind >= 10 else next_wind + 1
        quotient = int(t // 0.5)
        if t >= 0.0 and quotient != last_saved_step:
            result.append(dict(record_id=len(result), integration_step=step,
                               clock_before_s=t, quotient=quotient,
                               active_wind_index=active_wind))
            last_saved_step += 1
        t += 0.1
    return result


def write_tsv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t",
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    old = old_records()
    new = reconstruct(1000.0)
    assert len(old) == 2000, len(old)
    assert len(new) == 1803, len(new)
    assert all(r["quotient"] == r["record_id"] for r in old)

    new_times = [r["clock_before_s"] for r in new]
    mapping = []
    for i in TARGETS:
        old_t = old[i]["clock_before_s"]
        at = bisect.bisect_left(new_times, old_t)
        candidates = [j for j in (at - 1, at) if 0 <= j < len(new)]
        j = min(candidates, key=lambda n: (abs(new_times[n] - old_t), n))
        err = abs(new_times[j] - old_t)
        mapping.append(dict(original_record_id=i,
                            historical_physical_time_s=format(old_t, ".17g"),
                            new_exact_record_id=j if err == 0 else "NONE",
                            new_nearest_record_id=j,
                            new_physical_time_s=format(new_times[j], ".17g"),
                            time_error_seconds=format(err, ".17g"),
                            exact_match="YES" if err == 0 else "NO",
                            old_integration_step=old[i]["integration_step"],
                            new_integration_step=new[j]["integration_step"],
                            old_wind_index=old[i]["active_wind_index"],
                            new_wind_index=new[j]["active_wind_index"],
                            wind_index_match="YES" if old[i]["active_wind_index"] == new[j]["active_wind_index"] else "NO"))
    write_tsv(OUT / "RECORD_MAPPING_10.tsv", list(mapping[0]), mapping)

    trace = []
    for label, records, ids in (
        ("OLD", old, sorted(set(range(5)) | set(range(998, 1003)) | set(range(1995, 2000)) | set(TARGETS))),
        ("NEW", new, sorted(set(range(5)) | set(range(899, 904)) | set(range(1798, 1803)) | set(TARGETS))),
    ):
        for i in ids:
            row = records[i]
            trace.append(dict(version=label, record_id=i,
                              integration_step=row["integration_step"],
                              clock_before_s=format(row["clock_before_s"], ".17g"),
                              quotient=row.get("quotient", "NA")))
    write_tsv(OUT / "CLOCK_TRACE_SAMPLES.tsv", list(trace[0]), trace)
    with (OUT / "HISTORICAL_FILE_HEADERS.tsv").open(encoding="utf-8", newline="") as stream:
        headers = list(csv.DictReader(stream, delimiter="\t"))
    historic = []
    wind_matches = 0
    for h in headers:
        i = int(h["record_id"])
        if int(h["embedded_wind_index"]) == old[i]["active_wind_index"]:
            wind_matches += 1
        historic.append(dict(record_id=i, filename=h["filename"],
                             embedded_time_if_any="NONE",
                             derived_time_s=format(old[i]["clock_before_s"], ".17g"),
                             embedded_wind_index=h["embedded_wind_index"],
                             derived_wind_index=old[i]["active_wind_index"],
                             evidence="2021 source double-clock replay + 2022 zlib version-1 header",
                             notes="conditional on unlocated original executable; mtime is not simulation time"))
    write_tsv(OUT / "HISTORICAL_RECORD_TIMES.tsv", list(historic[0]), historic)
    errs = [float(r["time_error_seconds"]) for r in mapping]
    result = dict(old_count=len(old), old_first_s=old[0]["clock_before_s"],
                  old_last_s=old[-1]["clock_before_s"],
                  old_last_step=old[-1]["integration_step"],
                  new_count=len(new), new_first_s=new[0]["clock_before_s"],
                  new_last_s=new[-1]["clock_before_s"],
                  new_last_step=new[-1]["integration_step"],
                  targets=list(TARGETS),
                  exact_matches=sum(r["exact_match"] == "YES" for r in mapping),
                  max_error_s=max(errs), mean_error_s=statistics.mean(errs),
                  median_error_s=statistics.median(errs),
                  no_simulator_invoked=True)
    result["historical_header_wind_matches"] = wind_matches
    result["historical_header_wind_inspected"] = len(headers)
    result["target_wind_index_matches"] = sum(r["wind_index_match"] == "YES" for r in mapping)
    result.update(old_interrecord_min_s=min(old[i+1]["clock_before_s"]-old[i]["clock_before_s"] for i in range(len(old)-1)),
                  old_interrecord_max_s=max(old[i+1]["clock_before_s"]-old[i]["clock_before_s"] for i in range(len(old)-1)),
                  new_interrecord_min_s=min(new_times[i+1]-new_times[i] for i in range(len(new)-1)),
                  new_interrecord_max_s=max(new_times[i+1]-new_times[i] for i in range(len(new)-1)))
    (OUT / "CLOCK_REPLAY_SUMMARY.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    decision = dict(decision="TIMEBASE_APPROXIMATE_HOLD",
                    old_binary_provenance="SOURCE_CANDIDATE_BEHAVIORALLY_CORROBORATED_EXECUTABLE_NOT_LOCATED",
                    ten_exact_clock_matches=result["exact_matches"],
                    ten_wind_index_matches=result["target_wind_index_matches"],
                    nearest_clock_error_max_s=result["max_error_s"],
                    nearest_clock_error_median_s=result["median_error_s"],
                    nearest_clock_error_mean_s=result["mean_error_s"],
                    save_cadence_physics_independent="PASS_FOR_FROZEN_PRECALCULATE_FALSE",
                    ocb_r1_run_status="OCB_R1_RUN_HOLD",
                    simulator_runs_this_stage=0)
    (OUT / "TIMEBASE_DECISION.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
