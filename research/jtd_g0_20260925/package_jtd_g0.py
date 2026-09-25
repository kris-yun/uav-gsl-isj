#!/usr/bin/env python3
"""Package committed JTD-G0 evidence with exact source and git state."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import zipfile
from pathlib import Path


BASE = "e527beea07c33cdbc362d156545409245f029968"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True, errors="replace")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    root = args.repo.resolve()
    evidence = root / "evidence/jtd_g0_20260925"
    if args.out.exists():
        raise RuntimeError(f"review ZIP already exists: {args.out}")
    manifest = evidence / "MANIFEST_SHA256.txt"
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, rel = line.split("  ", 1)
        if sha(evidence / rel) != expected:
            raise RuntimeError(f"evidence hash drift: {rel}")
    files = sorted(p for p in evidence.rglob("*") if p.is_file())
    files += sorted(p for p in (root / "research/jtd_g0_20260925").rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    state = {
        "git_status.txt": git(root, "status", "--short"),
        "git_log_last5.txt": git(root, "log", "-5", "--oneline", "--decorate"),
        "git_diff_from_R0.patch": git(root, "diff", "--binary", BASE + "..HEAD", "--", "research/jtd_g0_20260925"),
        "git_head.txt": git(root, "rev-parse", "HEAD"),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=7) as z:
        for p in files:
            z.write(p, arcname=p.relative_to(root).as_posix())
        for name, content in state.items():
            z.writestr("review_meta/" + name, content)
    digest = sha(args.out)
    args.out.with_suffix(args.out.suffix + ".sha256").write_text(f"{digest}  {args.out.name}\n", encoding="utf-8")
    print(f"archive={args.out}\nbytes={args.out.stat().st_size}\nsha256={digest}")


if __name__ == "__main__":
    main()
