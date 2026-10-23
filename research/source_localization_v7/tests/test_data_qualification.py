"""Scientific failure gates, including real native bytes when present."""
import csv
import os
from pathlib import Path
import numpy as np
import pytest
from gsl_discrimination.data import OCBDataset, DataQualification, QualificationError, SynchronousBlock
from gsl_discrimination.data.ocb import load_manifest, verify_file


def small_block():
    return SynchronousBlock(
        values=np.array([[.12, .32], [.25, .45]]),
        times_s=[50.2998047, 100.099045],
        positions_m=[[0., 0., .2], [1., 0., .2]],
        sensor_ids=("a", "b"),
        qualification=DataQualification(synchronous_spatial=True, physical_clock=True,
                                       scope="sparse_native_snapshots"),
        block_id="b", realization_id="r",
    )


def test_sparse_clock_cannot_be_promoted_to_dynamic():
    block = small_block()
    with pytest.raises(QualificationError, match="continuous_window"):
        block.require_dynamic()
    with pytest.raises(QualificationError, match="physical clock"):
        DataQualification(continuous_window=True)
    with pytest.raises(QualificationError, match="explicit boolean"):
        DataQualification(continuous_window="yes")


def test_wind_flag_without_vectors_is_rejected():
    block = small_block()
    with pytest.raises(QualificationError, match="vectors"):
        SynchronousBlock(block.values, block.times_s, block.positions_m, block.sensor_ids,
                         DataQualification(synchronous_spatial=True, local_wind=True), "c", "r")


def test_interpolated_record_does_not_acquire_native_status():
    block = small_block()
    with pytest.raises(QualificationError, match="interpolation"):
        SynchronousBlock(block.values, block.times_s, block.positions_m, block.sensor_ids,
                         block.qualification, "c", "r", metadata={"interpolated": True})


def test_same_frame_different_sensor_clocks_are_not_synchronous(tmp_path):
    path = tmp_path / "block.csv"
    small_block().save_csv(path)
    with path.open(newline="") as f:
        reader = csv.DictReader(f); fields = reader.fieldnames; rows = list(reader)
    rows[1]["time_s"] = "50.3000"
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    with pytest.raises(QualificationError, match="timestamp"):
        SynchronousBlock.load_csv(path)


def test_manifest_is_whole_seed_discovery_and_source_heights_are_distinct():
    manifest = load_manifest()
    train = [w for w in manifest["worlds"] if w["split"] == "train"]
    dev = [w for w in manifest["worlds"] if w["split"] == "dev"]
    assert len(train) == len(dev) == 4
    assert set(w["master_seed"] for w in train).isdisjoint(w["master_seed"] for w in dev)
    assert {w["source_xyz"][2] for w in manifest["worlds"]} == {-.3, .4}
    assert not manifest["qualification"]["source_occupancy_validated"]
    assert not manifest["qualification"]["continuous_window"]


@pytest.fixture(scope="module")
def dataset():
    default = Path(__file__).resolve().parents[2] / "v7_work/discovery/ocb_r2"
    root = Path(os.environ.get("V7_OCB_ROOT", default))
    if not (root / "raw/ocb_r2_cfg00_r01.cube.npy").exists():
        pytest.skip("native OCB files not packaged; use fetch_ocb_assets.py and V7_OCB_ROOT")
    return OCBDataset(root)


def test_native_pooling_and_same_frame_query(dataset):
    w = dataset.worlds[0]
    p = dataset.probes[0]
    samples = []
    for ix in range(p["native_x0"], p["native_x1_exclusive"]):
        for iy in range(p["native_y0"], p["native_y1_exclusive"]):
            samples.append([-7.55+.1*(ix+.5), -7.88+.1*(iy+.5)])
    native = dataset.query_snapshot(w, 0, samples)
    assert native.mean(dtype=np.float64) == dataset.query_probes(w, 0, ["1"])[0]
    with pytest.raises(QualificationError, match="cell centres"):
        dataset.query_snapshot(w, 0, [[-.6, 1.95]])
    with pytest.raises(QualificationError, match="integer"):
        dataset.query_snapshot(w, 50.2998047, samples)
    with pytest.raises(QualificationError, match="temporal"):
        dataset.query_time(w, 60.0)


def test_byte_tampering_is_detected_before_loading(dataset, tmp_path):
    spec = dataset.manifest["worlds"][0]["files"]["pooled"]
    raw = dataset.root / "raw" / spec["filename"]
    bad = bytearray(raw.read_bytes()); bad[-1] ^= 1
    path = tmp_path / spec["filename"]; path.write_bytes(bad)
    with pytest.raises(QualificationError, match="SHA256"):
        verify_file(path, spec)


def test_real_csv_npz_keep_native_times_and_truth_out_of_block(dataset, tmp_path):
    for world in dataset.worlds:
        block = dataset.to_block(world, [0, 1, 2], ["1", "2"])
        npz = tmp_path / f"{world.run_id}.npz"; csv_path = tmp_path / f"{world.run_id}.csv"
        block.save_npz(npz); block.save_csv(csv_path)
        for loaded in (SynchronousBlock.load_npz(npz), SynchronousBlock.load_csv(csv_path)):
            assert np.array_equal(loaded.times_s, world.times_s[:3])
            assert np.array_equal(loaded.values, block.values)
            assert "source_id" not in loaded.metadata and "source_xyz" not in loaded.metadata
            with pytest.raises(QualificationError):
                loaded.require_dynamic()
