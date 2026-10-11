"""Read-only JSON configuration guard for controlled mechanism comparisons.

No subprocesses, network, simulator calls, or writes to protected inputs.
Allowed paths are declared before an experiment, e.g. factors.gas_motion_domain.
Changing a source, observation stream, RNG contract, or scorer requires a separate
explicit experimental factor; such a run must not be labelled native parity.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, dict) and value:
        result = {}
        for key in sorted(value):
            if "." in key:
                raise ValueError("Dots in JSON keys are unsupported")
            result.update(flatten(value[key], f"{prefix}.{key}" if prefix else key))
        return result
    # Arrays are atomic so reordering cannot escape the audit.
    return {prefix: value}


def audit(baseline: dict, run: dict, allowed: list[str]) -> dict:
    b, r = flatten(baseline), flatten(run)
    missing = sorted(set(b) - set(r))
    added = sorted(set(r) - set(b))
    changed = sorted(k for k in set(b) & set(r) if b[k] != r[k])
    bad_allowed = sorted(set(allowed) - set(b))
    forbidden = sorted(set(changed) - set(allowed))
    common = {k: b[k] for k in sorted(b) if k not in allowed}
    digest = hashlib.sha256(json.dumps(common, sort_keys=True, separators=(",", ":"),
                                      ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    ok = not (missing or added or bad_allowed or forbidden)
    return {"status": "PASS" if ok else "FAIL", "common_contract_sha256": digest,
            "declared_change_paths": sorted(set(allowed)), "changed_paths": changed,
            "undeclared_changed_paths": forbidden, "missing_paths": missing,
            "added_paths": added, "invalid_allowed_paths": bad_allowed,
            "scope": "JSON values only; does not certify actual binary execution or data lineage"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("baseline", type=Path)
    ap.add_argument("run", type=Path)
    ap.add_argument("--allow", action="append", default=[])
    args = ap.parse_args()
    result = audit(json.loads(args.baseline.read_text(encoding="utf-8")),
                   json.loads(args.run.read_text(encoding="utf-8")), args.allow)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    if result["status"] != "PASS":
        raise SystemExit(2)

if __name__ == "__main__":
    main()
