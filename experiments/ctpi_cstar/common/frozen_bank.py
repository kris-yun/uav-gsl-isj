from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import json
import struct

import numpy as np

MAGIC = b"PFV3STR1"


@dataclass(frozen=True)
class BankCell:
    ordinal: int
    native_cell_index: int
    x: float
    y: float


def load_cell_manifest(root: Path) -> list[BankCell]:
    path = root / "cell_manifest.csv"
    if not path.is_file():
        raise RuntimeError(f"CSTAR_BANK_CELL_MANIFEST_MISSING:{path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        expected = ["stream_ordinal", "native_cell_index", "x", "y"]
        if reader.fieldnames != expected:
            raise RuntimeError(f"CSTAR_BANK_CELL_MANIFEST_HEADER:{reader.fieldnames}")
        rows = list(reader)
    if not rows:
        raise RuntimeError("CSTAR_BANK_CELL_MANIFEST_EMPTY")
    cells: list[BankCell] = []
    seen_native: set[int] = set()
    for expected_ordinal, row in enumerate(rows):
        ordinal = int(row["stream_ordinal"])
        native = int(row["native_cell_index"])
        if ordinal != expected_ordinal:
            raise RuntimeError("CSTAR_BANK_CELL_MANIFEST_ORDER")
        if native in seen_native:
            raise RuntimeError("CSTAR_BANK_CELL_MANIFEST_DUPLICATE_NATIVE")
        seen_native.add(native)
        cells.append(BankCell(ordinal, native, float(row["x"]), float(row["y"])))
    return cells


def world_path(root: Path, member_id: int, carrier_id: str) -> Path:
    if member_id < 0:
        raise ValueError("CSTAR_BANK_MEMBER_NEGATIVE")
    if not carrier_id or "/" in carrier_id or "\\" in carrier_id:
        raise ValueError("CSTAR_BANK_CARRIER_ID")
    return root / "worlds" / f"member_{member_id:02d}" / f"{carrier_id}.bin"


def load_world(root: Path, member_id: int, carrier_id: str, *, mmap: bool = True):
    """Read one CPIR full-grid world as [cell, time] float32.

    The reader is intentionally strict and does not infer missing/ragged lengths.
    It is for offline CSTAR training/evaluation only; it is not a deployment API.
    """
    cells = load_cell_manifest(root)
    path = world_path(root, member_id, carrier_id)
    if not path.is_file():
        raise RuntimeError(f"CSTAR_BANK_WORLD_MISSING:{path}")
    with path.open("rb") as handle:
        header = handle.read(12)
        if len(header) != 12 or header[:8] != MAGIC:
            raise RuntimeError(f"CSTAR_BANK_BAD_MAGIC:{path}")
        count = struct.unpack_from("<I", header, 8)[0]
        if count != len(cells):
            raise RuntimeError(f"CSTAR_BANK_CELL_COUNT:{count}:{len(cells)}")
        raw_lengths = handle.read(4 * count)
        if len(raw_lengths) != 4 * count:
            raise RuntimeError(f"CSTAR_BANK_LENGTH_TABLE:{path}")
        lengths = struct.unpack(f"<{count}I", raw_lengths)
    if len(set(lengths)) != 1:
        raise RuntimeError(f"CSTAR_BANK_RAGGED_TIME:{path}")
    time_count = int(lengths[0])
    if time_count < 1:
        raise RuntimeError(f"CSTAR_BANK_EMPTY_TIME:{path}")
    data_offset = 12 + 4 * count
    expected_bytes = data_offset + 4 * count * time_count
    if path.stat().st_size != expected_bytes:
        raise RuntimeError(
            f"CSTAR_BANK_WORLD_SIZE:{path}:{path.stat().st_size}:{expected_bytes}"
        )
    if mmap:
        values = np.memmap(
            path, dtype="<f4", mode="r", offset=data_offset,
            shape=(count, time_count), order="C"
        )
    else:
        values = np.fromfile(path, dtype="<f4", offset=data_offset).reshape(count, time_count)
    if not np.isfinite(values).all():
        raise RuntimeError(f"CSTAR_BANK_WORLD_NONFINITE:{path}")
    if np.any(values < 0.0):
        raise RuntimeError(f"CSTAR_BANK_WORLD_NEGATIVE:{path}")
    return cells, values


def load_placement_manifest(path: Path) -> list[dict]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if obj.get("contract") != "PF_DEI_V3_REGION_PLACEMENT_V1":
        raise RuntimeError("CSTAR_PLACEMENT_CONTRACT")
    rows: list[dict] = []
    seen: set[tuple[str, str, int, str]] = set()
    for raw in obj.get("rows", []):
        row = {
            "split": str(raw["split"]),
            "house": str(raw["house"]),
            "carrier_id": str(raw["carrier_id"]),
            "member_id": int(raw["member_id"]),
            "x": float(raw["x"]),
            "y": float(raw["y"]),
            "z": float(raw["z"]),
            "transport_seed": int(raw["transport_seed"]),
        }
        key = (row["house"], row["carrier_id"], row["member_id"], row["split"])
        if key in seen:
            raise RuntimeError(f"CSTAR_PLACEMENT_DUPLICATE:{key}")
        seen.add(key)
        rows.append(row)
    if not rows:
        raise RuntimeError("CSTAR_PLACEMENT_EMPTY")
    return rows
