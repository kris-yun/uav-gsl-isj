#!/usr/bin/env python3
"""Close the RCEC V13 build boundary by disabling the incomplete legacy V12-M path.

Scientific scope:
- RCEC V13 uses pfdi_mode=me_aci plus RCEC_V13_ARM.
- RC-SD-TFEI V12 is not part of RCEC and its two dependency headers were never
  committed to uav-gsl-isj.
- This script removes only the unreachable V12-M compile dependency and mode
  exposure. It does not change ACIT, CREI, TMEM, PMFS OFF, planner parameters,
  inverse-transport parameters, or RCEC ablation logic.

Run once on top of commit 2a43cfb085b4b23ffd2f0d855de2b443fc906654.
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


def replace_exact(text: str, old: str, new: str, label: str, count: int = 1) -> str:
    n = text.count(old)
    if n != count:
        raise SystemExit(f"{label}: expected {count} occurrence(s), found {n}")
    return text.replace(old, new, count)


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

    # V12 is no longer a supported runtime mode in this build-closed branch.
    cpp = cpp.replace(' || pfdiMode == "rc_sd_tfei_v12"', '')
    cpp = cpp.replace(' && pfdiMode != "rc_sd_tfei_v12"', '')

    # Remove the V12-only contract branch that references namespace constants.
    contract_start = cpp.find('        if (pfdiMode == "rc_sd_tfei_v12")\n        {')
    if contract_start >= 0:
        # Find the matching else that begins the non-V12 contract. We use a
        # stable textual anchor from the frozen source rather than brace-count
        # guessing across arbitrary code.
        else_anchor = '\n        else\n        {\n'
        else_pos = cpp.find(else_anchor, contract_start)
        if else_pos < 0:
            raise SystemExit('V12 contract branch has no expected else anchor')
        # Find the closing brace of the else block by locating the next known
        # function boundary; keep only the existing else body, de-indented by
        # one branch level.
        next_fn = cpp.find('\n    void Simulations::recordPCACIEvent', else_pos)
        if next_fn < 0:
            raise SystemExit('could not locate recordPCACIEvent after contract branch')
        else_body = cpp[else_pos + len(else_anchor):next_fn]
        # Remove the final branch-closing brace immediately before next_fn.
        tail = else_body.rstrip()
        if not tail.endswith('}'):
            raise SystemExit('unexpected configureTADM contract tail')
        tail = tail[:-1].rstrip() + '\n'
        cpp = cpp[:contract_start] + '        // RCEC_V13_BUILD_CLOSURE_20260826: V12 contract branch removed.\n' + tail + cpp[next_fn:]

    # Remove the dispatch to the disabled V12 method.
    cpp = cpp.replace('        if (pfdiMode == "rc_sd_tfei_v12")\n            return applyRCSDTFEIV12Main();\n', '')

    # PMFS parameter parser must reject the unavailable V12 mode too.
    pmfs = pmfs.replace(' && pfdiMode != "rc_sd_tfei_v12"', '')
    pmfs = pmfs.replace(' || pfdiMode == "rc_sd_tfei_v12"', '')
    # Add an auditable marker without changing executable behavior.
    marker_anchor = '#include <gsl_server/algorithms/PMFS/PMFS.hpp>\n'
    if marker_anchor not in pmfs:
        raise SystemExit('PMFS include anchor missing')
    pmfs = pmfs.replace(marker_anchor, marker_anchor + '// RCEC_V13_BUILD_CLOSURE_20260826: incomplete legacy V12-M mode excluded.\n', 1)

    CPP.write_text(cpp, encoding='utf-8')
    PMFS.write_text(pmfs, encoding='utf-8')

    # Hard postconditions.
    for token in ('RCSDTFEIV12.hpp', 'V12ResponseBank.hpp', 'rc_sd_tfei_v12::', 'namespace v12 = rc_sd_tfei_v12;'):
        if token in cpp:
            raise SystemExit(f'build closure failed; forbidden token remains: {token}')
    if 'RCEC_V13_ARM' not in cpp or 'rcec_full' not in cpp or 'crei_latest' not in cpp:
        raise SystemExit('RCEC runtime markers disappeared')
    if 'RCEC_V13_BUILD_CLOSURE_20260826' not in cpp or 'RCEC_V13_BUILD_CLOSURE_20260826' not in pmfs:
        raise SystemExit('build closure marker missing')

    print('RCEC_V13_BUILD_CLOSURE=PASS')
    print(f'Simulations.cpp_before_sha256={cpp_before}')
    print(f'Simulations.cpp_after_sha256={sha256(CPP)}')
    print(f'PMFS.cpp_before_sha256={pmfs_before}')
    print(f'PMFS.cpp_after_sha256={sha256(PMFS)}')
    print('legacy_v12_runtime=FAIL_CLOSED')
    print('rcec_method_equations_changed=false')


if __name__ == '__main__':
    main()
