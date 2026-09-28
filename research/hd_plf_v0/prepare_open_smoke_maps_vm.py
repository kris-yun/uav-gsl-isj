"""Read saved OPEN PMFS products only; create compact mean maps for software smoke.

No forward simulation or target concentration is opened by this script.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--forward", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--cell-counts", nargs=3, type=int, default=(1102, 1053, 1053))
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    arrays = {}
    inventory = []
    for env in (0, 1, 2):
        for kind in ("u", "rawu"):
            per_source = []
            for source in range(6):
                samples = []
                directory = args.forward / f"env_{env}" / f"source_{source}"
                for state in range(11):
                    for replica in range(1, 9):
                        path = directory / f"state_{state}_replica_{replica}.{kind}.f32"
                        if not path.is_file():
                            raise FileNotFoundError(path)
                        raw = np.fromfile(path, dtype="<f4")
                        if (raw.size != args.cell_counts[env] or
                                not np.isfinite(raw).all() or (raw < 0).any()):
                            raise ValueError(f"invalid saved product: {path}")
                        samples.append(raw.astype(np.float64))
                        inventory.append({"path": str(path), "sha256": sha256(path)})
                per_source.append(np.mean(samples, axis=0))
            arrays[f"env_{env}_{kind}"] = np.stack(per_source)
    assert len(inventory) == 3 * 2 * 6 * 11 * 8
    np.savez_compressed(args.out / "open_mean_maps.npz", **arrays)
    (args.out / "INPUT_SHA256.json").write_text(
        json.dumps({"status": "OPEN_SAVED_FORWARD_READ_ONLY", "files": inventory}, indent=2) + "\n")
    print(json.dumps({"files": len(inventory), "shapes": {k: list(v.shape) for k, v in arrays.items()},
                      "npz_sha256": sha256(args.out / "open_mean_maps.npz")}, indent=2))


if __name__ == "__main__":
    main()
