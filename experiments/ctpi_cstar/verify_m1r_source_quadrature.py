"""Independently recompute the fixed-source treatment's exported score atoms.

Usage (the persistence mode is mandatory because it is not in the CSV):
  python verify_m1r_source_quadrature.py --context-dir DIR \
    --persistence historical_rolling --native-mantissa-bits 64 --output audit.json
  python verify_m1r_source_quadrature.py --self-test

mpmath is used for probabilities, log likelihoods, mixtures, and CSV numbers;
likelihoods never pass through a binary64 float. Every exported U/K/event row
is consumed, including rows preceding the scored window. This verifies the
logged scoring arithmetic, not that PF generated a correct response dictionary,
nor the construction of the initial candidate context: refinement-level identity
is absent from these CSVs. No source truth, raw bank, or simulator is accessed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import tempfile

import mpmath as mp


EVENT_FILE = "contrastive_source_point_event_attribution.csv"
SCORE_FILE = "source_point_component_scores.csv"
CONTEXT = "source_U_mean_then_candidate_mean_within_transport_K"
SEMANTICS = "four_fixed_rectangle_points_finite_approximation_not_exact_region_integral"
EVENT_FIELDS = ("run_uuid source_update_id candidate_id candidate_x candidate_y member_index "
                "event_index block_id sim_time_s cell_index observed_hit concentration threshold "
                "legacy_hit_probability aggregate_raw_exposure iterations_to_record delta_time_s "
                "context_value context_centered_log_odds observation_operator source_point_index "
                "source_point_weight event_window_start source_quadrature_context").split()
SCORE_FIELDS = ("run_uuid source_update_id candidate_id origin_i origin_j size_i size_j "
                "source_point_index source_x source_y source_weight transport_members "
                "component_likelihood weighted_component_likelihood region_mixture_likelihood "
                "legacy_forward_calls fixed_point_forward_calls source_dim quadrature_semantics").split()
EPS = mp.mpf("0.0001")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value):
    result = mp.mpf(value)
    require(mp.isfinite(result), "NONFINITE_NUMBER")
    return result


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def rows(path, fields):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames is not None and set(fields) <= set(reader.fieldnames),
                f"MISSING_COLUMNS:{path.name}")
        for row in reader:
            require(None not in row and all(row.get(field) not in (None, "") for field in fields),
                    f"INCOMPLETE_ROW:{path.name}:{reader.line_num}")
            yield row


def clip(value):
    return min(1 - EPS, max(EPS, value))


def logit(value):
    value = clip(value)
    return mp.log(value) - mp.log1p(-value)


def logmean(log_values):
    largest = max(log_values)
    return largest + mp.log(mp.fsum(mp.exp(v - largest) for v in log_values) / len(log_values))


def persistence_logit(threshold, previous):
    # Recompute the intended law at high precision. The native overload of
    # log1p(double) rounds before assignment to long double; the disclosed
    # numerical budget below includes that binary64 stage.
    return logit(mp.erfc((mp.log1p(threshold) - mp.log1p(previous)) / mp.sqrt(2)) / 2)


def factor_log(source_probability, context_logit, prior_logit, hit):
    eta = prior_logit + logit(source_probability) - context_logit
    corrected = clip(1 / (1 + mp.exp(-eta)))
    return mp.log(corrected if hit else 1 - corrected)


def numerical_budget(event_count, mantissa_bits):
    # A declared audit tolerance, NOT a rigorous error bound on an arbitrary
    # C++ standard library. Clipping provides the explicit 1/eps scale. We
    # reserve 64 binary64 and 256 long-double rounding units per event plus
    # a small serialization floor. Overflow/underflow to zero is NEVER waived.
    return mp.mpf("1e-12") + event_count * (
        64 * mp.power(2, -52) + 256 * mp.power(2, -mantissa_bits)) / EPS


def verify(directory, persistence, mantissa_bits=64):
    require(persistence in ("historical_rolling", "window_constant"), "PERSISTENCE_NOT_DECLARED")
    require(mantissa_bits in (53, 64, 113), "UNSUPPORTED_NATIVE_MANTISSA_ASSUMPTION")
    mp.mp.dps = 80
    global EPS
    EPS = mp.mpf("0.0001")
    paths = [directory / EVENT_FILE, directory / SCORE_FILE]
    require(all(path.is_file() for path in paths), "MISSING_TREATMENT_LOGS")
    initial_hashes = {path.name: digest(path) for path in paths}
    groups = {}
    for row in rows(paths[1], SCORE_FIELDS):
        group = (row["run_uuid"], int(row["source_update_id"]), row["candidate_id"])
        u = int(row["source_point_index"])
        require(u in range(4), "SOURCE_SUPPORT_COUNT")
        points = groups.setdefault(group, {})
        require(u not in points, f"DUPLICATE_COMPONENT:{group}:{u}")
        for key in ("source_x", "source_y", "source_weight", "component_likelihood",
                    "weighted_component_likelihood", "region_mixture_likelihood"):
            row[key] = number(row[key])
        for key in ("origin_i", "origin_j", "size_i", "size_j", "transport_members",
                    "legacy_forward_calls", "fixed_point_forward_calls", "source_dim"):
            row[key] = int(row[key])
        require(row["source_weight"] == mp.mpf("0.25"), "SOURCE_WEIGHT")
        require(row["source_dim"] == 2 and row["quadrature_semantics"] == SEMANTICS, "SOURCE_SEMANTICS")
        require(row["transport_members"] > 0 and row["legacy_forward_calls"] == row["transport_members"]
                and row["fixed_point_forward_calls"] == 4 * row["transport_members"], "FORWARD_COST_METADATA")
        require(min(row["size_i"], row["size_j"]) > 0, "INVALID_REGION_SIZE")
        require(all(row[key] > 0 for key in ("component_likelihood", "weighted_component_likelihood",
                                           "region_mixture_likelihood")), "ZERO_OR_NEGATIVE_REPORTED_LIKELIHOOD")
        points[u] = row
    require(groups, "EMPTY_COMPONENT_LOG")
    for group, points in groups.items():
        require(set(points) == set(range(4)), f"MISSING_SOURCE_COMPONENT:{group}")
        for u, row in points.items():
            require(all(row[key] == points[0][key] for key in (
                "origin_i", "origin_j", "size_i", "size_j", "transport_members",
                "region_mixture_likelihood")), f"INCONSISTENT_REGION_METADATA:{group}:{u}")
        # Verify the indexed 2x2 support topology. World origin/cell-size are
        # not logged here, so absolute rectangle fractions remain a code check.
        require(points[0]["source_x"] == points[1]["source_x"] < points[2]["source_x"]
                == points[3]["source_x"] and points[0]["source_y"] == points[2]["source_y"]
                < points[1]["source_y"] == points[3]["source_y"], "SOURCE_POINT_TOPOLOGY")

    series = {}
    event_reference = {}
    context_reference = {}
    update_reference = {}
    persistence_cache = {}
    current = None
    current_key = None
    count = 0

    def finish():
        if current is not None:
            require(current["next"] > current["window"], "EMPTY_SCORED_WINDOW")
            series[current_key] = (current["log_score"], current["next"], current["window"])

    for row in rows(paths[0], EVENT_FIELDS):
        count += 1
        group = (row["run_uuid"], int(row["source_update_id"]), row["candidate_id"])
        u, k, e = (int(row[key]) for key in ("source_point_index", "member_index", "event_index"))
        require(group in groups and u in groups[group], "EVENT_WITHOUT_COMPONENT")
        point = groups[group][u]
        require(0 <= k < point["transport_members"], "TRANSPORT_MEMBER_RANGE")
        require(number(row["source_point_weight"]) == point["source_weight"], "EVENT_WEIGHT_MISMATCH")
        require(number(row["candidate_x"]) == point["source_x"] and
                number(row["candidate_y"]) == point["source_y"], "EVENT_POINT_COORDINATE_MISMATCH")
        require(row["context_centered_log_odds"] == "0" and row["observation_operator"] == "hit_map_probability"
                and row["source_quadrature_context"] == CONTEXT, "UNSUPPORTED_SCORING_MODE")
        window = int(row["event_window_start"])
        require(window >= 0, "NEGATIVE_WINDOW")
        key = (*group, u, k)
        if key != current_key:
            finish()
            require(key not in series, "NONCONTIGUOUS_OR_DUPLICATE_SERIES")
            current_key = key
            current = {"next": 0, "window": window, "previous": mp.mpf(0),
                       "window_previous": mp.mpf(0), "log_score": mp.mpf(0), "time": None}
        require(e == current["next"] and window == current["window"], "EVENT_PREFIX_OR_WINDOW_MISMATCH")
        require(row["observed_hit"] in ("0", "1"), "INVALID_OBSERVED_HIT")
        hit = row["observed_hit"] == "1"
        threshold, concentration, sim_time, probability, context, exposure = (
            number(row[field]) for field in ("threshold", "concentration", "sim_time_s",
                "legacy_hit_probability", "context_value", "aggregate_raw_exposure"))
        require(threshold >= 0 and concentration >= 0 and exposure >= 0 and
                0 <= probability <= 1 and 0 <= context <= 1, "INVALID_OBSERVABLE_OR_PROBABILITY")
        require(int(row["cell_index"]) >= 0 and int(row["block_id"]) >= 0 and
                int(row["iterations_to_record"]) > 0 and number(row["delta_time_s"]) > 0, "INVALID_EVENT_METADATA")
        require(current["time"] is None or sim_time >= current["time"], "NONMONOTONE_EVENT_TIME")
        update = group[:2]
        update_meta = (point["transport_members"], window, int(row["iterations_to_record"]), number(row["delta_time_s"]))
        require(update_reference.setdefault(update, update_meta) == update_meta, "UPDATE_METADATA_MISMATCH")
        event = (row["block_id"], sim_time, row["cell_index"], hit, concentration, threshold)
        require(event_reference.setdefault((update, e), event) == event, "OBSERVATIONS_DIFFER_BETWEEN_CANDIDATES")
        context_key = (update, k, e)
        if context_key not in context_reference:
            context_reference[context_key] = (context, logit(context))
        require(context_reference[context_key][0] == context, "CONTEXT_NOT_SHARED_ACROSS_U_AND_CANDIDATES")
        if e == window:
            current["window_previous"] = current["previous"]
        if e >= window:
            previous = current["previous"] if persistence == "historical_rolling" else current["window_previous"]
            prior_key = (update, e, window)
            if prior_key not in persistence_cache:
                persistence_cache[prior_key] = persistence_logit(threshold, previous)
            current["log_score"] += factor_log(probability, context_reference[context_key][1],
                                                persistence_cache[prior_key], hit)
        current["previous"] = concentration
        current["time"] = sim_time
        current["next"] += 1
    finish()
    require(count > 0, "EMPTY_EVENT_LOG")

    max_error = mp.mpf(0)
    max_budget = mp.mpf(0)
    comparisons = 0
    minimum_log = mp.inf
    all_dimensions = set()
    update_counts = {}
    for group, points in sorted(groups.items()):
        component_logs = []
        dimensions = set()
        members = points[0]["transport_members"]
        for u in range(4):
            member_logs = []
            for k in range(members):
                key = (*group, u, k)
                require(key in series, f"MISSING_U_K_EVENT_SERIES:{key}")
                member_log, events, window = series[key]
                member_logs.append(member_log)
                dimensions.add((events, window))
            component_logs.append(logmean(member_logs))
        require(len(dimensions) == 1, "U_K_EVENT_DIMENSION_MISMATCH")
        events, window = next(iter(dimensions))
        require(update_counts.setdefault(group[:2], (events, window)) == (events, window), "UPDATE_EVENT_PREFIX_MISMATCH")
        all_dimensions.add((members, events, window))
        budget = numerical_budget(events - window, mantissa_bits)
        max_budget = max(max_budget, budget)
        mixture_log = logmean(component_logs)
        minimum_log = min(minimum_log, mixture_log)
        for u, log_score in enumerate(component_logs):
            for field, expected in (("component_likelihood", log_score),
                                    ("weighted_component_likelihood", log_score + mp.log(mp.mpf("0.25"))),
                                    ("region_mixture_likelihood", mixture_log)):
                error = abs(mp.log(points[u][field]) - expected)
                max_error = max(max_error, error)
                comparisons += 1
                require(error <= budget, f"SCORE_MISMATCH:{group}:U{u}:{field}:log_error={mp.nstr(error, 15)}:budget={mp.nstr(budget, 15)}")
    final_hashes = {path.name: digest(path) for path in paths}
    require(final_hashes == initial_hashes, "LOG_CHANGED_DURING_VERIFICATION")
    return {
        "status": "LOGGED_SCORING_ARITHMETIC_PASS", "schema": "M1R_SOURCE_QUADRATURE_RECOMPUTE_V1",
        "input_sha256": initial_hashes, "verifier_sha256": digest(Path(__file__)),
        "persistence": persistence, "native_mantissa_bits_assumed": mantissa_bits,
        "mpmath_version": mp.__version__, "decimal_precision": mp.mp.dps, "epsilon": str(EPS),
        "candidate_updates": len(groups), "source_updates": len(update_counts),
        "event_rows_read": count, "U_K_full_prefix_series": len(series), "score_comparisons": comparisons,
        "dimensions_K_events_window": sorted(all_dimensions),
        "max_absolute_log_score_error": mp.nstr(max_error, 25),
        "max_log_error_budget": mp.nstr(max_budget, 25),
        "minimum_region_log10_likelihood": mp.nstr(minimum_log / mp.log(10), 25),
        "numerical_policy": {
            "comparison": "abs(log(reported)-log(recomputed)) <= budget; zero never accepted",
            "budget": "1e-12 + scored_events * (64*2^-52 + 256*2^-native_mantissa_bits) / 1e-4",
            "scope": "declared roundoff audit tolerance including double log1p and long-double operations; not a proven bound for libc",
            "native_range": "sub-double positive values are preserved; native underflow to zero is a failure",
        },
        "checked": ["all U=4 and independent K/event dimensions", "complete logged event prefixes and window",
                    "shared context across U and candidate IDs within update/K/event",
                    "identical deployed observations across candidates", "2x2 source topology and weights",
                    "source-point coordinates agree across both logs", "unchanged persistence/clip/logit scorer",
                    "arithmetic K mixture followed by complete-prefix U mixture", "forward cost metadata is K plus 4K"],
        "not_established": ["correctness of PF response maps or transport physics", "initial-candidate context construction (no refinement-level field)",
                            "absolute .25/.75 rectangle fractions (world grid metadata absent from these CSVs)",
                            "native ABI mantissa width (declared command-line assumption)",
                            "posterior normalization, closed-loop utility, source identification, causal novelty"],
    }


def write_fixture(directory, tiny=False, window=0):
    """Analytic fixtures: context=persistence gives corrected probability=p.

    Standard U/K products all equal .09 while eventwise averaging gives .25.
    The long fixture is (1e-4)^400=1e-1600, below binary64's range.
    """
    mp.mp.dps = 80
    events = 400 if tiny else 2
    members = 2
    expected = mp.mpf("1e-1600") if tiny else mp.mpf("0.09")
    with (directory / SCORE_FILE).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCORE_FIELDS)
        writer.writeheader()
        for u in range(4):
            writer.writerow(dict(zip(SCORE_FIELDS, ["synthetic", 1, "leaf", 0, 0, 4, 4, u,
                1 if u < 2 else 3, 1 if u % 2 == 0 else 3, ".25", members,
                mp.nstr(expected, 75), mp.nstr(expected / 4, 75), mp.nstr(expected, 75),
                members, 4 * members, 2, SEMANTICS])))
    with (directory / EVENT_FILE).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EVENT_FIELDS)
        writer.writeheader()
        for u in range(4):
            for k in range(members):
                for e in range(events + window):
                    probability = ".0001" if tiny else (".9" if (u + k + e - window) % 2 == 0 else ".1")
                    # threshold=previous=0 gives persistence=context=.5 exactly.
                    writer.writerow(dict(zip(EVENT_FIELDS, ["synthetic", 1, "leaf",
                        1 if u < 2 else 3, 1 if u % 2 == 0 else 3, k, e, 0, str(e), 0, 1,
                        "0", "0", probability, "0", 10, ".1", ".5", 0, "hit_map_probability",
                        u, ".25", window, CONTEXT])))


def self_test():
    cases = []
    with tempfile.TemporaryDirectory(prefix="m1r_quadrature_verify_") as temporary:
        directory = Path(temporary)
        for tiny, window, mode in ((False, 0, "historical_rolling"), (False, 1, "window_constant"),
                                   (True, 0, "historical_rolling")):
            write_fixture(directory, tiny, window)
            result = verify(directory, mode)
            expected_log = -1600 if tiny else mp.log10(mp.mpf(".09"))
            require(abs(number(result["minimum_region_log10_likelihood"]) - expected_log) < mp.mpf("1e-20"), "ANALYTIC_REFERENCE_FAILED")
            cases.append({"tiny": tiny, "window": window, "persistence": mode,
                          "status": result["status"], "log10_likelihood": result["minimum_region_log10_likelihood"]})
        for mutation in ("wrong_component", "missing_row", "unshared_context"):
            write_fixture(directory)
            path = directory / (SCORE_FILE if mutation == "wrong_component" else EVENT_FILE)
            fields = SCORE_FIELDS if mutation == "wrong_component" else EVENT_FIELDS
            records = list(rows(path, fields))
            if mutation == "wrong_component":
                records[0]["component_likelihood"] = ".25"
            elif mutation == "missing_row":
                records.pop()
            else:
                records[-1]["context_value"] = ".6"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(records)
            try:
                verify(directory, "historical_rolling")
            except ValueError as error:
                cases.append({"mutation": mutation, "status": "REJECTED", "reason": str(error)})
            else:
                raise AssertionError(f"mutation accepted: {mutation}")
    return {"status": "SYNTHETIC_VERIFIER_SELFTEST_PASS", "cases": cases,
            "limits": "synthetic arithmetic and rejection checks only; no C++ runtime/physical/utility PASS"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context-dir", type=Path)
    parser.add_argument("--persistence", choices=("historical_rolling", "window_constant"))
    parser.add_argument("--native-mantissa-bits", type=int, default=64)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not args.self_test and (args.context_dir is None or args.persistence is None):
        parser.error("--context-dir and an explicit --persistence are required")
    try:
        report = self_test() if args.self_test else verify(args.context_dir, args.persistence, args.native_mantissa_bits)
        code = 0
    except (ValueError, OSError, KeyError, csv.Error) as error:
        report = {"status": "SCORING_AUDIT_FAIL", "reason": str(error), "verifier_sha256": digest(Path(__file__))}
        code = 1
    serialized = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8", newline="\n")
    print(serialized, end="")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
