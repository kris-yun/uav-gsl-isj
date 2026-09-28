"""Recheck every archived 300 s OPEN realization without opening concentration."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from acquire_archive_host import HOST_ARCHIVE, HOST_RECEIPTS, LOCK_SHA, ROOT, sha


def main() -> None:
    lock = json.loads((ROOT / "FROZEN_RUN_MANIFEST.json").read_text())
    if sha(ROOT / "FROZEN_RUN_MANIFEST.json") != LOCK_SHA:
        raise RuntimeError("frozen manifest drift")
    receipts = sorted(HOST_RECEIPTS.glob("*.json"))
    if len(receipts) != 72 or len(list(HOST_ARCHIVE.glob("*.tar.zst"))) != 72:
        raise RuntimeError("archive/receipt count is not 72")
    counts = Counter()
    splits = Counter()
    total = 0
    archive_hashes = []
    for n, run in enumerate(lock["runs"], 1):
        receipt_path = HOST_RECEIPTS / f"{n:03d}_{run['run_id']}.json"
        receipt = json.loads(receipt_path.read_text())
        archive = HOST_ARCHIVE / f"{run['run_id']}.tar.zst"
        if receipt["ordinal"] != n or receipt["run_id"] != run["run_id"]:
            raise RuntimeError(f"receipt identity drift at {n}")
        if receipt["historical_seed"] != run["historical_seed"] or receipt["native_frames"] != 566:
            raise RuntimeError(f"seed/frame drift at {n}")
        if receipt["frozen_manifest_sha256"] != LOCK_SHA:
            raise RuntimeError(f"manifest reference drift at {n}")
        digest = sha(archive)
        if digest != receipt["archive_sha256"] or archive.stat().st_size != receipt["archive_bytes"]:
            raise RuntimeError(f"archive checksum/size drift at {n}")
        counts[f"{run['house']}/{run['wind']}"] += 1
        splits[run["split"]] += 1
        total += archive.stat().st_size
        archive_hashes.append(f"{digest}  {archive.name}")
    if sorted(counts.values()) != [24, 24, 24]:
        raise RuntimeError("environment count drift")
    inventory = ROOT / "ARCHIVE_SHA256SUMS.txt"
    inventory.write_text("\n".join(archive_hashes) + "\n")
    result = {"status": "BRG_V1_OPEN_CONTINUOUS_72_ARCHIVED",
              "frozen_manifest_sha256": LOCK_SHA,
              "frame_time_map_sha256": sha(ROOT / "RESULT_TIME_MAP_300S.tsv"),
              "archive_sha256_inventory_sha256": sha(inventory),
              "new_gaden_executions": 72, "new_independent_realizations": 0,
              "archive_count": 72, "frames_per_archive": 566,
              "total_native_frames": 72 * 566,
              "total_compressed_bytes": total,
              "environments": dict(sorted(counts.items())),
              "split_counts": dict(sorted(splits.items())),
              "host_archive_directory": str(HOST_ARCHIVE)}
    (ROOT / "ACQUISITION_RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
