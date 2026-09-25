#!/usr/bin/env python3
"""Read-only inventory of existing GADEN assets for E0.

This script never invokes GADEN or alters source assets. A row is a physical
plume run (or its compact vector), not an output frame or sensor episode.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


CANONICAL = {
    "House01": ("1,3-2,4_fast", "1,3-2,4_slow", "2,4-1_fast", "2,4-1_slow"),
    "House02": ("3,5-1_fast", "3,5-1_slow", "4,5-3_fast", "4,5-3_slow"),
    "House03": ("1-2,5_fast", "1-2,5_slow", "5-3_fast", "5-3_slow"),
}
BASE = Path("/home/zyc")
SCENARIOS = Path("/mnt/hgfs/workspace/GADEN_files/scenarios")
CONTRACT_SHA = "68121bc9225646e37fcf0233e769b694d9dbaec382723f45b8e80ffc73cea334"
TIMES = (100, 150, 200, 250, 300, 350, 400, 450, 500, 550)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def kv(path: Path) -> dict[str, str]:
    result = {}
    if path.is_file():
        for line in path.read_text(errors="replace").splitlines():
            a, sep, b = line.partition("\t")
            if not sep:
                a, sep, b = line.partition("=")
            if sep:
                result[a] = b
    return result


def xyz(value: str | tuple[float, float, float]) -> tuple[float, float, float]:
    if isinstance(value, str):
        return tuple(float(s) for s in value.split(","))  # type: ignore[return-value]
    return value


def pos_from_name(name: str) -> tuple[int, tuple[float, float, float]]:
    match = re.search(r"gasType_(\d+)_sourcePosition_(-?[\d.]+)_(-?[\d.]+)_(-?[\d.]+)", name)
    if not match:
        raise ValueError(name)
    return int(match[1]), (float(match[2]), float(match[3]), float(match[4]))


def frames(directory: Path) -> tuple[int, int, bool]:
    ids = [int(p.name[10:]) for p in directory.glob("iteration_*") if p.name[10:].isdigit()]
    return len(ids), max(ids, default=-1), all(i in ids for i in TIMES)


def add(rows: list[dict], *, house: str, wind: str, source_id: str, pos, seed,
        family: str, path: Path, form: str, nframes: int, last: int,
        gas: int, time_complete: bool, hash_path: Path | None = None,
        contract: str = "", note: str = "") -> None:
    assert wind in CANONICAL[house], (house, wind, path)
    p = xyz(pos)
    same_geometry = house == "House02"
    same_gas = gas == 10
    if form == "compact_300":
        compatible = same_geometry and same_gas and time_complete and contract == CONTRACT_SHA
        reason = "ready_300" if compatible else "compact_contract_unverified"
    elif form == "cube_10x83x119":
        compatible = same_geometry and same_gas and time_complete
        reason = "pool_existing_cube" if compatible else "geometry_or_gas_mismatch"
    else:
        compatible = same_geometry and same_gas and time_complete
        reason = "extract_existing_raw" if compatible else (
            "short_raw" if not time_complete else "geometry_or_gas_mismatch")
    rows.append(dict(house=house, wind=wind, source_id=source_id,
                     x_m=p[0], y_m=p[1], z_m=p[2], gas_type=gas,
                     seed=str(seed), family=family, form=form, path=str(path),
                     n_iterations=nframes, last_iteration=last,
                     has_D1R_times=int(time_complete), D1R_direct_or_extractable=int(compatible),
                     compatibility_reason=reason, contract_sha256=contract,
                     artifact_sha256=digest(hash_path) if hash_path else "",
                     provenance_note=note))


def scan_modern(rows: list[dict]) -> None:
    roots = [
        (BASE / "cess_d1r_168x16_reference_20260925", "CESS_D1R"),
        (BASE / "r0_stochastic_benchmark_20260924", "R0"),
        (BASE / "lsc_crosswind_d0_128_runs_20260925", "LSC_D0"),
        (BASE / "c0_5_real_gaden_bank_20260923", "M4_C0.5"),
        (BASE / "mz_d3_s1_w2_20260924", "MZ_D3"),
        (BASE / "pasi_d0_s3_w2_20260924", "PASI_D0"),
    ]
    for root, family in roots:
        for cube in sorted(root.rglob("spatial/concentration.npy")):
            run = cube.parent.parent
            m = kv(run / "manifest.tsv")
            if not m:
                raise RuntimeError(f"missing manifest: {run}")
            wind = m.get("wind_name") or m.get("wind")
            if not wind:
                wind = Path(m.get("wind_dir", "")).parents[1].name
            if wind not in CANONICAL["House02"]:
                raise RuntimeError(f"unmapped wind: {run} {wind}")
            source_id = m.get("source_id") or m.get("cell", "").split("_W")[0]
            seed = m.get("rng_seed") or m.get("gaden_rng_seed")
            if not seed:
                raise RuntimeError(f"missing RNG seed: {run}")
            shape = np.load(cube, mmap_mode="r", allow_pickle=False).shape
            if shape != (10, 83, 119):
                raise RuntimeError(f"bad cube shape: {cube} {shape}")
            pooled = run / "pooled.npy"
            if pooled.exists() and np.load(pooled, mmap_mode="r", allow_pickle=False).shape != (10, 30):
                raise RuntimeError(f"bad pooled shape: {pooled}")
            contract = m.get("gate1a_contract_sha256", "")
            if family in ("R0", "M4_C0.5", "MZ_D3", "PASI_D0"):
                # These have the same frozen House02 spatial export; pooling
                # can be applied from the retained raw concentration cube.
                contract = contract or CONTRACT_SHA
            add(rows, house="House02", wind=wind, source_id=source_id,
                pos=m["source_xyz_m"], seed=seed, family=family, path=run,
                form="cube_10x83x119", nframes=10, last=550, gas=10,
                time_complete=True, hash_path=cube, contract=contract,
                note="existing_cube; source manifest and concentration hashed")


def scan_gate(rows: list[dict]) -> None:
    root = BASE / "bigreen_gate1a_exact_20260924"
    source_bank = {}
    with (root / "source_bank.tsv").open(newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            source_bank[row["source_id"]] = (float(row["x_m"]), float(row["y_m"]), float(row["z_m"]))
    assert len(source_bank) == 630
    for seed in (2026092401, 2026092402):
        files = sorted((root / "predictions" / f"seed_{seed}").glob("*.npy"))
        assert len(files) == 630, (seed, len(files))
        for file in files:
            sidecar = json.loads(file.with_suffix(".json").read_text())
            if int(sidecar["prediction_seed"]) != seed or sidecar["source_id"] != file.stem:
                raise RuntimeError(f"sidecar mismatch: {file}")
            if np.load(file, mmap_mode="r", allow_pickle=False).size != 300:
                raise RuntimeError(f"bad compact vector: {file}")
            actual = digest(file)
            if actual != sidecar["prediction_sha256"]:
                raise RuntimeError(f"prediction SHA mismatch: {file}")
            add(rows, house="House02", wind="3,5-1_slow", source_id=file.stem,
                pos=source_bank[file.stem], seed=seed, family="Gate1A_CD", path=file,
                form="compact_300", nframes=10, last=550, gas=10,
                time_complete=True, contract=CONTRACT_SHA, hash_path=None,
                note=f"sidecar_sha256={actual}; raw 3D cube not retained")


def scan_canonical(rows: list[dict]) -> None:
    for house, winds in CANONICAL.items():
        for wind in winds:
            dirs = sorted((SCENARIOS / house / "gas_simulations" / wind).glob("FilamentSimulation_gasType_*"))
            for directory in dirs:
                gas, p = pos_from_name(directory.name)
                n, last, ok = frames(directory)
                sample = directory / "iteration_100"
                add(rows, house=house, wind=wind, source_id=f"canonical_{p}",
                    pos=p, seed=f"unrecorded_canonical_{house}_{wind}", family="canonical_legacy",
                    path=directory, form="raw_gaden", nframes=n, last=last,
                    gas=gas, time_complete=ok, hash_path=sample if sample.exists() else None,
                    note="single unseeded canonical run; cannot prove RNG independence from other banks")


def scan_hcmc(rows: list[dict]) -> None:
    root = BASE / "hcmc_v1_independent_data_20260922"
    for manifest in sorted(root.glob("H0*_R*/generation_manifest.txt")):
        m = kv(manifest)
        directory = next(manifest.parent.glob("FilamentSimulation_gasType_*"))
        gas, p = pos_from_name(directory.name)
        n, last, ok = frames(directory)
        house = m["house"]
        wind = Path(m["wind_directory"]).parents[1].name
        add(rows, house=house, wind=wind, source_id=f"hcmc_{p}", pos=p,
            seed=m["plume_seed"], family="HCMC_independent", path=directory,
            form="raw_gaden", nframes=n, last=last, gas=gas,
            time_complete=ok, hash_path=directory / "iteration_100",
            note=f"generation_manifest_sha256={digest(manifest)}")


def scan_sctt(rows: list[dict]) -> None:
    root = BASE / "SCTT_DISCOVERY_DATASET_V2_20260817"
    manifest = json.loads((root / "collection_manifest.json").read_text())
    sources = {s["source_id"]: (s["x"], s["y"], s["z"]) for s in manifest["sources"]}
    winds = {w["wind_id"]: w["config"] for w in manifest["winds"]}
    for directory in sorted((root / "oracle_frames").iterdir()):
        match = re.fullmatch(r"(S_\w+)__(W_\w+)__seed(\d+)", directory.name)
        if not match:
            continue
        source, wind_id, seed = match.groups()
        n, last, ok = frames(directory)
        add(rows, house="House02", wind=winds[wind_id], source_id=source,
            pos=sources[source], seed=seed, family="SCTT_V2_short",
            path=directory, form="raw_gaden", nframes=n, last=last,
            gas=10, time_complete=ok,
            hash_path=directory / "iteration_0" if (directory / "iteration_0").exists() else None,
            note="150-second/oracle-frame asset; R2 mirror not counted again")


def source_key(row: dict) -> tuple:
    return (row["house"], row["wind"], round(row["x_m"], 4),
            round(row["y_m"], 4), round(row["z_m"], 4), row["gas_type"])


def run_key(row: dict) -> tuple:
    return source_key(row) + (row["seed"],)


def write_tsv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    fields = fields or list(rows[0])
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for scanner in (scan_modern, scan_gate, scan_canonical, scan_hcmc, scan_sctt):
        scanner(rows)
    # The same physical run is represented by c0.5/MZ or target copies. Keep
    # every evidence location, but count one source x wind x seed only once.
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[run_key(row)].append(row)
    for key, group in grouped.items():
        for row in group:
            row["duplicate_evidence_paths"] = len(group) - 1
            row["counted_once_key"] = "|".join(map(str, key))
    write_tsv(out / "E0_ENVIRONMENT_ASSET_INVENTORY.tsv", rows)

    summary = []
    for house, winds in CANONICAL.items():
        for wind in winds:
            selected = [r for r in rows if (r["house"], r["wind"]) == (house, wind)]
            unique: dict[tuple, dict] = {}
            for row in selected:
                key = run_key(row)
                if key not in unique or row["D1R_direct_or_extractable"] > unique[key]["D1R_direct_or_extractable"]:
                    unique[key] = row
            eligible = [r for r in unique.values() if r["D1R_direct_or_extractable"]]
            counts = Counter(source_key(r) for r in eligible)
            positions = {source_key(r)[:-1] for r in unique.values()}
            vals = sorted(counts.values())
            median = (vals[(len(vals)-1)//2] + vals[len(vals)//2]) / 2 if vals else 0
            four = sum(v >= 4 for v in vals)
            summary.append(dict(
                house=house, wind=wind,
                N_existing_source_positions=len(positions),
                N_existing_independent_realizations_total=len(unique),
                N_D1R_compatible_independent_realizations=len(eligible),
                realizations_per_source_min=min(vals, default=0),
                realizations_per_source_median=median,
                realizations_per_source_max=max(vals, default=0),
                N_sources_extractable_under_D1R_operator=len(counts),
                N_sources_with_at_least_4_realizations=four,
                at_least_4_sources_with_4_realizations=four >= 4,
                at_least_6_sources_with_4_realizations=four >= 6,
                environment_benchmark_ready_zero_new_runs=four >= 6,
                excluded_short_run_count=sum(not r["has_D1R_times"] for r in unique.values()),
                gas_type13_count=sum(r["gas_type"] == 13 for r in unique.values()),
                evidence_families=sorted({r["family"] for r in selected}),
            ))
    decision = "E0_PARTIAL_ASSETS_REQUIRE_MINIMAL_FILL_IN"
    report = dict(schema="E0_ENVIRONMENT_LEVEL_ASSET_AUDIT_V1", decision=decision,
                  N_environment_universe=12,
                  N_environment_ready=sum(r["environment_benchmark_ready_zero_new_runs"] for r in summary),
                  N_house_ready=len({r["house"] for r in summary if r["environment_benchmark_ready_zero_new_runs"]}),
                  N_new_plume=0, inventory_rows=len(rows),
                  unique_run_keys=len(grouped), environments=summary)
    (out / "E0_ENVIRONMENT_SUMMARY.json").write_text(json.dumps(report, indent=2) + "\n")
    write_tsv(out / "E0_ENVIRONMENT_SUMMARY.tsv", summary,
              [k for k in summary[0] if k != "evidence_families"])
    ready = [f"{r['house']} / {r['wind']}" for r in summary if r["environment_benchmark_ready_zero_new_runs"]]
    (out / "E0_REUSE_MAP.md").write_text(
        "# E0 reuse map\n\n"
        "The 10x30 operator is the frozen House02 Gate1A/D1R probe contract. "
        "Existing 10x83x119 cubes can be pooled without a plume rerun. "
        "Compact Gate1A C/D vectors are directly usable. Raw House02 gasType10 "
        "runs with all ten iteration indices can be extracted without a plume rerun.\n\n"
        "Ready with >=6 sources and >=4 independent seeds/source:\n\n" +
        "\n".join(f"- {s}" for s in ready) + "\n\n"
        "House01/03 require a separately frozen, geometry-valid probe operator; "
        "the House02 absolute probe coordinates are not a cross-House operator. "
        "gasType13 legacy runs are inventoried but are not pooled into the "
        "gasType10 benchmark. SCTT 150 s oracle-frame runs are kept as short "
        "historical assets, not as D1R 275 s observations. C0.5/MZ duplicate "
        "source/wind/seed keys are counted once. The R2 SCTT mirror and Git "
        "worktree copies are not new plume realizations.\n")
    missing = [f"- {r['house']} / {r['wind']}: {r['N_sources_with_at_least_4_realizations']} "
               "sources currently meet >=4 seeds; "
               f"{r['N_D1R_compatible_independent_realizations']} compatible runs."
               for r in summary if not r["environment_benchmark_ready_zero_new_runs"]]
    (out / "E0_DATA_GAPS.md").write_text(
        "# E0 data gaps\n\nDecision: `" + decision + "`.\n\n"
        "Only House02 has environments with a reusable multi-source, multi-seed "
        "House02 observation contract. No whole House can currently be reserved "
        "as an untouched held-out test with an equivalent multi-source bank. "
        "Do not infer a required fill-in run count before freezing a cross-House "
        "observation design and checking source support in all Houses.\n\n" +
        "\n".join(missing) + "\n")
    provenance = [
        "# E0 provenance and counting rules", "",
        "Read-only scan; no GADEN executable invoked; no source asset modified.",
        "N_environment is 12 canonical House x wind operators, never edge x wind or seed count.",
        "Unique realization key = House, wind, source xyz rounded to 0.1 mm, gas type, RNG seed.",
        "Unrecorded canonical seed is retained as one physical run with weak provenance.",
        "House02 D1R contract SHA256: " + CONTRACT_SHA,
        "10 frozen indices: " + ",".join(map(str, TIMES)), "",
        "## Source files and SHA256", "",
    ]
    for path in (
        BASE / "bigreen_gate1a_exact_20260924/source_bank.tsv",
        BASE / "bigreen_gate1a_exact_20260924/gate1a_contract.json",
        BASE / "cess_d1r_reference_repo_20260925/evidence/causal_emergent_source_scale_v0/d1r/CESS_D1R_ARTIFACT_SHA256.tsv",
        BASE / "lsc_crosswind_d0_repo_20260925/evidence/local_stochastic_confusability_v0/crosswind_d0/LSC_CROSSWIND_D0_ARTIFACT_SHA256.tsv",
        BASE / "SCTT_DISCOVERY_DATASET_V2_20260817/collection_manifest.json",
    ):
        provenance.append(f"- `{path}`: `{digest(path)}`")
    provenance += ["", "Each inventory row also carries its own artifact or sidecar SHA256.",
                   "Raw canonical/HCMC rows hash iteration_100 as a representative content check.",
                   "The E0 result does not claim full byte verification of every raw iteration.", ""]
    (out / "E0_HASHES_PROVENANCE.md").write_text("\n".join(provenance))
    print(json.dumps({"decision": decision, "rows": len(rows),
                      "unique_runs": len(grouped), "ready": ready}, indent=2))


if __name__ == "__main__":
    main()
