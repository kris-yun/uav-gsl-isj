"""A common NPZ/long-CSV contract for simultaneous physical sensor blocks.

Missing capabilities stay false. Interpolated samples are never promoted to
native observations. Source truth belongs to the evaluator, not this schema.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import csv
import json
import numpy as np


class QualificationError(ValueError):
    """A requested scientific use is unsupported by the asset."""


@dataclass(frozen=True)
class DataQualification:
    synchronous_spatial: bool = False
    physical_clock: bool = False
    continuous_window: bool = False
    local_wind: bool = False
    independent_realizations: bool = False
    alternative_sources: bool = False
    source_occupancy_validated: bool = False
    native_active_closed_loop: bool = False
    sensor_response_calibrated: bool = False
    native_samples_only: bool = True
    scope: str = "unqualified"
    limitations: tuple[str, ...] = ()

    def __post_init__(self):
        for key, value in asdict(self).items():
            if key not in {"scope", "limitations"} and type(value) is not bool:
                raise QualificationError(f"{key} must be an explicit boolean")
        if self.continuous_window and not self.physical_clock:
            raise QualificationError("continuous_window requires a physical clock")
        object.__setattr__(self, "limitations", tuple(self.limitations))

    def require(self, *capabilities: str) -> None:
        for key in capabilities:
            if key not in self.__dataclass_fields__ or key in {"scope", "limitations"}:
                raise QualificationError(f"unknown capability {key!r}")
            if getattr(self, key) is not True:
                raise QualificationError(
                    f"{key} is not qualified for {self.scope}; "
                    + "; ".join(self.limitations)
                )

    def require_dynamic(self, *, with_wind: bool = True) -> None:
        required = ["synchronous_spatial", "physical_clock",
                    "continuous_window", "native_samples_only"]
        if with_wind:
            required.append("local_wind")
        self.require(*required)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict) -> "DataQualification":
        return cls(**value)


def _array(value, dtype=float):
    a = np.array(value, dtype=dtype, copy=True)
    a.setflags(write=False)
    return a


@dataclass
class SynchronousBlock:
    """values[T,P], native times[T], and positions[P,3] or [T,P,3].

    A long gap can be represented, but does not make a continuous window.
    Missing data are not silently converted into zero concentration.
    """
    values: np.ndarray
    times_s: np.ndarray
    positions_m: np.ndarray
    sensor_ids: tuple[str, ...]
    qualification: DataQualification
    block_id: str
    realization_id: str
    units: str = "ppm"
    local_wind_mps: np.ndarray | None = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        self.values = _array(self.values)
        self.times_s = _array(self.times_s)
        self.positions_m = _array(self.positions_m)
        self.sensor_ids = tuple(str(x) for x in self.sensor_ids)
        if self.values.ndim != 2 or min(self.values.shape) < 1:
            raise ValueError("values must be nonempty [time,sensor]")
        t, p = self.values.shape
        if self.times_s.shape != (t,) or not np.isfinite(self.times_s).all():
            raise ValueError("times_s must contain one finite value per native frame")
        if np.any(np.diff(self.times_s) <= 0):
            raise ValueError("native times must be strictly increasing")
        if self.positions_m.shape not in {(p, 3), (t, p, 3)}:
            raise ValueError("positions_m must be [sensor,3] or [time,sensor,3]")
        if not np.isfinite(self.values).all() or not np.isfinite(self.positions_m).all():
            raise ValueError("invalid values or positions must not masquerade as zeros")
        if len(self.sensor_ids) != p or len(set(self.sensor_ids)) != p:
            raise ValueError("sensor_ids must be unique and match values")
        if not self.block_id or not self.realization_id:
            raise ValueError("block_id and realization_id are required")
        if self.units == "ppm" and np.any(self.values < 0):
            raise ValueError("physical ppm concentrations cannot be negative")
        self.qualification.require("synchronous_spatial")
        if self.qualification.local_wind and self.local_wind_mps is None:
            raise QualificationError("local_wind=True requires actual synchronized vectors")
        if self.local_wind_mps is not None:
            self.local_wind_mps = _array(self.local_wind_mps)
            if self.local_wind_mps.shape != (t, p, 3):
                raise ValueError("local_wind_mps must have shape [time,sensor,3]")
            if not np.isfinite(self.local_wind_mps).all():
                raise ValueError("wind vectors must be finite")
        if self.metadata.get("interpolated", False):
            if self.qualification.native_samples_only or self.qualification.continuous_window:
                raise QualificationError("interpolation cannot be asserted as native continuous data")

    def require_dynamic(self, *, with_wind: bool = True) -> None:
        self.qualification.require_dynamic(with_wind=with_wind)
        if len(self.times_s) < 2:
            raise QualificationError("a single snapshot has no temporal window")

    def _metadata(self) -> dict:
        return {
            "schema_version": "gsl-synchronous-block-1",
            "sensor_ids": list(self.sensor_ids), "block_id": self.block_id,
            "realization_id": self.realization_id, "units": self.units,
            "qualification": self.qualification.to_dict(),
            "metadata": self.metadata,
        }

    def save_npz(self, path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = dict(values=self.values, times_s=self.times_s,
                    positions_m=self.positions_m,
                    schema_json=np.array(json.dumps(self._metadata(), ensure_ascii=False)))
        if self.local_wind_mps is not None:
            data["local_wind_mps"] = self.local_wind_mps
        np.savez_compressed(path, **data)

    @classmethod
    def load_npz(cls, path) -> "SynchronousBlock":
        with np.load(path, allow_pickle=False) as z:
            meta = json.loads(str(z["schema_json"]))
            if meta.pop("schema_version") != "gsl-synchronous-block-1":
                raise ValueError("unsupported synchronous-block schema")
            meta["qualification"] = DataQualification.from_dict(meta["qualification"])
            return cls(values=z["values"], times_s=z["times_s"], positions_m=z["positions_m"],
                       local_wind_mps=z["local_wind_mps"] if "local_wind_mps" in z else None,
                       **meta)

    def save_csv(self, path) -> None:
        """Long CSV plus a required .schema.json sidecar; no inferred seconds."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fields = ["frame", "time_s", "sensor_id", "x_m", "y_m", "z_m", "value"]
        if self.local_wind_mps is not None:
            fields += ["u_mps", "v_mps", "w_mps"]
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for ti, time_s in enumerate(self.times_s):
                pos = self.positions_m if self.positions_m.ndim == 2 else self.positions_m[ti]
                for pi, sid in enumerate(self.sensor_ids):
                    row = dict(frame=ti, time_s=float(time_s), sensor_id=sid,
                               x_m=float(pos[pi, 0]), y_m=float(pos[pi, 1]),
                               z_m=float(pos[pi, 2]), value=float(self.values[ti, pi]))
                    if self.local_wind_mps is not None:
                        row.update(zip(("u_mps", "v_mps", "w_mps"),
                                       map(float, self.local_wind_mps[ti, pi])))
                    writer.writerow(row)
        path.with_suffix(".schema.json").write_text(
            json.dumps(self._metadata(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    @classmethod
    def load_csv(cls, path) -> "SynchronousBlock":
        path = Path(path)
        meta = json.loads(path.with_suffix(".schema.json").read_text(encoding="utf-8"))
        if meta.pop("schema_version") != "gsl-synchronous-block-1":
            raise ValueError("unsupported synchronous-block schema")
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            columns = reader.fieldnames or []
        if not rows or "time_s" not in columns:
            raise QualificationError("explicit timestamps and nonempty observations required")
        ids = meta["sensor_ids"]
        frames = sorted({int(x["frame"]) for x in rows})
        if frames != list(range(len(frames))):
            raise ValueError("CSV frame indices must be contiguous local indices")
        t, p = len(frames), len(ids)
        if len(rows) != t * p:
            raise ValueError("each frame must contain exactly every sensor")
        values = np.empty((t, p)); pos = np.empty((t, p, 3))
        times = np.full(t, np.nan)
        has_wind = all(x in columns for x in ("u_mps", "v_mps", "w_mps"))
        wind = np.empty((t, p, 3)) if has_wind else None
        seen = set()
        for row in rows:
            ti = int(row["frame"]); pi = ids.index(row["sensor_id"])
            if (ti, pi) in seen:
                raise ValueError("duplicate frame/sensor pair")
            seen.add((ti, pi))
            clock = float(row["time_s"])
            if np.isfinite(times[ti]) and times[ti] != clock:
                raise QualificationError("sensors in one frame do not share a physical timestamp")
            times[ti] = clock
            values[ti, pi] = float(row["value"])
            pos[ti, pi] = [float(row[k]) for k in ("x_m", "y_m", "z_m")]
            if has_wind:
                wind[ti, pi] = [float(row[k]) for k in ("u_mps", "v_mps", "w_mps")]
        if np.array_equal(pos, np.broadcast_to(pos[0], pos.shape)):
            pos = pos[0]
        meta["qualification"] = DataQualification.from_dict(meta["qualification"])
        return cls(values=values, times_s=times, positions_m=pos,
                   local_wind_mps=wind, **meta)
