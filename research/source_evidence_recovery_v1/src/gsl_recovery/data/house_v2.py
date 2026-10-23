"""Strict numerical-only adapter for the archived House02 18-source panel.

Only the archive's already authorized offline-fit rows are loaded.  The original
test fold stays unopened; a development fold is carved from the original train
sources.  There is no physical-clock, local-wind or privileged 3D-state claim.
This module deliberately cannot export a future response bank for deployment.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

import numpy as np


class HouseQualificationError(ValueError):
    """A source document or numerical qualification is missing/inconsistent."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _csv(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))


def _json(data: bytes):
    return json.loads(data.decode("utf-8-sig"))


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def export_house_training(
    archive: str | Path,
    out: str | Path,
    *,
    test_fold: int = 0,
    dev_fold: int = 1,
) -> dict:
    """Export train/dev arrays without opening original test response vectors.

    Original 3-fold source grouping is preserved. Default: original fold 0 is
    held out; fold 1 supplies development data and fold 2 supplies training.
    The routing CSV is metadata, including labels for authorized train sources;
    it is not passed to any online process. Original test vector bytes are never
    read by this function. An export is refused if provenance permissions do not
    explicitly support offline fit and source-separated evaluation.
    """
    archive, out = Path(archive), Path(out)
    if test_fold not in (0, 1, 2) or dev_fold not in (0, 1, 2) or test_fold == dev_fold:
        raise HouseQualificationError("test/dev folds must differ and be original folds 0/1/2")
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("Refuse to overwrite a frozen House export")
    out.mkdir(parents=True, exist_ok=True)
    requested = [
        "inputs/ARCHIVE_DATA_SCOPE.json", "inputs/PREREGISTRATION.json",
        "inputs/SOURCE_FOLDS.csv", "inputs/PROBES.json", "PROTOCOL.json",
        "inputs/TRUTH_EVALUATION.csv",
    ]
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            p = Path(name)
            if p.is_absolute() or ".." in p.parts:
                raise HouseQualificationError("Unsafe archive path")
        missing = [name for name in requested if name not in z.namelist()]
        if missing:
            raise HouseQualificationError("Missing original permission/metadata files: " + repr(missing))
        # Permissions are checked before opening the routing index or responses.
        scope_b = z.read(requested[0]); prereg_b = z.read(requested[1])
        scope, prereg = _json(scope_b), _json(prereg_b)
        if "offline fit" not in str(scope.get("role", "")).lower():
            raise HouseQualificationError("Original scope does not authorize offline fit")
        if prereg.get("role") != "RETROSPECTIVE_NUMERICAL_SOURCE_HOLDOUT_ONLY":
            raise HouseQualificationError("Expected explicit numerical-only source-holdout scope")
        if prereg.get("source_strength") != "ABSOLUTE_Q_HOLD":
            raise HouseQualificationError("Unexpected source-strength provenance; requalify the new asset")
        folds_b = z.read(requested[2]); probes_b = z.read(requested[3])
        protocol_b = z.read(requested[4]); protocol = _json(protocol_b)
        folds, probes = _csv(folds_b), _json(probes_b)
        if prereg.get("SOURCE_FOLDS_sha256") != _sha(folds_b):
            raise HouseQualificationError("Original source-fold hash mismatch")
        if len(folds) != 18 or len(probes) != 30:
            raise HouseQualificationError("This adapter is for the qualified 18-source/30-probe panel")
        source_ids = [row["source_id"] for row in folds]
        if len(set(source_ids)) != len(source_ids):
            raise HouseQualificationError("Duplicate source identity")
        source_to_index = {name: i for i, name in enumerate(source_ids)}
        original_test = {r["source_id"] for r in folds if int(r["fold"]) == test_fold}
        original_train = set(source_ids) - original_test
        pre = next((f for f in prereg.get("folds", []) if f.get("fold") == test_fold), None)
        if pre is None or set(pre.get("test_source_ids", [])) != original_test:
            raise HouseQualificationError("Original preregistered test-source mapping missing")
        groups = {
            "train": {r["source_id"] for r in folds if int(r["fold"]) not in (test_fold, dev_fold)},
            "dev": {r["source_id"] for r in folds if int(r["fold"]) == dev_fold},
        }
        if any(not group.issubset(original_train) for group in groups.values()):
            raise HouseQualificationError("Attempt to train/develop on original test sources")
        geometry = np.array([[float(p["center_x_m"]), float(p["center_y_m"]), float(p["z_m"])] for p in probes])
        if not np.isfinite(geometry).all():
            raise HouseQualificationError("Nonfinite probe geometry")
        # Only metadata routes members; retained test values stay sealed in ZIP.
        routing_b = z.read(requested[5]); rows = _csv(routing_b)
        required = {"sample_id", "source_id", "seed", "x_m", "y_m", "source_z_m", "raw_cube_sha256", "response_sha256", "n_values"}
        if not rows or not required.issubset(rows[0]):
            raise HouseQualificationError("Routing schema incomplete")
        if any(r["source_id"] not in source_to_index for r in rows):
            raise HouseQualificationError("Unregistered source")
        keys = [(r["source_id"], r["seed"]) for r in rows]
        if len(keys) != len(set(keys)):
            raise HouseQualificationError("Duplicate source-realization metadata")
        expected = {r["source_id"]: int(r["num_realizations"]) for r in folds}
        if any(sum(r["source_id"] == sid for r in rows) != count for sid, count in expected.items()):
            raise HouseQualificationError("Realization counts do not match original source manifest")
        source_xy = np.array([[float(r["x_m"]), float(r["y_m"])] for r in folds])
        if any(not np.allclose([float(r["x_m"]), float(r["y_m"])], source_xy[source_to_index[r["source_id"]]], atol=1e-9, rtol=0) for r in rows):
            raise HouseQualificationError("Source coordinates conflict between manifests")
        group_rows = {role: sorted([r for r in rows if r["source_id"] in names], key=lambda r:(source_to_index[r["source_id"]], int(r["seed"]))) for role, names in groups.items()}
        cubes = {role: {r["raw_cube_sha256"] for r in rr} for role, rr in group_rows.items()}
        test_cubes = {r["raw_cube_sha256"] for r in rows if r["source_id"] in original_test}
        if cubes["train"] & cubes["dev"] or (cubes["train"] | cubes["dev"]) & test_cubes:
            raise HouseQualificationError("Raw-cube identity crosses a split; investigate before training")
        authorization = {
            "decision": "AUTHORIZED_NUMERICAL_OFFLINE_FIT_ON_ORIGINAL_TRAIN_SOURCES_ONLY",
            "scope_path": requested[0], "scope_sha256": _sha(scope_b),
            "preregistration_path": requested[1], "preregistration_sha256": _sha(prereg_b),
            "scope_role_verbatim": scope["role"], "preregistered_role": prereg["role"],
            "original_test_fold": test_fold, "dev_fold_within_original_train": dev_fold,
            "training_is_new_user_authorized_offline_research": True,
            "original_test_response_bytes_opened": False,
        }
        split = {
            "schema": "HOUSE02_NUMERICAL_RECORD_SEQUENCE_V1", "archive_sha256": _file_sha(archive),
            "original_source_folds_sha256": _sha(folds_b), "routing_metadata_sha256": _sha(routing_b),
            "authorization": authorization,
            "train_sources": sorted(groups["train"]), "dev_sources": sorted(groups["dev"]),
            "sealed_test_sources": sorted(original_test),
            "time_mode": "record_index", "physical_time_available": False,
            "local_wind_available": False, "full_3d_teacher_state_available": False,
            "online_response_bank_allowed": False, "scientific_scope": prereg["role"],
            "observations": "4-native-cell mean; 30 probes x 10 saved records; not point instrument or a feasible UAV route",
            "original_record_index_used": protocol.get("record_index"),
            "original_record_native_label": protocol.get("record_native_label"),
        }
        # Persist the split before reading any response values, as an auditable freeze.
        _write_json(out / "SPLIT_FREEZE.json", split)
        _write_json(out / "AUTHORIZATION_EVIDENCE.json", authorization)
        evidence_dir = out / "authorization_sources"
        evidence_dir.mkdir(exist_ok=True)
        for name, data in (("ARCHIVE_DATA_SCOPE.json", scope_b), ("PREREGISTRATION.json", prereg_b), ("SOURCE_FOLDS.csv", folds_b)):
            (evidence_dir / name).write_bytes(data)
        artifacts = []
        for role, rr in group_rows.items():
            gas = []; src = []; manifest_rows = []
            for row in rr:
                name = "inputs/vectors/" + row["sample_id"] + ".npy"
                data = z.read(name)
                if _sha(data) != row["response_sha256"]:
                    raise HouseQualificationError("Response SHA mismatch: " + name)
                value = np.load(io.BytesIO(data), allow_pickle=False)
                if value.shape != (300,) or int(row["n_values"]) != 300 or not np.isfinite(value).all() or np.any(value < 0):
                    raise HouseQualificationError("Invalid response values/shape: " + name)
                gas.append(value.reshape(10, 30))
                src.append([float(row[k]) for k in ("x_m", "y_m", "source_z_m")])
                manifest_rows.append({k: row[k] for k in ("sample_id", "source_id", "seed", "raw_cube_sha256", "response_sha256")})
            n = len(rr)
            np.savez_compressed(
                out / (role + ".npz"),
                gas=np.asarray(gas, dtype=np.float32), source_xyz=np.asarray(src, dtype=np.float32),
                probe_xyz=geometry.astype(np.float32), candidate_xy=source_xy.astype(np.float32),
                source_index=np.array([source_to_index[r["source_id"]] for r in rr], dtype=np.int64),
                source_ids=np.array([r["source_id"] for r in rr]),
                sample_ids=np.array([r["sample_id"] for r in rr]),
                realization_ids=np.array([r["source_id"] + ":seed=" + r["seed"] + ":cube=" + r["raw_cube_sha256"] for r in rr]),
                record_index=np.arange(10, dtype=np.int64), physical_time_available=np.array(False),
                wind=np.full((n, 10, 30, 3), np.nan, dtype=np.float32),
                wind_available=np.zeros((n, 10, 30), dtype=bool),
                partition=np.array(role), scope=np.array(prereg["role"]),
                three_dimensional_dynamics_qualified=np.array(False),
            )
            _write_json(out / (role + "_manifest.json"), manifest_rows)
            artifacts.append({"role": role, "samples": n, "sources": len(groups[role]), "sha256": _file_sha(out / (role + ".npz"))})
        np.savez_compressed(out / "student_geometry.npz", candidate_xy=source_xy, probe_xyz=geometry)
    receipt = {
        "status": "PASS_NUMERICAL_ONLY_TRAIN_DEV_EXPORT",
        "archive": str(archive.resolve()), "archive_sha256": split["archive_sha256"],
        "authorization": authorization, "artifacts": artifacts,
        "original_test_samples_unopened": sum(r["source_id"] in original_test for r in rows),
        "original_test_response_bytes_opened": False, "future_response_library_exported": False,
        "local_wind_fabricated": False, "physical_clock_fabricated": False,
        "teacher_state": "BLOCKED_NO_FULL_3D_HISTORY_IN_THIS_ASSET",
        "evaluation_status": "NOT_RUN", "native_active_loop_status": "NOT_QUALIFIED_BY_THIS_DATA",
        "limits": ["Previously opened retrospective development data", "Single House", "All probes at z=0.2m", "Absolute source Q and full historical wind remain HOLD", "Rows sharing a plume seed in different source runs are not automatically independent wind worlds", "10 records are correlated within each realization"],
    }
    _write_json(out / "QUALIFICATION_RECEIPT.json", receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--test-fold", type=int, default=0)
    parser.add_argument("--dev-fold", type=int, default=1)
    args = parser.parse_args()
    print(json.dumps(export_house_training(args.archive, args.out, test_fold=args.test_fold, dev_fold=args.dev_fold), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
