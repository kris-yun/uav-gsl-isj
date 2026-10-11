"""Independent arithmetic from frozen predictions. No fitting or phi queries."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import argparse, csv, json, math


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def conditional_gap_summary(root):
    # Descriptive post-result arithmetic; not a new fitted model or primary endpoint.
    data = read_csv(root / "CLASS_CONDITIONAL_RESPONSE_DIFFERENCES.csv")
    summary = []
    for fold in sorted({r["fold"] for r in data}):
        supported = [r for r in data if r["fold"] == fold and int(r["test_C7_count"]) > 0 and int(r["test_K2_count"]) > 0]
        values = [(min(int(r["test_C7_count"]), int(r["test_K2_count"])),
                   float(r["train_C7_minus_K2_h"]), float(r["test_C7_minus_K2_h"])) for r in supported]
        count_weight = sum(w for w, a, b in values)
        train_energy = math.fsum(w * a * a for w, a, b in values)
        test_energy = math.fsum(w * b * b for w, a, b in values)
        dot = math.fsum(w * a * b for w, a, b in values)
        error = math.fsum(w * (a - b) ** 2 for w, a, b in values)
        summary.append(dict(fold=fold,rows=len(supported),count_weight_sum=count_weight,
                            weighted_train_gap_energy=train_energy/count_weight,
                            weighted_test_gap_energy=test_energy/count_weight,
                            weighted_gap_fit_MSE=error/count_weight,
                            gap_fit_relative_to_test_zero=error/test_energy,
                            weighted_gap_cosine=dot/math.sqrt(train_energy*test_energy),
                            same_sign_test_gap_energy=math.fsum(w*b*b for w,a,b in values if a*b>0)/test_energy,
                            opposite_sign_test_gap_energy=math.fsum(w*b*b for w,a,b in values if a*b<0)/test_energy,
                            all_rows_included_no_gap_threshold=True,
                            scope="Post-result descriptive aggregate of all jointly supported fine-class/pose rows; correlated particles/poses, no significance claim or change to primary endpoint"))
    return summary


def main(root, out):
    pred = read_csv(root / "PREDICTIONS_BLIND.csv")
    saved = read_csv(root / "BANK_METRICS_ANALYSIS.csv")
    mapping = json.loads((root / "POST_FREEZE_GENERATOR_MAPPING.json").read_text(encoding="utf-8"))
    result = []
    identity_max = 0.0
    arms = ["U", "S", "C_C7", "C_K2", "C_ORACLE"]
    for fold, role, bank in sorted({(r["fold"], r["role"], r["bank"]) for r in pred}):
        subset = [r for r in pred if (r["fold"], r["role"], r["bank"]) == (fold, role, bank) and int(r["membership_branch"]) == 0]
        assert len(subset) == 50
        for arm in arms:
            col = "C_" + mapping[bank] if arm == "C_ORACLE" else arm
            errors = [float(r[col + "_prediction_ppm"]) - float(r["target_phi64_ppm"]) for r in subset]
            for r, error in zip(subset, errors):
                component_error = float(r[col + "_Q_prediction_ppm"]) - float(r["target_Q64_ppm"])
                identity_max = max(identity_max, abs(component_error - error))
            record = dict(fold=fold, role=role, bank=bank, arm=arm,
                          MSE_ppm2=math.fsum(e * e for e in errors) / 50,
                          mean_signed_error_ppm=math.fsum(errors) / 50,
                          MAE_ppm=math.fsum(abs(e) for e in errors) / 50,
                          event_errors_native_F32=sum(int(r[col + "_event"]) != int(r["native_F32_event"]) for r in subset),
                          tail_alone_positive_events=sum(int(r["tail_alone_event"]) for r in subset))
            original = next(r for r in saved if (r["fold"], r["role"], r["bank"], r["arm"]) == (fold, role, bank, arm))
            for key in ["MSE_ppm2", "mean_signed_error_ppm", "MAE_ppm"]:
                assert math.isclose(record[key], float(original[key]), rel_tol=2e-12, abs_tol=3e-13), (record, original)
            for key in ["event_errors_native_F32", "tail_alone_positive_events"]:
                assert record[key] == int(original[key])
            result.append(record)
    test = [r for r in result if r["role"] == "test"]
    pair = []
    for bank in sorted({r["bank"] for r in test}):
        by = {r["arm"]: r for r in test if r["bank"] == bank}
        for low, high in [("U", "S"), ("S", "C_ORACLE")]:
            a, b = by[low], by[high]
            tol = max(1e-12, 1e-10 * max(a["MSE_ppm2"], b["MSE_ppm2"]))
            pair.append(dict(bank=bank, fold=a["fold"], pair=low + "_to_" + high,
                             MSE_reduction=a["MSE_ppm2"] - b["MSE_ppm2"],
                             MAE_reduction=a["MAE_ppm"] - b["MAE_ppm"],
                             absolute_mean_bias_reduction=abs(a["mean_signed_error_ppm"]) - abs(b["mean_signed_error_ppm"]),
                             comparison_tolerance_ppm2=tol,
                             MSE_direction="IMPROVE" if a["MSE_ppm2"] - b["MSE_ppm2"] > tol else "WORSEN" if b["MSE_ppm2"] - a["MSE_ppm2"] > tol else "NUMERICALLY_SAME"))
    report = dict(status="PASS_INDEPENDENT_SCIENTIFIC_ARITHMETIC", independent_metrics=result,
                  test_paired_directions=pair,
                  equal_bank_mean_test_MSE={arm: math.fsum(r["MSE_ppm2"] for r in test if r["arm"] == arm) / 4 for arm in arms},
                  maximum_total_vs_Q_error_identity_difference_ppm=identity_max,
                  descriptive_fine_class_gap_recomputation=conditional_gap_summary(root),
                  scope="Frozen predictions only; no additional kernel fits, physics, source classification, significance or deployed localization claim")
    assert identity_max < 3e-13
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ["status", "test_paired_directions", "equal_bank_mean_test_MSE", "maximum_total_vs_Q_error_identity_difference_ppm"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    main(args.root, args.out)
