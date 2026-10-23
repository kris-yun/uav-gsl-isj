import csv
import hashlib
import io
import json
import zipfile

import numpy as np
import pytest

from gsl_recovery.data.house_v2 import export_house_training, HouseQualificationError


def _csv(rows):
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader(); writer.writerows(rows)
    return stream.getvalue().encode()


def _archive(tmp_path, *, allow_fit=True, tamper=False, collision=False):
    path = tmp_path / "archive.zip"
    folds = [dict(source_id=f"s{i}", x_m=i, y_m=1, fold=i % 3, num_realizations=2) for i in range(18)]
    fbytes = _csv(folds)
    prereg = {
        "role": "RETROSPECTIVE_NUMERICAL_SOURCE_HOLDOUT_ONLY", "source_strength": "ABSOLUTE_Q_HOLD",
        "SOURCE_FOLDS_sha256": hashlib.sha256(fbytes).hexdigest(),
        "folds": [dict(fold=f, test_source_ids=[r["source_id"] for r in folds if r["fold"] == f]) for f in range(3)],
    }
    rows = []; values = {}
    for i in range(18):
        for seed in range(2):
            sample = f"sample_{i}_{seed}"
            stream = io.BytesIO(); np.save(stream, np.full(300, 0.1 + i + seed, dtype=np.float32))
            raw = stream.getvalue()
            rows.append(dict(sample_id=sample, source_id=f"s{i}", seed=seed, x_m=i, y_m=1,
                             source_z_m=0.2, raw_cube_sha256=("duplicate" if collision else f"cube_{i}_{seed}"),
                             response_sha256=hashlib.sha256(raw).hexdigest(), n_values=300))
            values[f"inputs/vectors/{sample}.npy"] = raw
    if tamper:
        values["inputs/vectors/sample_2_0.npy"] += b"tamper"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("inputs/ARCHIVE_DATA_SCOPE.json", json.dumps({"role": "Only benchmark and offline fit" if allow_fit else "evaluation only"}))
        z.writestr("inputs/PREREGISTRATION.json", json.dumps(prereg))
        z.writestr("inputs/SOURCE_FOLDS.csv", fbytes)
        z.writestr("inputs/TRUTH_EVALUATION.csv", _csv(rows))
        z.writestr("inputs/PROBES.json", json.dumps([dict(center_x_m=i, center_y_m=0, z_m=.2) for i in range(30)]))
        z.writestr("PROTOCOL.json", json.dumps(dict(record_index=9, record_native_label=550)))
        for name, raw in values.items(): z.writestr(name, raw)
    return path


def test_preserves_original_holdout_and_missing_wind(tmp_path, monkeypatch):
    path = _archive(tmp_path)
    opened = []
    original = zipfile.ZipFile.read
    def observe(self, name, *args, **kwargs):
        opened.append(name)
        return original(self, name, *args, **kwargs)
    monkeypatch.setattr(zipfile.ZipFile, "read", observe)
    receipt = export_house_training(path, tmp_path / "out")
    assert receipt["original_test_samples_unopened"] == 12
    assert not receipt["original_test_response_bytes_opened"]
    for i in range(0, 18, 3):
        for seed in range(2): assert f"inputs/vectors/sample_{i}_{seed}.npy" not in opened
    with np.load(tmp_path / "out/train.npz", allow_pickle=False) as data:
        assert data["gas"].shape == (12, 10, 30)
        assert not data["wind_available"].any()
        assert np.isnan(data["wind"]).all()
        assert not bool(data["physical_time_available"])
        assert set(data["source_index"].tolist()) == set(range(2, 18, 3))


def test_permission_refuses_before_reading_routing_or_responses(tmp_path, monkeypatch):
    path = _archive(tmp_path, allow_fit=False)
    opened = []; original = zipfile.ZipFile.read
    def observe(self, name, *args, **kwargs):
        opened.append(name); return original(self, name, *args, **kwargs)
    monkeypatch.setattr(zipfile.ZipFile, "read", observe)
    with pytest.raises(HouseQualificationError, match="authorize offline fit"):
        export_house_training(path, tmp_path / "out")
    assert "inputs/TRUTH_EVALUATION.csv" not in opened
    assert not any("vectors" in name for name in opened)


def test_tamper_fails_closed(tmp_path):
    with pytest.raises(HouseQualificationError, match="SHA mismatch"):
        export_house_training(_archive(tmp_path, tamper=True), tmp_path / "out")
    assert not (tmp_path / "out/QUALIFICATION_RECEIPT.json").exists()


def test_duplicate_realization_across_splits_fails_closed(tmp_path):
    with pytest.raises(HouseQualificationError, match="Raw-cube identity crosses"):
        export_house_training(_archive(tmp_path, collision=True), tmp_path / "out")
