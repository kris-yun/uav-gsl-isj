"""Revalidate archived raw evidence on another checkout without rewriting hashes.

Absolute VM artifact paths are rebased to this checkout; runtime code references
are checked against exact archived source bytes, not Windows CRLF conversions.
This replays the environment validator, not the ROS simulator.
"""
import argparse
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    sys.dont_write_bytecode = True  # verification must not mutate the archive
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    evidence = ROOT / "evidence/cstar_environment_20260906"
    spec = importlib.util.spec_from_file_location("frozen_cstar_env_validator",
        evidence / "source_snapshot/validate_environment_alignment_v2.py")
    env = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(env)
    original_resolve = env.resolve
    old = "/home/zyc/CSTAR_ENV_ALIGN_20260906/"

    def rebase(base, value):
        value = str(value)
        if value.startswith(old):
            relative = value[len(old):]
            if relative.startswith("closed_loop/ctpi/"):
                return evidence / "source_snapshot" / Path(relative).name
            return ROOT / relative
        return original_resolve(base, value)

    env.resolve = rebase
    sys.argv = [str(env.__file__), "--manifest", str(evidence / "CSTAR_ENVIRONMENT_ALIGNMENT_V1.json"),
                "--output", str(args.output.resolve())]
    return env.main()


if __name__ == "__main__":
    raise SystemExit(main())
