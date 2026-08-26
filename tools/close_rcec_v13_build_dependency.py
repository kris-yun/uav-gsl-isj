#!/usr/bin/env python3
"""Close the RCEC V13 build boundary by disabling the incomplete legacy V12-M path.

Scientific scope:
- RCEC V13 uses pfdi_mode=me_aci plus RCEC_V13_ARM.
- RC-SD-TFEI V12 is not part of RCEC and its two dependency headers were never
  committed to uav-gsl-isj.
- This script removes only the unreachable V12-M compile dependency and mode
  exposure. It does not change ACIT, CREI, TMEM, PMFS OFF, planner parameters,
  inverse-transport parameters, or RCEC ablation logic.

The V12 contract in configureTADM() is a standalone `if`, not an if/else pair.
Its exact block boundary is therefore found with a small C++ lexical brace
matcher that ignores braces inside strings, character literals and comments.
"""
from __future__ import annotations

from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]
CPP = ROOT / "ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp"
PMFS = ROOT / "ros2_package/src/gsl_server/algorithms/PMFS/PMFS.cpp"

MISSING_INCLUDES = (
    '#include <gsl_server/algorithms/PMFS/internal/RCSDTFEIV12.hpp>\n',
    '#include <gsl_server/algorithms/PMFS/internal/V12ResponseBank.hpp>\n',
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def find_matching_cpp_brace(text: str, opening: int) -> int:
    """Return the matching `}` for text[opening] == `{`.

    This is deliberately a lexical matcher, not a C++ parser. It is sufficient
    for locating one already-known function-local block while remaining safe
    against the JSON strings in the frozen contract writer.
    """
    if opening < 0 or opening >= len(text) or text[opening] != '{':
        raise ValueError('opening index is not a left brace')

    depth = 0
    i = opening
    state = 'code'
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ''

        if state == 'code':
            if ch == '/' and nxt == '/':
                state = 'line_comment'
                i += 2
                continue
            if ch == '/' and nxt == '*':
                state = 'block_comment'
                i += 2
                continue
            if ch == '"':
                state = 'string'
                i += 1
                continue
            if ch == "'":
                state = 'char'
                i += 1
                continue
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return i
            i += 1
            continue

        if state == 'line_comment':
            if ch == '\n':
                state = 'code'
            i += 1
            continue

        if state == 'block_comment':
            if ch == '*' and nxt == '/':
                state = 'code'
                i += 2
            else:
                i += 1
            continue

        if state in ('string', 'char'):
            if ch == '\\':
                # Skip the escaped byte so escaped quotes cannot terminate the
                # literal. This also safely handles the frozen "\\n" strings.
                i += 2
                continue
            if (state == 'string' and ch == '"') or (state == 'char' and ch == "'"):
                state = 'code'
            i += 1
            continue

    raise ValueError('unmatched C++ brace')


def main() -> None:
    cpp = CPP.read_text(encoding='utf-8')
    pmfs = PMFS.read_text(encoding='utf-8')
    cpp_before = sha256(CPP)
    pmfs_before = sha256(PMFS)

    marker = 'RCEC_V13_BUILD_CLOSURE_20260826'
    if marker in cpp and marker in pmfs:
        print('RCEC_V13_BUILD_CLOSURE=ALREADY_APPLIED')
        print(f'Simulations.cpp_sha256={cpp_before}')
        print(f'PMFS.cpp_sha256={pmfs_before}')
        return

    for inc in MISSING_INCLUDES:
        if inc not in cpp:
            raise SystemExit(f'missing expected include anchor: {inc.strip()}')
        cpp = cpp.replace(inc, '', 1)

    # Disable the entire legacy V12 implementation body while preserving a
    # linkable member function. This avoids fabricating uncommitted headers.
    start = cpp.find('    bool Simulations::applyRCSDTFEIV12Main()\n    {')
    end = cpp.find('    bool Simulations::applyTADMPosterior()\n    {', start)
    if start < 0 or end < 0 or end <= start:
        raise SystemExit('could not locate applyRCSDTFEIV12Main function boundary')
    stub = '''    bool Simulations::applyRCSDTFEIV12Main()\n    {\n        // RCEC_V13_BUILD_CLOSURE_20260826: the historical V12-M source body\n        // referenced RCSDTFEIV12.hpp/V12ResponseBank.hpp, but those files were\n        // never committed to this repository. RCEC V13 does not use V12-M.\n        // Keep an explicit fail-closed stub rather than silently fabricating\n        // legacy behavior or copying untracked workstation files.\n        GSL_ERROR("RC-SD-TFEI V12 is unavailable in the RCEC V13 frozen source boundary");\n        return false;\n    }\n\n'''
    cpp = cpp[:start] + stub + cpp[end:]

    # Remove the standalone V12-only contract writer. The frozen source uses a
    # sequence of independent `if` statements here, so there is intentionally
    # no `else` anchor. Match the exact lexical C++ block instead.
    contract_anchor = '        if (pfdiMode == "rc_sd_tfei_v12")\n        {'
    contract_start = cpp.find(contract_anchor)
    if contract_start < 0:
        raise SystemExit('could not locate standalone V12 contract branch')
    opening = cpp.find('{', contract_start, contract_start + len(contract_anchor) + 1)
    if opening < 0:
        raise SystemExit('could not locate V12 contract opening brace')
    try:
        closing = find_matching_cpp_brace(cpp, opening)
    except ValueError as error:
        raise SystemExit(f'could not locate V12 contract closing brace: {error}')

    after = closing + 1
    if after < len(cpp) and cpp[after] == '\r':
        after += 1
    if after < len(cpp) and cpp[after] == '\n':
        after += 1
    cpp = (
        cpp[:contract_start]
        + '        // RCEC_V13_BUILD_CLOSURE_20260826: standalone V12 contract branch removed.\n'
        + cpp[after:]
    )

    # V12 is no longer a supported runtime mode in this build-closed branch.
    # These replacements cover event recording, source-update setup and
    # persistent-carrier selection without touching the me_aci path.
    cpp = cpp.replace(' || pfdiMode == "rc_sd_tfei_v12"', '')
    cpp = cpp.replace(' && pfdiMode != "rc_sd_tfei_v12"', '')

    # Remove the dispatch to the disabled V12 method.
    cpp = cpp.replace(
        '        if (pfdiMode == "rc_sd_tfei_v12")\n            return applyRCSDTFEIV12Main();\n',
        ''
    )

    # PMFS parameter parser must reject the unavailable V12 mode too.
    pmfs = pmfs.replace(' && pfdiMode != "rc_sd_tfei_v12"', '')
    pmfs = pmfs.replace(' || pfdiMode == "rc_sd_tfei_v12"', '')
    # Add an auditable marker without changing executable behavior.
    marker_anchor = '#include <gsl_server/algorithms/PMFS/PMFS.hpp>\n'
    if marker_anchor not in pmfs:
        raise SystemExit('PMFS include anchor missing')
    pmfs = pmfs.replace(
        marker_anchor,
        marker_anchor + '// RCEC_V13_BUILD_CLOSURE_20260826: incomplete legacy V12-M mode excluded.\n',
        1,
    )

    # Hard postconditions before writing either file: failure cannot leave a
    # half-materialized source tree.
    forbidden_cpp = (
        'RCSDTFEIV12.hpp',
        'V12ResponseBank.hpp',
        'rc_sd_tfei_v12::',
        'namespace v12 = rc_sd_tfei_v12;',
        'pfdiMode == "rc_sd_tfei_v12"',
        'pfdiMode != "rc_sd_tfei_v12"',
    )
    for token in forbidden_cpp:
        if token in cpp:
            raise SystemExit(f'build closure failed; forbidden token remains: {token}')
    if 'rc_sd_tfei_v12' in pmfs:
        raise SystemExit('build closure failed; PMFS still exposes rc_sd_tfei_v12')
    if 'RCEC_V13_ARM' not in cpp or 'rcec_full' not in cpp or 'crei_latest' not in cpp:
        raise SystemExit('RCEC runtime markers disappeared')
    if 'RCEC_V13_BUILD_CLOSURE_20260826' not in cpp or marker not in pmfs:
        raise SystemExit('build closure marker missing')

    CPP.write_text(cpp, encoding='utf-8')
    PMFS.write_text(pmfs, encoding='utf-8')

    print('RCEC_V13_BUILD_CLOSURE=PASS')
    print(f'Simulations.cpp_before_sha256={cpp_before}')
    print(f'Simulations.cpp_after_sha256={sha256(CPP)}')
    print(f'PMFS.cpp_before_sha256={pmfs_before}')
    print(f'PMFS.cpp_after_sha256={sha256(PMFS)}')
    print('legacy_v12_runtime=FAIL_CLOSED')
    print('rcec_method_equations_changed=false')


if __name__ == '__main__':
    main()
