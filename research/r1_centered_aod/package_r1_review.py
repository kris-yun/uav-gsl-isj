#!/usr/bin/env python3
"""Package the compact, independently recomputable R1 audit."""
from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(r"D:\ZYC\A-gas\_staging\R1_CENTERED_AOD_REVIEW_20260929.zip")
FILES = [
    "research/r1_centered_aod/R1_PREREG_20260929.md",
    "research/r1_centered_aod/R1_BOOTSTRAP_FREEZE_20260929.json",
    "research/r1_centered_aod/CODEX_EXECUTE_ONLY.txt",
    "research/r1_centered_aod/evaluate_r1.py",
    "research/r1_centered_aod/R1_RESULT_20260929.md",
    "evidence/r1_centered_aod/assets/TARGET_PATHS_12x8x2x10.npy",
    "evidence/r1_centered_aod/R1_RESULT.json",
    "evidence/r1_centered_aod/TARGET_METRICS.csv",
    "evidence/r1_centered_aod/SOURCE_AGGREGATES.csv",
    "evidence/r1_centered_aod/BOOTSTRAP.json",
    "evidence/r1_centered_aod/ASSET_MANIFEST_SHA256.tsv",
    "evidence/r1_centered_aod/DETERMINISTIC_REPEAT.json",
    "research/aod_house03_f1_full624_20260927/templates/candidate_path_templates.npz",
    "research/aod_house03_f1_full624_20260927/templates/CANDIDATE_SUPPORT.csv",
    "research/aod_house03_f1_full624_20260927/protocol/frozen/HOUSE03_F1_TRUTH_PANEL_12.tsv",
    "research/aod_house03_f1_full624_20260927/amplitude_implementation/amplitude_readout.py",
    "research/aod_house03_f1_full624_20260927/execution/score_amended_f1_vm.py",
    "research/aod_house03_f1_full624_20260927/protocol/evaluate_f1_full624.py",
    "evidence/aod_house03_f1_full624_20260927/TEMPLATE_FREEZE.json",
    "evidence/aod_house03_f1_full624_20260927/amended/TARGET_DATA_FREEZE.json",
    "evidence/aod_house03_f1_full624_20260927/amended/F1_PRIMARY_RESULT.json",
    "evidence/aod_house03_f1_full624_20260927/amended/NOMINAL_FULL624_TARGET_METRICS.csv",
    "evidence/aod_house03_f1_full624_20260927/amended/STATE0_FULL624_TARGET_METRICS.csv",
]


def main() -> None:
    assert len(FILES) == len(set(FILES))
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    assert branch == "research/r1-centered-aod-orthogonality-20260929"
    result = json.loads((ROOT / "evidence/r1_centered_aod/R1_RESULT.json").read_text())
    assert result["interpretation_label"] == "R1_CENTERING_NOT_CROSS_HOUSE"
    output_bytes = {}
    for relative in FILES:
        path = ROOT / relative
        assert path.is_file(), relative
        output_bytes[relative] = path.read_bytes()
    sums = "sha256\tbytes\tpath\n" + "".join(
        f"{hashlib.sha256(data).hexdigest()}\t{len(data)}\t{name}\n"
        for name, data in sorted(output_bytes.items()))
    output_bytes["SHA256SUMS.tsv"] = sums.encode()
    output_bytes["PACKAGE_META.json"] = (json.dumps({
        "branch": branch,
        "commit": commit,
        "decision": result["interpretation_label"],
        "contents": "Compact House03 target and full624 template bank; no raw plume archive",
    }, indent=2, sort_keys=True) + "\n").encode()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(output_bytes.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 29, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(OUTPUT) as z:
        assert z.testzip() is None
        for name, data in output_bytes.items():
            assert z.read(name) == data
    print(json.dumps({"path": str(OUTPUT), "bytes": OUTPUT.stat().st_size,
                      "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
                      "commit": commit}, indent=2))


if __name__ == "__main__":
    main()
