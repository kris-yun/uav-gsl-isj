#!/usr/bin/env python3
"""Build the prospective H01 fixed-U transport-coherence premise bank.

All six predictive and seven prospectively frozen observation realizations are
generated at the exact same U0 placement.  The 210 regenerated P0 worlds must
match the historical formal P0 shards byte for byte.  The script never reads a
PMFS posterior, source rank, localization error, or closed-loop output.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

from ctt_h01_wind_bank_io import read_physical, sha256_file


CONTRACT = "CTT_H01_FIXED_U_PROSPECTIVE_K_NATIVE_BANK_V2"
PASS = "CTT_H01_FIXED_U_PROSPECTIVE_K_MATERIALIZATION_PASS"
FORMAL_CONTRACT = "CTT_H01_WIND_CONDITIONED_NATIVE_BANK_V1"
FORMAL_PASS = "CTT_H01_WIND_BANK_MATERIALIZATION_PASS"
PLACEMENT_CONTRACT = "PF_DEI_V3_REGION_PLACEMENT_V1"
CONTEXT_CONTRACT = "CTT_H01_NATIVE_STATIC_WIND_CONTEXTS_V1"
PREREG_CONTRACT = "CTT_M2_FIXED_U_PROSPECTIVE_K_PREMISE_V2"
SOURCE_COUNT = 210
U_MEMBER = 0
CONTEXT = 0
ROUTES = tuple(range(4001, 4006))
PLACEMENT_K_BY_MEMBER = (101, 211, 307, 401, 503, 601, 701, 809)
PREDICTIVE_SEEDS = (101, 211, 307, 401, 503, 601)
OBSERVATION_SEEDS = (
    1413899429, 1029973170, 108828787, 380465369,
    2079440584, 361662980, 1554221114,
)
K_BY_MEMBER = PREDICTIVE_SEEDS + OBSERVATION_SEEDS
PREDICTIVE_MEMBERS = tuple(range(6))
HELD_MEMBERS = tuple(range(6, 13))
GENERATION_ENVIRONMENT = {
    "OMP_NUM_THREADS": "4",
    "OMP_DYNAMIC": "FALSE",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "PYTHONHASHSEED": "0",
}


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=path.name + ".tmp.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as target:
            target.write(value)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def load_json(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError(f"CTT_FIXED_U8_JSON_OBJECT_REQUIRED:{path}")
    return result


def schedule_length(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    if not rows:
        raise ValueError(f"CTT_FIXED_U8_EMPTY_SCHEDULE:{path}")
    return len(rows)


def validate_stream(path: Path, lengths: list[int]) -> None:
    actual = [int(stream.size) for stream in read_physical(path)]
    if actual != lengths:
        raise ValueError(f"CTT_FIXED_U8_STREAM_LENGTH_FAIL:{path}:{actual}:{lengths}")


def read_formal_hashes(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) != 2 or len(fields[1]) != 64 or fields[0] in result:
            raise ValueError(f"CTT_FIXED_U8_BAD_FORMAL_HASH_ROW:{line_number}")
        result[fields[0]] = fields[1].lower()
    return result


def select_u0(payload: dict, source_count: int = SOURCE_COUNT) -> list[dict]:
    if payload.get("contract") != PLACEMENT_CONTRACT:
        raise ValueError("CTT_FIXED_U8_PLACEMENT_CONTRACT_FAIL")
    rows = [
        row for row in payload.get("rows", [])
        if row.get("house") == "H01" and row.get("split") == "train"
    ]
    if len(rows) != source_count * len(PLACEMENT_K_BY_MEMBER):
        raise ValueError(f"CTT_FIXED_U8_PLACEMENT_COVERAGE_FAIL:{len(rows)}")
    by_pair: dict[tuple[str, int], dict] = {}
    for row in rows:
        key = (str(row["carrier_id"]), int(row["member_id"]))
        if key in by_pair:
            raise ValueError(f"CTT_FIXED_U8_DUPLICATE_PLACEMENT:{key}")
        by_pair[key] = row
        member = key[1]
        if member not in range(len(PLACEMENT_K_BY_MEMBER)):
            raise ValueError(f"CTT_FIXED_U8_MEMBER_FAIL:{member}")
        if int(row["transport_seed"]) != PLACEMENT_K_BY_MEMBER[member]:
            raise ValueError(
                f"CTT_FIXED_U8_K_IDENTITY_FAIL:{key}:{row['transport_seed']}"
            )
    carriers = sorted({key[0] for key in by_pair})
    if len(carriers) != source_count:
        raise ValueError(f"CTT_FIXED_U8_SOURCE_COUNT_FAIL:{len(carriers)}")
    for carrier in carriers:
        if {member for cid, member in by_pair if cid == carrier} != set(
            range(len(PLACEMENT_K_BY_MEMBER))
        ):
            raise ValueError(f"CTT_FIXED_U8_MEMBER_COVERAGE_FAIL:{carrier}")
    selected = [by_pair[(carrier, U_MEMBER)] for carrier in carriers]
    for row in selected:
        xyz = [float(row[name]) for name in ("x", "y", "z")]
        if not all(value == value and abs(value) < float("inf") for value in xyz):
            raise ValueError(f"CTT_FIXED_U8_NONFINITE_U0:{row['carrier_id']}")
    return selected


def select_context0(payload: dict) -> dict:
    if payload.get("contract") != CONTEXT_CONTRACT:
        raise ValueError("CTT_FIXED_U8_CONTEXT_CONTRACT_FAIL")
    contexts = payload.get("contexts", [])
    if sorted(int(item["context"]) for item in contexts) != list(range(10)):
        raise ValueError("CTT_FIXED_U8_CONTEXT_INDEX_FAIL")
    chosen = [item for item in contexts if int(item["context"]) == CONTEXT]
    if len(chosen) != 1 or chosen[0].get("split") != "train":
        raise ValueError("CTT_FIXED_U8_CONTEXT0_FAIL")
    return chosen[0]


def build_command(
    native: Path, environment: Path, context: dict, u0: dict,
    transport_member: int, temporary: Path, schedules: list[Path],
) -> list[str]:
    if transport_member not in range(len(K_BY_MEMBER)):
        raise ValueError(f"CTT_FIXED_U8_GENERATED_MEMBER_FAIL:{transport_member}")
    return [
        str(native), str(environment), str(context["wind_dir"]),
        repr(float(u0["x"])), repr(float(u0["y"])), repr(float(u0["z"])),
        str(K_BY_MEMBER[transport_member]), "0.2", str(temporary),
        *(str(path) for path in schedules),
    ]


def run_atomic(command: list[str], temporary: Path, final: Path, lengths: list[int]) -> str:
    if final.is_file():
        validate_stream(final, lengths)
        return "reused"
    final.parent.mkdir(parents=True, exist_ok=True)
    try:
        frozen_environment = os.environ.copy()
        frozen_environment.update(GENERATION_ENVIRONMENT)
        completed = subprocess.run(
            command, text=True, capture_output=True, check=False,
            env=frozen_environment,
        )
        if completed.returncode:
            raise RuntimeError(
                "CTT_FIXED_U8_NATIVE_FAIL\nCOMMAND=" + json.dumps(command)
                + "\nSTDOUT=" + completed.stdout + "\nSTDERR=" + completed.stderr
            )
        validate_stream(temporary, lengths)
        os.replace(temporary, final)
    finally:
        temporary.unlink(missing_ok=True)
    return "generated"


def validate_formal(
    bank: Path, placement: Path, contexts: Path, native: Path,
    environment: Path, schedules: list[Path],
) -> tuple[dict, dict[str, str]]:
    summary_path = bank / "bank_summary.json"
    hashes_path = bank / "FILE_SHA256.tsv"
    for path in [summary_path, hashes_path, placement, contexts, native, environment, *schedules]:
        if not path.is_file():
            raise FileNotFoundError(path)
    summary = load_json(summary_path)
    if not (
        summary.get("contract") == FORMAL_CONTRACT
        and summary.get("verdict") == FORMAL_PASS
        and summary.get("scientific_gate_eligible") is True
        and int(summary.get("carrier_count", -1)) == SOURCE_COUNT
        and int(summary.get("transport_member_count", -1)) == 8
        and list(summary.get("route_seeds", [])) == list(ROUTES)
        and CONTEXT in [int(x) for x in summary.get("contexts", [])]
    ):
        raise ValueError("CTT_FIXED_U8_FORMAL_CONTRACT_FAIL")
    checks = {
        "placement_manifest_sha256": sha256_file(placement),
        "context_manifest_sha256": sha256_file(contexts),
        "native_binary_sha256": sha256_file(native),
        "environment_sha256": sha256_file(environment),
        "schedule_sha256": [sha256_file(path) for path in schedules],
    }
    for name, value in checks.items():
        if summary.get(name) != value:
            raise ValueError(f"CTT_FIXED_U8_FORMAL_HASH_FAIL:{name}")
    return summary, read_formal_hashes(hashes_path)


def validate_preregistration(
    path: Path, bank: Path, placement: Path, contexts: Path, native: Path,
    environment: Path, schedules: list[Path], null_maps: Path,
    seed_provenance: Path,
    native_source: Path, rng_hook_source: Path, rng_math_source: Path,
    running_simulation_source: Path,
) -> dict:
    payload = load_json(path)
    if (
        payload.get("contract") != PREREG_CONTRACT
        or payload.get("status") != "PREREGISTERED_NOT_RUN"
        or payload.get("scope", {}).get("gaden_worlds_to_generate")
        != SOURCE_COUNT * len(K_BY_MEMBER)
        or payload.get("fixed_factorization", {}).get(
            "predictive_transport_seed_map"
        ) != {f"P{index}": seed for index, seed in enumerate(PREDICTIVE_SEEDS)}
        or payload.get("fixed_factorization", {}).get(
            "prospective_observation_transport_seed_map"
        ) != {f"O{index}": seed for index, seed in enumerate(OBSERVATION_SEEDS)}
        or payload.get("fixed_factorization", {}).get("generation_environment")
        != GENERATION_ENVIRONMENT
        or payload.get("closed_loop_authorized") is not False
    ):
        raise ValueError("CTT_FIXED_U8_PREREGISTRATION_CONTRACT_FAIL")
    frozen = payload.get("frozen_inputs_sha256", {})
    actual = {
        "native_gaden_binary": sha256_file(native),
        "placement_manifest": sha256_file(placement),
        "wind_context_manifest": sha256_file(contexts),
        "existing_bank_summary": sha256_file(bank / "bank_summary.json"),
        "existing_bank_file_sha_manifest": sha256_file(bank / "FILE_SHA256.tsv"),
        "environment": sha256_file(environment),
        "route_4004": sha256_file(schedules[3]),
        "route_4005": sha256_file(schedules[4]),
        "native_generator_source": sha256_file(native_source),
        "rng_hook_source": sha256_file(rng_hook_source),
        "rng_math_source": sha256_file(rng_math_source),
        "running_simulation_source": sha256_file(running_simulation_source),
    }
    for name, digest in actual.items():
        if frozen.get(name) != digest:
            raise ValueError(f"CTT_FIXED_U8_PREREGISTERED_HASH_FAIL:{name}")
    if sha256_file(null_maps) != payload.get("destruction_controls", {}).get(
        "null_map_sha256"
    ):
        raise ValueError("CTT_FIXED_U8_NULL_MAP_HASH_FAIL")
    if sha256_file(seed_provenance) != payload.get("fixed_factorization", {}).get(
        "prospective_seed_provenance_sha256"
    ):
        raise ValueError("CTT_FIXED_U8_SEED_PROVENANCE_HASH_FAIL")
    return payload


def generated_path(root: Path, carrier: str, member: int) -> Path:
    return (
        root / "context_00" / "fixed_u_member_00"
        / f"transport_member_{member:02d}_seed_{K_BY_MEMBER[member]}" / f"{carrier}.bin"
    )


def validate_completed(root: Path, hashes: dict) -> dict:
    summary_path = root / "bank_summary.json"
    manifest_path = root / "FACTORIAL_SHA256.tsv"
    if not summary_path.is_file() or not manifest_path.is_file():
        raise ValueError(f"CTT_FIXED_U8_NONRESUMABLE_OUTPUT:{root}")
    summary = load_json(summary_path)
    if not (
        summary.get("contract") == CONTRACT and summary.get("verdict") == PASS
        and summary.get("input_hashes") == hashes
        and int(summary.get("materialized_file_count", -1))
        == SOURCE_COUNT * len(K_BY_MEMBER)
        and int(summary.get("factorial_shard_count", -1))
        == SOURCE_COUNT * len(K_BY_MEMBER)
    ):
        raise ValueError("CTT_FIXED_U8_COMPLETED_CONTRACT_FAIL")
    rows = list(csv.DictReader(manifest_path.open(newline="", encoding="utf-8"), delimiter="\t"))
    generated = rows
    if len(rows) != SOURCE_COUNT * len(K_BY_MEMBER):
        raise ValueError("CTT_FIXED_U8_COMPLETED_MANIFEST_COVERAGE_FAIL")
    for row in generated:
        path = root / row["relative_path"]
        if not path.is_file() or sha256_file(path) != row["sha256"]:
            raise ValueError(f"CTT_FIXED_U8_COMPLETED_HASH_FAIL:{row['carrier_id']}:{row['transport_member']}")
    return summary


def selftest() -> None:
    rows = []
    for carrier in range(2):
        for member, seed in enumerate(PLACEMENT_K_BY_MEMBER):
            rows.append({
                "house": "H01", "split": "train", "carrier_id": f"c{carrier:03d}",
                "member_id": member, "transport_seed": seed,
                "x": carrier + member / 10, "y": 2.0, "z": 0.5,
            })
    u0 = select_u0({"contract": PLACEMENT_CONTRACT, "rows": rows}, 2)
    assert len(u0) == 2 and float(u0[0]["x"]) == 0.0
    schedules = [Path(f"route_{route}.csv") for route in ROUTES]
    for member in range(len(K_BY_MEMBER)):
        command = build_command(
            Path("native"), Path("environment"), {"wind_dir": "wind"}, u0[0],
            member, Path("temporary"), schedules,
        )
        assert command[3:6] == ["0.0", "2.0", "0.5"]
        assert command[6] == str(K_BY_MEMBER[member])
    # A changed diagonal placement must not affect the selected U0 command.
    rows[-1]["x"] = 999.0
    assert float(select_u0({"contract": PLACEMENT_CONTRACT, "rows": rows}, 2)[0]["x"]) == 0.0
    print("CTT_H01_FIXED_U_TRANSPORT_GATE_MATERIALIZER_SELFTEST=PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--formal-bank", type=Path)
    parser.add_argument("--placement-manifest", type=Path)
    parser.add_argument("--context-manifest", type=Path)
    parser.add_argument("--preregistration", type=Path)
    parser.add_argument("--null-maps", type=Path)
    parser.add_argument("--seed-provenance", type=Path)
    parser.add_argument("--native-binary", type=Path)
    parser.add_argument("--native-source", type=Path)
    parser.add_argument("--rng-hook-source", type=Path)
    parser.add_argument("--rng-math-source", type=Path)
    parser.add_argument("--running-simulation-source", type=Path)
    parser.add_argument("--environment", type=Path)
    parser.add_argument("--schedule-root", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    names = (
        "formal_bank", "placement_manifest", "context_manifest", "preregistration",
        "null_maps", "seed_provenance", "native_binary", "native_source", "rng_hook_source",
        "rng_math_source", "running_simulation_source", "environment",
        "schedule_root", "output_root",
    )
    missing = [name for name in names if getattr(args, name) is None]
    if missing:
        raise SystemExit("CTT_FIXED_U8_MISSING_ARGUMENTS:" + ",".join(missing))
    if not 1 <= args.workers <= 12:
        raise SystemExit("CTT_FIXED_U8_WORKERS_MUST_BE_1_TO_12")

    schedules = [
        args.schedule_root / "H01" / "reserved" / f"trajectory_seed_{route}.csv"
        for route in ROUTES
    ]
    lengths = [schedule_length(path) for path in schedules]
    formal_summary, formal_hashes = validate_formal(
        args.formal_bank, args.placement_manifest, args.context_manifest,
        args.native_binary, args.environment, schedules,
    )
    validate_preregistration(
        args.preregistration, args.formal_bank, args.placement_manifest,
        args.context_manifest, args.native_binary, args.environment, schedules,
        args.null_maps, args.seed_provenance, args.native_source, args.rng_hook_source,
        args.rng_math_source, args.running_simulation_source,
    )
    u0_rows = select_u0(load_json(args.placement_manifest))
    context = select_context0(load_json(args.context_manifest))
    original = Path(context["original_path"])
    if not original.is_file() or sha256_file(original) != context["payload_sha256"]:
        raise SystemExit("CTT_FIXED_U8_CONTEXT0_PAYLOAD_HASH_FAIL")
    for slot in range(11):
        linked = Path(context["wind_dir"]) / f"wind_iteration_{slot}"
        if not linked.is_file() or sha256_file(linked) != context["payload_sha256"]:
            raise SystemExit(f"CTT_FIXED_U8_CONTEXT0_SLOT_HASH_FAIL:{slot}")

    input_hashes = {
        "formal_bank_summary": sha256_file(args.formal_bank / "bank_summary.json"),
        "formal_bank_file_manifest": sha256_file(args.formal_bank / "FILE_SHA256.tsv"),
        "placement_manifest": sha256_file(args.placement_manifest),
        "context_manifest": sha256_file(args.context_manifest),
        "preregistration": sha256_file(args.preregistration),
        "null_maps": sha256_file(args.null_maps),
        "seed_provenance": sha256_file(args.seed_provenance),
        "native_binary": sha256_file(args.native_binary),
        "native_source": sha256_file(args.native_source),
        "rng_hook_source": sha256_file(args.rng_hook_source),
        "rng_math_source": sha256_file(args.rng_math_source),
        "running_simulation_source": sha256_file(args.running_simulation_source),
        "environment": sha256_file(args.environment),
        "schedules": [sha256_file(path) for path in schedules],
    }
    output = args.output_root
    if output.exists() and not (output / "IN_PROGRESS").is_file():
        summary = validate_completed(output, input_hashes)
        print("CTT_H01_FIXED_U_EIGHT_K_ALREADY_PASS " + json.dumps(summary, sort_keys=True))
        return 0
    output.mkdir(parents=True, exist_ok=True)
    atomic_text(output / "IN_PROGRESS", CONTRACT + "\n")

    k0_records: dict[str, tuple[str, str]] = {}
    for row in u0_rows:
        carrier = str(row["carrier_id"])
        relative = f"context_00/member_00/{carrier}.bin"
        path = args.formal_bank / relative
        expected = formal_hashes.get(relative)
        if expected is None:
            raise SystemExit(f"CTT_FIXED_U8_K0_MANIFEST_MISSING:{relative}")
        validate_stream(path, lengths)
        actual = sha256_file(path)
        if actual != expected:
            raise SystemExit(f"CTT_FIXED_U8_K0_HASH_FAIL:{relative}")
        k0_records[carrier] = (relative, actual)

    def generate(row: dict, member: int) -> str:
        carrier = str(row["carrier_id"])
        final = generated_path(output, carrier, member)
        temporary = final.with_suffix(f".tmp.{os.getpid()}")
        command = build_command(
            args.native_binary, args.environment, context, row, member, temporary, schedules
        )
        return run_atomic(command, temporary, final, lengths)

    counts = {"generated": 0, "reused": 0}
    started = time.monotonic()
    def execute_tasks(tasks: list[tuple[dict, int]], label: str) -> None:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(generate, row, member) for row, member in tasks]
            for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
                counts[future.result()] += 1
                if index % 100 == 0 or index == len(futures):
                    print(
                        f"CTT_FIXED_U8_{label}_PROGRESS={index}/{len(futures)} "
                        f"generated={counts['generated']} reused={counts['reused']}",
                        flush=True,
                    )

    # Fail early if the current runtime environment is not byte-identical to
    # the frozen bank before spending time on any new realization.
    execute_tasks([(row, 0) for row in u0_rows], "K0_SENTINEL")
    for row in u0_rows:
        carrier = str(row["carrier_id"])
        sentinel = generated_path(output, carrier, 0)
        if sha256_file(sentinel) != k0_records[carrier][1]:
            raise SystemExit(f"CTT_FIXED_U8_K0_SENTINEL_MISMATCH:{carrier}")
    print(f"CTT_FIXED_U8_K0_SENTINEL_PASS={SOURCE_COUNT}/{SOURCE_COUNT}", flush=True)

    execute_tasks(
        [
            (row, member)
            for row in u0_rows
            for member in range(1, len(K_BY_MEMBER))
        ],
        "PROSPECTIVE",
    )

    manifest_rows = []
    changed = 0
    k0_sentinel_matches = 0
    for row in u0_rows:
        carrier = str(row["carrier_id"])
        k0_relative, k0_sha = k0_records[carrier]
        for member, seed in enumerate(K_BY_MEMBER):
            path = generated_path(output, carrier, member)
            validate_stream(path, lengths)
            root_name = "prospective_fixed_u"
            relative = path.relative_to(output).as_posix()
            digest = sha256_file(path)
            if member == 0:
                if digest != k0_sha:
                    raise SystemExit(f"CTT_FIXED_U8_K0_SENTINEL_MISMATCH:{carrier}")
                k0_sentinel_matches += 1
            else:
                changed += int(digest != k0_sha)
            manifest_rows.append({
                "carrier_id": carrier,
                "x": repr(float(row["x"])), "y": repr(float(row["y"])), "z": repr(float(row["z"])),
                "u_member": str(U_MEMBER), "transport_member": str(member),
                "transport_seed": str(seed), "storage_root": root_name,
                "relative_path": relative, "sha256": digest,
            })
    if k0_sentinel_matches != SOURCE_COUNT:
        raise SystemExit(
            f"CTT_FIXED_U8_K0_SENTINEL_COVERAGE:{k0_sentinel_matches}:{SOURCE_COUNT}"
        )
    if changed == 0:
        raise SystemExit("CTT_FIXED_U8_TRANSPORT_DEGENERATE_ALL_BYTES_EQUAL")
    fields = list(manifest_rows[0])
    lines = ["\t".join(fields)] + [
        "\t".join(row[field] for field in fields) for row in manifest_rows
    ]
    atomic_text(output / "FACTORIAL_SHA256.tsv", "\n".join(lines) + "\n")
    summary = {
        "contract": CONTRACT, "verdict": PASS,
        "scientific_scope": "fixed_U0_6_predictive_to_7_prospective_observation_K",
        "closed_loop_authorized": False, "context": CONTEXT, "u_member": U_MEMBER,
        "transport_seed_by_member": list(K_BY_MEMBER),
        "predictive_members": list(PREDICTIVE_MEMBERS), "held_members": list(HELD_MEMBERS),
        "carrier_count": SOURCE_COUNT,
        "materialized_file_count": SOURCE_COUNT * len(K_BY_MEMBER),
        "factorial_shard_count": SOURCE_COUNT * len(K_BY_MEMBER),
        "route_seeds": list(ROUTES),
        "generated": counts["generated"], "reused": counts["reused"],
        "k0_sentinel_byte_identical_count": k0_sentinel_matches,
        "non_k0_byte_different_from_k0_count": changed,
        "generation_environment": GENERATION_ENVIRONMENT,
        "elapsed_s": time.monotonic() - started, "input_hashes": input_hashes,
        "formal_bank_contract": formal_summary["contract"],
        "materializer_sha256": sha256_file(Path(__file__)),
        "factorial_manifest_sha256": sha256_file(output / "FACTORIAL_SHA256.tsv"),
    }
    atomic_text(output / "bank_summary.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (output / "IN_PROGRESS").unlink()
    print(PASS + " " + json.dumps(summary, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
