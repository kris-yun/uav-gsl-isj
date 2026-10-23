"""Read only the eight authorized X00 discovery exports.

The original 50-second snapshot gaps are retained. No temporal interpolation,
local-wind substitute, source-occupancy promotion, or source-label exposure in
observation blocks is performed.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import numpy as np
from .schema import DataQualification, QualificationError, SynchronousBlock


PIN = "005ba6a34d95fdfe340050df96fe30a688fa71bf"
RUN_IDS = tuple(f"{prefix}_r{r:02d}" for prefix in
                ("ocb_r2_cfg00", "ocb_r2_s2x_x00") for r in range(1, 5))


def load_manifest(path=None) -> dict:
    path = Path(path) if path is not None else Path(__file__).with_name("ocb_x00_manifest.json")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest["repository"] != "kris-yun/uav-gsl-isj" or manifest["commit"] != PIN:
        raise QualificationError("reader is pinned to the authorized X00 discovery release")
    ids = [w["run_id"] for w in manifest["worlds"]]
    if len(ids) != 8 or set(ids) != set(RUN_IDS):
        raise QualificationError("only the eight authorized X00 discovery worlds are admitted")
    if manifest["scope"] != "previously_open_discovery":
        raise QualificationError("confirmation/holdout worlds are not authorized by this adapter")
    return manifest


def verify_file(path, descriptor: dict) -> None:
    path = Path(path)
    payload = path.read_bytes()
    if len(payload) != descriptor["size_bytes"]:
        raise QualificationError(f"asset size mismatch: {path.name}")
    if hashlib.sha256(payload).hexdigest() != descriptor["sha256"]:
        raise QualificationError(f"asset SHA256 mismatch: {path.name}")
    git = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
    if git != descriptor["git_blob_sha"]:
        raise QualificationError(f"asset Git blob mismatch: {path.name}")


@dataclass(frozen=True)
class OCBWorld:
    realization_id: str
    source_id: str
    source_xyz: np.ndarray
    master_seed: int
    split: str
    cube: np.ndarray
    pooled: np.ndarray
    times_s: np.ndarray
    wind_indices: np.ndarray
    qualification: DataQualification
    grid: dict
    provenance: dict

    @property
    def run_id(self):
        return self.realization_id

    def query_snapshot(self, frame: int, xy_points) -> np.ndarray:
        return query_snapshot(self, frame, xy_points)


def _frame(world: OCBWorld, frame: int) -> int:
    if isinstance(frame, (bool, np.bool_)) or not isinstance(frame, (int, np.integer)):
        raise QualificationError("frame must be an integer native snapshot index, not seconds")
    if frame < 0 or frame >= len(world.times_s):
        raise IndexError("native snapshot frame outside available data")
    return int(frame)


def query_snapshot(world: OCBWorld, frame: int, xy_points) -> np.ndarray:
    """Return native grid samples at exact cell centres, with no interpolation.

    Geometry is the metadata/probe-contract convention; original extractor
    internals and free-voxel navigation remain unqualified. For original 2x2
    sensor footprints use OCBDataset.query_probes, not this native-cell method.
    """
    frame = _frame(world, frame)
    world.qualification.require("synchronous_spatial", "physical_clock")
    xy = np.asarray(xy_points, dtype=float)
    if xy.ndim != 2 or xy.shape[1] != 2 or not np.isfinite(xy).all():
        raise ValueError("xy_points must be finite [point,2]")
    if not len(xy):
        raise ValueError("at least one query point required")
    origin = np.array([world.grid["min_x"], world.grid["min_y"]])
    index_float = (xy - origin) / world.grid["cell_m"] - 0.5
    indices = np.rint(index_float).astype(np.int64)
    if not np.allclose(index_float, indices, rtol=0, atol=1e-8):
        raise QualificationError(
            "query_snapshot requires native cell centres; use query_probes for original 2x2 pooling"
        )
    if np.any(indices < 0) or np.any(indices >= np.array(world.cube.shape[1:])):
        raise QualificationError("query is outside the exported domain; invalid is not zero gas")
    return np.array(world.cube[frame, indices[:, 0], indices[:, 1]], dtype=float)


class OCBDataset:
    def __init__(self, root, *, manifest_path=None, verify_hashes=True):
        if verify_hashes is not True:
            raise QualificationError("physical-asset hash verification cannot be disabled")
        self.root = Path(root)
        self.manifest = load_manifest(manifest_path)
        self.grid = self.manifest["grid"]
        self.probes = self.manifest["probes"]
        self.probe_ids = tuple(str(p["probe_rank"]) for p in self.probes)
        self.probe_positions_m = np.array([p["center_xyz_m"] for p in self.probes], dtype=float)
        self.probe_positions_m.setflags(write=False)
        self.qualification = DataQualification.from_dict(self.manifest["qualification"])
        self.qualification.require("synchronous_spatial", "physical_clock")
        self.worlds = []
        raw = self.root / "raw" if (self.root / "raw").is_dir() else self.root
        for descriptor in self.manifest["worlds"]:
            arrays = {}
            for kind in ("cube", "pooled"):
                spec = descriptor["files"][kind]
                expected_name = f"{descriptor['run_id']}.{kind}.npy"
                if spec["filename"] != expected_name:
                    raise QualificationError("manifest filename is outside the pinned discovery asset")
                path = raw / spec["filename"]
                verify_file(path, spec)
                arr = np.load(path, allow_pickle=False)
                if list(arr.shape) != spec["shape"] or str(arr.dtype) != spec["dtype"]:
                    raise QualificationError(f"array contract mismatch: {path.name}")
                if not np.isfinite(arr).all() or np.any(arr < 0):
                    raise QualificationError(f"invalid concentrations: {path.name}")
                arr.setflags(write=False)
                arrays[kind] = arr
            cube, pooled = arrays["cube"], arrays["pooled"]
            recomputed = np.stack([
                cube[:, p["native_x0"]:p["native_x1_exclusive"],
                     p["native_y0"]:p["native_y1_exclusive"]].mean(axis=(1, 2), dtype=np.float64)
                for p in self.probes
            ], axis=1)
            if not np.array_equal(recomputed, pooled):
                raise QualificationError("original 2x2 pooling is not bit-exact")
            clock = np.array(descriptor["times_s"], dtype=float)
            if clock.shape != (cube.shape[0],) or not np.isfinite(clock).all() or np.any(np.diff(clock) <= 0):
                raise QualificationError("invalid native physical clock")
            source = np.array(descriptor["source_xyz"], dtype=float)
            wind_index = np.array(descriptor["wind_indices"], dtype=int)
            if source.shape != (3,) or not np.isfinite(source).all() or wind_index.shape != clock.shape:
                raise QualificationError("source/clock/index metadata mismatch")
            for arr in (clock, source, wind_index):
                arr.setflags(write=False)
            self.worlds.append(OCBWorld(
                descriptor["run_id"], descriptor["source_id"], source,
                descriptor["master_seed"], descriptor["split"], cube, pooled, clock,
                wind_index, self.qualification, dict(self.grid),
                {"repository": self.manifest["repository"], "commit": PIN,
                 "files": descriptor["files"], "asset_hashes": descriptor["asset_hashes"],
                 "truth_role": "offline evaluation only"},
            ))
        self.worlds = tuple(self.worlds)
        self.records = self.worlds
        self._by_id = {w.realization_id: w for w in self.worlds}
        if len({w.master_seed for w in self.worlds}) != 8:
            raise QualificationError("each realization needs a distinct original master seed")
        if len({tuple(w.source_xyz) for w in self.worlds}) != 2:
            raise QualificationError("exactly two distinct 3D release locations required")
        if len({tuple(w.times_s) for w in self.worlds}) != 1:
            raise QualificationError("native clock mismatch across the selected context")
        for sid in {w.source_id for w in self.worlds}:
            if [sum(w.source_id == sid and w.split == split for w in self.worlds)
                    for split in ("train", "dev")] != [2, 2]:
                raise QualificationError("require per-source whole-realization 2 train / 2 dev")

    def get_world(self, world: str | OCBWorld) -> OCBWorld:
        if isinstance(world, OCBWorld):
            if self._by_id.get(world.realization_id) is not world:
                raise QualificationError("world is not owned by this verified dataset")
            return world
        return self._by_id[world]

    def split(self, name: str) -> tuple[OCBWorld, ...]:
        if name not in {"train", "dev"}:
            raise QualificationError("only already-open train/dev worlds are authorized")
        return tuple(w for w in self.worlds if w.split == name)

    def query_snapshot(self, world, frame: int, xy_points) -> np.ndarray:
        return query_snapshot(self.get_world(world), frame, xy_points)

    def _probes(self, probe_ids) -> list[int]:
        ids = list(map(str, probe_ids))
        if not ids or len(set(ids)) != len(ids) or any(x not in self.probe_ids for x in ids):
            raise ValueError("provide distinct original House01 probe ranks 1..30")
        return [self.probe_ids.index(x) for x in ids]

    def query_probes(self, world, frame: int, probe_ids) -> np.ndarray:
        world = self.get_world(world)
        frame = _frame(world, frame)
        return np.array(world.pooled[frame, self._probes(probe_ids)], copy=True)

    def to_block(self, world, frame_indices, probe_ids) -> SynchronousBlock:
        world = self.get_world(world)
        frames = [_frame(world, f) for f in frame_indices]
        if not frames or any(b <= a for a, b in zip(frames, frames[1:])):
            raise ValueError("frame_indices must be nonempty, unique and increasing")
        probes = self._probes(probe_ids)
        event = json.dumps([world.realization_id, frames, probes], separators=(",", ":")).encode()
        return SynchronousBlock(
            values=world.pooled[np.ix_(frames, probes)],
            times_s=world.times_s[frames], positions_m=self.probe_positions_m[probes],
            sensor_ids=tuple(self.probe_ids[p] for p in probes),
            qualification=self.qualification,
            block_id=hashlib.sha256(event).hexdigest()[:24],
            realization_id=world.realization_id, units="ppm",
            metadata={"native_frame_indices": frames, "interpolated": False,
                      "readout": "mean of 2x2 native cells at z=0.2m; no sensor lag",
                      "wind_index_only": world.wind_indices[frames].tolist(),
                      "coordinate_status": self.grid["coordinate_status"],
                      "truth_included": False},
        )

    def query_time(self, *args, **kwargs):
        raise QualificationError(
            "no temporal interpolation: select a native integer frame and inspect its actual times_s"
        )

    def local_wind(self, *args, **kwargs):
        raise QualificationError("wind indices and hashes are present, local wind vector bytes are absent")

    def audit(self) -> dict:
        return {
            "status": "PASS_RETROSPECTIVE_SYNC_SPATIAL_ONLY",
            "worlds": len(self.worlds), "sources": len({w.source_id for w in self.worlds}),
            "independent_master_seeds": len({w.master_seed for w in self.worlds}),
            "raw_bytes": sum(spec["size_bytes"] for w in self.manifest["worlds"]
                             for spec in w["files"].values()),
            "train_worlds": [w.realization_id for w in self.split("train")],
            "dev_worlds": [w.realization_id for w in self.split("dev")],
            "native_times_s": self.worlds[0].times_s.tolist(),
            "snapshot_gap_s": [float(np.diff(self.worlds[0].times_s).min()),
                               float(np.diff(self.worlds[0].times_s).max())],
            "pooling_bit_exact": True, "qualification": self.qualification.to_dict(),
            "source_z_difference_m": float(abs(self.worlds[0].source_xyz[2] - self.worlds[-1].source_xyz[2])),
            "source_occupancy_verdict": "HOLD_original_House01_occupancy_bytes_missing",
            "new_worlds_generated": 0, "new_propagation_steps": 0,
            "confirmation_or_H03_targets_read": False,
        }
