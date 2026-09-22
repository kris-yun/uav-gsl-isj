#!/usr/bin/env python3
"""Freeze a source-blind HCMC definability failure without inventing fallback mass."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, fields: tuple[str, ...], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_validator(path: Path):
    spec = importlib.util.spec_from_file_location("hcmc_v1_frozen", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validator", type=Path, required=True)
    parser.add_argument("--native-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    h = load_validator(args.validator.resolve())
    output_root = args.output_root.resolve()
    generated: list[Path] = []
    reports = []

    for case_dir in h.discover_case_dirs(args.native_root.resolve(), []):
        bank = case_dir / "context_bank"
        update_id, update_time, timing = h.select_final_update(bank, 300.0)
        metadata = h.grid_metadata(timing)
        update_dir = bank / f"source_update_{update_id:04d}"
        cells = h.load_cells(update_dir, metadata)
        final_ids, geometry, ownership = h.derive_final_leaves(update_dir, cells)
        rows_by_candidate = {candidate_id: [] for candidate_id in final_ids}
        for row in h.read_csv(update_dir / "candidate_support_alignment.csv"):
            if row["candidate_id"] in rows_by_candidate:
                rows_by_candidate[row["candidate_id"]].append(row)
        candidates = {key: h.Candidate(value) for key, value in rows_by_candidate.items()}
        score_results = {key: candidate.score() for key, candidate in candidates.items()}
        scores = {key: result[0] for key, result in score_results.items()}
        diagnostics = {key: result[1] for key, result in score_results.items()}
        ranks = h.average_percentile(scores, final_ids)
        valid_ids = [key for key in final_ids if scores[key] is not None]
        rank_mass = sum(ranks.values())
        case_output = output_root / case_dir.name
        score_path = case_output / "candidate_scores.csv"
        rank_path = case_output / "candidate_ranks.csv"
        diagnostic_path = case_output / "source_blind_definability.json"
        native_path = case_output / "native_posterior.csv"
        write_csv(
            score_path,
            ("candidate_id", "score", "valid_slope_comparisons", "support_rows_above_confidence_floor", "pairs_scale_1", "pairs_scale_2", "pairs_scale_4", "pairs_scale_8"),
            [
                {
                    "candidate_id": key,
                    "score": "" if scores[key] is None else format(scores[key], ".17g"),
                    "valid_slope_comparisons": diagnostics[key]["valid_slope_comparisons"],
                    "support_rows_above_confidence_floor": diagnostics[key]["support_rows_above_confidence_floor"],
                    **{f"pairs_scale_{scale}": diagnostics[key]["pair_counts_by_scale"][str(scale)] for scale in h.SCALES},
                }
                for key in final_ids
            ],
        )
        ordered = sorted(final_ids, key=lambda key: (-ranks[key], key))
        write_csv(
            rank_path,
            ("candidate_id", "average_percentile_rank", "ordinal_rank_best_is_1"),
            [
                {"candidate_id": key, "average_percentile_rank": format(ranks[key], ".17g"), "ordinal_rank_best_is_1": index + 1}
                for index, key in enumerate(ordered)
            ],
        )
        h.write_posterior(native_path, cells, h.normalize({cell.cell_index: cell.native_probability for cell in cells}))
        status = "DEFINED" if rank_mass > 0.0 and math.isfinite(rank_mass) else "UNDEFINED_ALL_CANDIDATES_INVALID"
        diagnostic = {
            "case_id": case_dir.name,
            "source_truth_loaded": False,
            "selected_update_id": update_id,
            "selected_update_time_s": update_time,
            "final_leaf_count": len(final_ids),
            "valid_candidate_count": len(valid_ids),
            "total_valid_slope_comparisons": sum(item["valid_slope_comparisons"] for item in diagnostics.values()),
            "hcmc_rank_mass_before_normalization": rank_mass,
            "status": status,
            "frozen_rule": "invalid candidate density = 0; no Native or uniform fallback",
        }
        if status == "DEFINED":
            hcmc_path = case_output / "hcmc_posterior.csv"
            h.write_posterior(hcmc_path, cells, h.posterior_from_ranks(cells, ownership, ranks))
            generated.append(hcmc_path)
        write_json(diagnostic_path, diagnostic)
        generated.extend((score_path, rank_path, diagnostic_path, native_path))
        reports.append(diagnostic)

    undefined = [report["case_id"] for report in reports if report["status"] != "DEFINED"]
    freeze = {
        "contract": "HCMC_V1_SOURCE_BLIND_DEFINABILITY_V1",
        "phase": "PRE_TRUTH_DEFINABILITY_FREEZE",
        "truth_inputs_loaded": False,
        "hcmc_code_sha256": sha256(args.validator),
        "case_reports": reports,
        "undefined_cases": undefined,
        "destructive_controls": {
            "random_leaf_permutation_repetitions": 300,
            "spatial_shuffle_repetitions": 30,
            "status": "NOT_EVALUABLE_BECAUSE_REAL_HCMC_POSTERIOR_IS_UNDEFINED" if undefined else "READY",
        },
        "anti_metric_gaming_diagnostics": "NOT_EVALUABLE_FOR_UNDEFINED_HCMC_CASES",
        "verdict": "HCMC_V1_SOURCE_BLIND_DEFINABILITY_NO_GO" if undefined else "HCMC_V1_SOURCE_BLIND_DEFINABILITY_PASS",
        "generated_file_sha256": {str(path.relative_to(output_root)): sha256(path) for path in sorted(generated)},
    }
    freeze_path = output_root / "PRE_TRUTH_DEFINABILITY_FREEZE.json"
    write_json(freeze_path, freeze)
    print(json.dumps(freeze, indent=2, sort_keys=True))
    raise SystemExit(20 if undefined else 0)


if __name__ == "__main__":
    main()
