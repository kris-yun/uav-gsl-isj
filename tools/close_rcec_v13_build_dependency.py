#!/usr/bin/env python3
"""Close the RCEC V13 build boundary by disabling the incomplete legacy V12-M path.

This is a build-closure operation only. It must not change ACIT, CREI, TMEM,
PMFS OFF, planner parameters, inverse-transport parameters, or RCEC ablation
logic.

Design principles:
1. Remove the two uncommitted V12-only includes and replace the V12 method body
   with an explicit fail-closed stub.
2. Remove the standalone V12 contract branch.
3. Disable *all syntactic variants* of comparisons against the unavailable V12
   mode. Do not depend on one whitespace/operator layout.
4. Verify the generated source before writing either file. A failure is
   transactional and cannot leave a half-materialized tree.
5. Idempotence is accepted only when the already-materialized source itself
   passes the closure contract.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import re

ROOT = Path(__file__).resolve().parents[1]
CPP = ROOT / "ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp"
PMFS = ROOT / "ros2_package/src/gsl_server/algorithms/PMFS/PMFS.cpp"
CMAKE = ROOT / "ros2_package/CMakeLists.txt"
MARKER = "RCEC_V13_BUILD_CLOSURE_20260826"
DISABLED_MODE_LITERAL = '"__rcec_disabled_legacy_v12__"'
CTT_TARGET = "ctt_trace_bank_builder"

MISSING_INCLUDES = (
    '#include <gsl_server/algorithms/PMFS/internal/RCSDTFEIV12.hpp>\n',
    '#include <gsl_server/algorithms/PMFS/internal/V12ResponseBank.hpp>\n',
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def find_matching_cpp_brace(text: str, opening: int) -> int:
    """Return matching `}` while ignoring comments and quoted literals."""
    if opening < 0 or opening >= len(text) or text[opening] != "{":
        raise ValueError("opening index is not a left brace")
    depth = 0
    i = opening
    state = "code"
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if state == "code":
            if ch == "/" and nxt == "/":
                state = "line_comment"
                i += 2
                continue
            if ch == "/" and nxt == "*":
                state = "block_comment"
                i += 2
                continue
            if ch == '"':
                state = "string"
                i += 1
                continue
            if ch == "'":
                state = "char"
                i += 1
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i
            i += 1
            continue
        if state == "line_comment":
            if ch == "\n":
                state = "code"
            i += 1
            continue
        if state == "block_comment":
            if ch == "*" and nxt == "/":
                state = "code"
                i += 2
            else:
                i += 1
            continue
        if state in ("string", "char"):
            if ch == "\\":
                i += 2
                continue
            if (state == "string" and ch == '"') or (state == "char" and ch == "'"):
                state = "code"
            i += 1
            continue
    raise ValueError("unmatched C++ brace")


def rewrite_mode_comparisons(text: str) -> tuple[str, int]:
    """Disable V12 mode comparisons independent of spacing or operand order.

    Equality with the unavailable mode is always false; inequality is always
    true. Leaving `&& true`, `|| false`, or `if (false)` in generated C++ is
    deliberate: it is syntactically safe, compiler-optimizable, and avoids a
    brittle boolean-expression rewriter.
    """
    rules = (
        (r'\bpfdiMode\s*==\s*"rc_sd_tfei_v12"', "false"),
        (r'"rc_sd_tfei_v12"\s*==\s*\bpfdiMode\b', "false"),
        (r'\bpfdiMode\s*!=\s*"rc_sd_tfei_v12"', "true"),
        (r'"rc_sd_tfei_v12"\s*!=\s*\bpfdiMode\b', "true"),
    )
    total = 0
    for pattern, replacement in rules:
        text, count = re.subn(pattern, replacement, text)
        total += count
    return text, total


def self_test_rewriter() -> None:
    cases = {
        'pfdiMode == "rc_sd_tfei_v12"': "false",
        'pfdiMode != "rc_sd_tfei_v12"': "true",
        'pfdiMode   !=   "rc_sd_tfei_v12"': "true",
        '"rc_sd_tfei_v12" == pfdiMode': "false",
        '"rc_sd_tfei_v12" != pfdiMode': "true",
    }
    for source, expected in cases.items():
        rewritten, count = rewrite_mode_comparisons(source)
        if count != 1 or rewritten != expected:
            raise SystemExit(
                f"internal V12 comparison rewriter self-test failed: {source!r} -> {rewritten!r}"
            )


def remove_legacy_ctt_target(cmake: str) -> tuple[str, int]:
    """Remove the dormant CTT target that still compiles unavailable V12 code."""
    pattern = re.compile(
        r"(?ms)^# Truth-free physical trace-bank builder for the CTT premise gates\. It is not\n"
        r"# installed or launched by ROS and cannot access planner or final-source truth\.\n"
        r"add_executable\(ctt_trace_bank_builder\s+tools/ctt_trace_bank_builder\.cpp\)\n"
        r"ament_target_dependencies\(ctt_trace_bank_builder\n"
        r".*?^\)\n"
        r"target_link_libraries\(ctt_trace_bank_builder\s+PMFS\)\n"
    )
    replacement = (
        "# RCEC_V13_BUILD_CLOSURE_20260826: dormant CTT/V12-only helper target excluded.\n"
    )
    return pattern.subn(replacement, cmake)


def self_test_cmake_closure() -> None:
    fixture = '''before\n# Truth-free physical trace-bank builder for the CTT premise gates. It is not
# installed or launched by ROS and cannot access planner or final-source truth.
add_executable(ctt_trace_bank_builder tools/ctt_trace_bank_builder.cpp)
ament_target_dependencies(ctt_trace_bank_builder
    dep_a
    dep_b
)
target_link_libraries(ctt_trace_bank_builder PMFS)
after\n'''
    rewritten, count = remove_legacy_ctt_target(fixture)
    if count != 1 or CTT_TARGET in rewritten or not rewritten.startswith("before\n") or not rewritten.endswith("after\n"):
        raise SystemExit("internal dormant CTT target closure self-test failed")


def context(text: str, token: str, radius: int = 120) -> str:
    idx = text.find(token)
    if idx < 0:
        return "<not found>"
    lo = max(0, idx - radius)
    hi = min(len(text), idx + len(token) + radius)
    return text[lo:hi].replace("\n", "\\n")


def assert_closed(cpp: str, pmfs: str, cmake: str) -> None:
    forbidden_cpp = (
        "RCSDTFEIV12.hpp",
        "V12ResponseBank.hpp",
        "rc_sd_tfei_v12::",
        "namespace v12 = rc_sd_tfei_v12;",
        'pfdiMode == "rc_sd_tfei_v12"',
        'pfdiMode != "rc_sd_tfei_v12"',
        '"rc_sd_tfei_v12" == pfdiMode',
        '"rc_sd_tfei_v12" != pfdiMode',
        '"rc_sd_tfei_v12"',
    )
    for token in forbidden_cpp:
        if token in cpp:
            raise SystemExit(
                f"build closure failed; forbidden token remains: {token}\n"
                f"context={context(cpp, token)}"
            )
    if "rc_sd_tfei_v12" in pmfs:
        raise SystemExit(
            "build closure failed; PMFS still exposes rc_sd_tfei_v12\n"
            f"context={context(pmfs, 'rc_sd_tfei_v12')}"
        )
    if MARKER not in cpp or MARKER not in pmfs:
        raise SystemExit("build closure marker missing")
    if CTT_TARGET in cmake:
        raise SystemExit("build closure failed; dormant CTT/V12 target remains reachable")
    if MARKER not in cmake:
        raise SystemExit("CMake build closure marker missing")
    for token in ("RCEC_V13_ARM", "v11_stouffer", "crei_latest", "rcec_full"):
        if token not in cpp:
            raise SystemExit(f"RCEC runtime marker disappeared: {token}")
    if "RC-SD-TFEI V12 is unavailable in the RCEC V13 frozen source boundary" not in cpp:
        raise SystemExit("fail-closed legacy V12 stub marker missing")


def main() -> None:
    self_test_rewriter()
    self_test_cmake_closure()
    cpp = CPP.read_text(encoding="utf-8")
    pmfs = PMFS.read_text(encoding="utf-8")
    cmake = CMAKE.read_text(encoding="utf-8")
    cpp_before = sha256(CPP)
    pmfs_before = sha256(PMFS)
    cmake_before = sha256(CMAKE)

    cpp_marked = MARKER in cpp
    pmfs_marked = MARKER in pmfs
    if cpp_marked or pmfs_marked:
        if not (cpp_marked and pmfs_marked):
            raise SystemExit("partial build-closure marker state; refuse to continue")
        assert_closed(cpp, pmfs, cmake)
        print("RCEC_V13_BUILD_CLOSURE=ALREADY_APPLIED_AND_VERIFIED")
        print(f"Simulations.cpp_sha256={cpp_before}")
        print(f"PMFS.cpp_sha256={pmfs_before}")
        print(f"CMakeLists.txt_sha256={cmake_before}")
        return

    # 1. Remove missing legacy-only includes.
    for inc in MISSING_INCLUDES:
        if inc not in cpp:
            raise SystemExit(f"missing expected include anchor: {inc.strip()}")
        cpp = cpp.replace(inc, "", 1)

    # 2. Replace the unavailable legacy implementation with a linkable stub.
    start = cpp.find("    bool Simulations::applyRCSDTFEIV12Main()\n    {")
    end = cpp.find("    bool Simulations::applyTADMPosterior()\n    {", start)
    if start < 0 or end < 0 or end <= start:
        raise SystemExit("could not locate applyRCSDTFEIV12Main function boundary")
    stub = '''    bool Simulations::applyRCSDTFEIV12Main()\n    {\n        // RCEC_V13_BUILD_CLOSURE_20260826: unavailable historical V12-M\n        // dependencies are intentionally excluded from this frozen RCEC build.\n        // Preserve a fail-closed symbol; do not fabricate or copy legacy code.\n        GSL_ERROR("RC-SD-TFEI V12 is unavailable in the RCEC V13 frozen source boundary");\n        return false;\n    }\n\n'''
    cpp = cpp[:start] + stub + cpp[end:]

    # 3. Remove the standalone V12-only contract writer with lexical braces.
    contract_anchor = '        if (pfdiMode == "rc_sd_tfei_v12")\n        {'
    contract_start = cpp.find(contract_anchor)
    if contract_start < 0:
        raise SystemExit("could not locate standalone V12 contract branch")
    opening = cpp.find("{", contract_start, contract_start + len(contract_anchor) + 1)
    if opening < 0:
        raise SystemExit("could not locate V12 contract opening brace")
    try:
        closing = find_matching_cpp_brace(cpp, opening)
    except ValueError as error:
        raise SystemExit(f"could not locate V12 contract closing brace: {error}")
    after = closing + 1
    if after < len(cpp) and cpp[after] == "\r":
        after += 1
    if after < len(cpp) and cpp[after] == "\n":
        after += 1
    cpp = (
        cpp[:contract_start]
        + "        // RCEC_V13_BUILD_CLOSURE_20260826: unavailable V12 contract removed.\n"
        + cpp[after:]
    )

    # 4. Remove the canonical dispatch if present, then disable every remaining
    # comparison syntactic variant in both translation units.
    cpp = cpp.replace(
        '        if (pfdiMode == "rc_sd_tfei_v12")\n            return applyRCSDTFEIV12Main();\n',
        "",
    )
    cpp, cpp_comparisons = rewrite_mode_comparisons(cpp)
    pmfs, pmfs_comparisons = rewrite_mode_comparisons(pmfs)

    # Any residual *quoted* mode literal belongs to disabled legacy metadata or
    # diagnostics. Rename it to a sentinel so the historical mode cannot be
    # selected accidentally and the closure invariant is unambiguous.
    cpp = cpp.replace('"rc_sd_tfei_v12"', DISABLED_MODE_LITERAL)
    pmfs = pmfs.replace('"rc_sd_tfei_v12"', DISABLED_MODE_LITERAL)

    # 5. Mark PMFS build closure without changing active executable behavior.
    marker_anchor = '#include <gsl_server/algorithms/PMFS/PMFS.hpp>\n'
    if marker_anchor not in pmfs:
        raise SystemExit("PMFS include anchor missing")
    pmfs = pmfs.replace(
        marker_anchor,
        marker_anchor + "// RCEC_V13_BUILD_CLOSURE_20260826: incomplete legacy V12-M mode excluded.\n",
        1,
    )

    # 6. Exclude the dormant CTT helper from the default build. Its source is
    # retained as historical evidence, but it depends on the deliberately
    # unavailable V12 headers and is not part of the frozen RCEC runtime.
    cmake, ctt_targets_removed = remove_legacy_ctt_target(cmake)
    if ctt_targets_removed != 1:
        raise SystemExit(
            f"expected exactly one dormant CTT target, removed {ctt_targets_removed}"
        )

    # 7. Transactional postconditions before the only writes.
    assert_closed(cpp, pmfs, cmake)

    CPP.write_text(cpp, encoding="utf-8")
    PMFS.write_text(pmfs, encoding="utf-8")
    CMAKE.write_text(cmake, encoding="utf-8")

    print("RCEC_V13_BUILD_CLOSURE=PASS")
    print(f"v12_comparisons_rewritten_cpp={cpp_comparisons}")
    print(f"v12_comparisons_rewritten_pmfs={pmfs_comparisons}")
    print(f"Simulations.cpp_before_sha256={cpp_before}")
    print(f"Simulations.cpp_after_sha256={sha256(CPP)}")
    print(f"PMFS.cpp_before_sha256={pmfs_before}")
    print(f"PMFS.cpp_after_sha256={sha256(PMFS)}")
    print(f"CMakeLists.txt_before_sha256={cmake_before}")
    print(f"CMakeLists.txt_after_sha256={sha256(CMAKE)}")
    print(f"dormant_ctt_targets_removed={ctt_targets_removed}")
    print("legacy_v12_runtime=FAIL_CLOSED")
    print("rcec_method_equations_changed=false")


if __name__ == "__main__":
    main()
