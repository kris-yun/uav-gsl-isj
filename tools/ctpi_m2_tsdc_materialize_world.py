#!/usr/bin/env python3
"""TSDC adapter for the already-audited one-world native materializer.

The native physical/sensor implementation remains in ctpi_m2_materialize_world.py.
This adapter changes only the manifest/authorization contract for the frozen TSDC
fresh-confirm experiment and preserves the underlying GADEN execution path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

import ctpi_m2_materialize_world as base

WORLD_CONTRACT = "CTPI_M2_TSDC_FRESH_WORLD_MANIFEST_V0"
PREGEN_CONTRACT = "CTPI_M2_TSDC_PREGEN_AUDIT_V0"
AUDIT_CONTRACT = "CTPI_M2_TSDC_ONE_WORLD_MATERIALIZER_V0"
AUTH_KEY = "CTPI_M2_TSDC_PREGEN"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_bytes(value: dict) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def materialize(args: argparse.Namespace) -> dict:
    manifest = json.loads(args.world_manifest.read_text(encoding="utf-8"))
    if manifest.get("contract") != WORLD_CONTRACT or not manifest.get("pass"):
        raise RuntimeError("TSDC_WORLD_MANIFEST_NOT_PASS")
    world = base.select_world(manifest, args.world_id)

    compat_auth: Path | None = None
    tmp: tempfile.TemporaryDirectory[str] | None = None
    if world["set"] == "SMOKE":
        if not args.allow_disposable_smoke:
            raise RuntimeError("TSDC_WORLD_SMOKE_NOT_AUTHORIZED")
    else:
        if world["set"] != "TSDC_FRESH_CONFIRM":
            raise RuntimeError(f"TSDC_WORLD_SET:{world['set']}")
        if args.authorization is None:
            raise RuntimeError("TSDC_WORLD_FORMAL_DATASET_LOCKED")
        authorization = json.loads(args.authorization.read_text(encoding="utf-8"))
        if (
            authorization.get("contract") != PREGEN_CONTRACT
            or not authorization.get("pass")
            or authorization.get(AUTH_KEY) != "PASS"
        ):
            raise RuntimeError("TSDC_WORLD_PREGEN_AUTHORIZATION")
        tmp = tempfile.TemporaryDirectory(prefix="tsdc_compat_auth_")
        compat_auth = Path(tmp.name) / "compat_authorization.json"
        compat_auth.write_text(
            json.dumps({"CTPI_M2_SOURCE_INTERVENTION_PREGEN": "PASS"}) + "\n",
            encoding="utf-8",
        )

    base.EXPECTED_WORLD_CONTRACT = WORLD_CONTRACT
    base.CONTRACT = AUDIT_CONTRACT
    forwarded = argparse.Namespace(
        world_manifest=args.world_manifest,
        runtime_report=args.runtime_report,
        world_id=args.world_id,
        output=args.output,
        authorization=compat_auth,
        allow_disposable_smoke=args.allow_disposable_smoke,
    )
    try:
        audit = base.materialize(forwarded)
    finally:
        if tmp is not None:
            tmp.cleanup()

    audit.update(
        {
            "contract": AUDIT_CONTRACT,
            "tsdc_adapter": True,
            "tsdc_world_manifest_contract": WORLD_CONTRACT,
            "tsdc_world_manifest_sha256": sha256_file(args.world_manifest),
            "tsdc_pregen_authorization_sha256": (
                sha256_file(args.authorization) if args.authorization is not None else None
            ),
            "upstream_materializer_contract": "CTPI_M2_ONE_WORLD_MATERIALIZER_V1",
            "upstream_materializer_path": str(Path(base.__file__).resolve()),
            "upstream_materializer_sha256": sha256_file(Path(base.__file__).resolve()),
            "verdict": "CTPI_M2_TSDC_WORLD_MATERIALIZATION=PASS",
        }
    )
    (args.output / "WORLD_AUDIT.json").write_bytes(canonical_bytes(audit))
    (args.output / "TSDC_PASS").write_text(
        "CTPI_M2_TSDC_WORLD_MATERIALIZATION=PASS\n", encoding="ascii"
    )
    return audit


def selftest() -> None:
    base.selftest()
    assert WORLD_CONTRACT.endswith("_V0")
    assert PREGEN_CONTRACT.endswith("_V0")
    print("CTPI_M2_TSDC_ONE_WORLD_ADAPTER_SELFTEST=PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--world-manifest", type=Path)
    parser.add_argument("--runtime-report", type=Path)
    parser.add_argument("--world-id")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--allow-disposable-smoke", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    if any(v is None for v in (args.world_manifest, args.runtime_report, args.world_id, args.output)):
        parser.error("materialization arguments are required")
    audit = materialize(args)
    print(audit["verdict"])
    print(f"CTPI_M2_TSDC_WORLD_PAYLOAD_SHA256={audit['payload_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
