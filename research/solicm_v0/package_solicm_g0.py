#!/usr/bin/env python3
"""Create an independently scorable SOLICM-G0 review archive with SHA inventory."""
import hashlib
import io
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "evidence/solicm_v0/g0"
RUNS = Path(r"D:\ZYC\A-gas\_staging\SOLICM_G0_RUNS_20260926")
PACKAGE = Path(r"D:\ZYC\A-gas\_staging\SOLICM_G0_REVIEW_20260926.tar.gz")


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    result = json.loads((OUT / "SOLICM_G0_RESULT.json").read_text())
    independent = json.loads((OUT / "SOLICM_G0_INDEPENDENT_RECOMPUTATION.json").read_text())
    assert result["decision"] == independent["decision"] and independent["verification"] == "PASS"
    assert result["training_runs"] == 96
    include = {}
    for p in OUT.rglob("*"):
        if p.is_file():
            include[f"evidence/solicm_v0/g0/{p.relative_to(OUT).as_posix()}"] = p
    for p in (ROOT / "research/solicm_v0").rglob("*"):
        if p.is_file() and p.suffix != ".pyc":
            include[f"research/solicm_v0/{p.relative_to(ROOT / 'research/solicm_v0').as_posix()}"] = p
    for name in ("CODEX_SOLICM_G0_EXECUTION_PROMPT_20260926.md",):
        p = ROOT / "research/solicm_v0" / name
        assert p in include.values()
    complete = sorted(RUNS.glob("*/COMPLETE.json"))
    assert len(complete) == 96
    for done in complete:
        run = done.parent
        for basename in ("COMPLETE.json", "config.json", "training_history.json", "heldout_logits.npy"):
            p = run / basename
            include[f"runs/{run.name}/{basename}"] = p
        latent = run / "latent_structure.npz"
        if latent.exists():
            include[f"runs/{run.name}/latent_structure.npz"] = latent
    inventory = "".join(f"{sha(p)}  {name}\n" for name, p in sorted(include.items())).encode()
    PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    if PACKAGE.exists():
        raise FileExistsError(PACKAGE)
    with tarfile.open(PACKAGE, "w:gz") as tar:
        for name, p in sorted(include.items()):
            tar.add(p, arcname=name, recursive=False)
        info = tarfile.TarInfo("SHA256SUMS")
        info.size = len(inventory)
        tar.addfile(info, io.BytesIO(inventory))
    print(json.dumps({"package": str(PACKAGE), "bytes": PACKAGE.stat().st_size,
                      "sha256": sha(PACKAGE), "files": len(include) + 1,
                      "decision": result["decision"]}, indent=2))


if __name__ == "__main__":
    main()
