"""Package one frozen run; remove its VM scratch only after host verification."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from acquire_continuous_vm import load


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def paths(ordinal: int) -> tuple[Path, Path, str]:
    lock = load()
    run = lock["runs"][ordinal - 1]
    root = Path(lock["scratch_root"]).resolve()
    run_id = run["run_id"]
    if not re.fullmatch(r"[A-Za-z0-9_,.\-]+", run_id):
        raise RuntimeError("unsafe run ID")
    source = root / run_id
    archive = root / "archives" / (run_id + ".tar.zst")
    if source.resolve().parent != root or archive.resolve().parent != root / "archives":
        raise RuntimeError("archive/scratch path escaped frozen root")
    return source, archive, run_id


def package(ordinal: int) -> None:
    source, archive, run_id = paths(ordinal)
    if not source.is_dir():
        raise RuntimeError("frozen raw run missing")
    meta = json.loads((source / "RUN_METADATA.json").read_text())
    if meta["ordinal"] != ordinal or meta["run_id"] != run_id:
        raise RuntimeError("run metadata identity mismatch")
    frames = sorted(int(p.name.split("_")[1]) for p in (source / "realization").iterdir()
                    if re.fullmatch(r"iteration_\d+", p.name))
    if frames != list(range(meta["raw_frames"])) or meta["raw_frames"] != 566:
        raise RuntimeError("native frame inventory mismatch")
    if sha(source / "RAW_SHA256.tsv") != meta["raw_inventory_sha256"]:
        raise RuntimeError("raw hash inventory drift")
    archive.parent.mkdir(exist_ok=True)
    if not archive.exists():
        subprocess.run(["tar", "-I", "zstd -3 -T2", "-cf", str(archive),
                        "-C", str(source.parent), run_id], check=True)
    subprocess.run(["zstd", "-t", str(archive)], check=True, stdout=subprocess.DEVNULL)
    print(json.dumps({"status": "VM_ARCHIVE_READY", "ordinal": ordinal, "run_id": run_id,
                      "archive": str(archive), "archive_bytes": archive.stat().st_size,
                      "archive_sha256": sha(archive), "native_frames": len(frames),
                      "raw_inventory_sha256": meta["raw_inventory_sha256"]}), flush=True)


def cleanup(ordinal: int, expected_sha: str) -> None:
    source, archive, run_id = paths(ordinal)
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
        raise RuntimeError("invalid host-verified archive hash")
    if not source.is_dir() or not archive.is_file() or sha(archive) != expected_sha:
        raise RuntimeError("VM archive mismatch; refusing scratch cleanup")
    meta = json.loads((source / "RUN_METADATA.json").read_text())
    if meta["ordinal"] != ordinal or meta["run_id"] != run_id:
        raise RuntimeError("run metadata mismatch; refusing scratch cleanup")
    shutil.rmtree(source)
    archive.unlink()
    print(json.dumps({"status": "VERIFIED_VM_WORK_COPY_REMOVED", "ordinal": ordinal,
                      "run_id": run_id}), flush=True)


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "package":
        package(int(sys.argv[2]))
    elif len(sys.argv) == 4 and sys.argv[1] == "cleanup":
        cleanup(int(sys.argv[2]), sys.argv[3])
    else:
        raise SystemExit("usage: archive_one_vm.py package N | cleanup N host_verified_sha256")


if __name__ == "__main__":
    main()
