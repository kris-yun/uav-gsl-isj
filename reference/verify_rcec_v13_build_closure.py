#!/usr/bin/env python3
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]
CPP = ROOT / 'ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp'
PMFS = ROOT / 'ros2_package/src/gsl_server/algorithms/PMFS/PMFS.cpp'


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    cpp = CPP.read_text(encoding='utf-8')
    pmfs = PMFS.read_text(encoding='utf-8')
    forbidden_cpp = [
        'RCSDTFEIV12.hpp',
        'V12ResponseBank.hpp',
        'rc_sd_tfei_v12::',
        'namespace v12 = rc_sd_tfei_v12;',
    ]
    for token in forbidden_cpp:
        assert token not in cpp, f'legacy V12 compile dependency remains: {token}'
    assert 'RCEC_V13_BUILD_CLOSURE_20260826' in cpp
    assert 'RCEC_V13_BUILD_CLOSURE_20260826' in pmfs
    for token in ('RCEC_V13_ARM', 'v11_stouffer', 'crei_latest', 'rcec_full'):
        assert token in cpp, f'RCEC runtime token missing: {token}'
    assert 'rc_sd_tfei_v12' not in pmfs, 'PMFS still exposes unavailable V12 mode'
    assert 'RC-SD-TFEI V12 is unavailable in the RCEC V13 frozen source boundary' in cpp
    print('RCEC_V13_BUILD_CLOSURE_CONTRACT=PASS')
    print(f'Simulations.cpp_sha256={sha256(CPP)}')
    print(f'PMFS.cpp_sha256={sha256(PMFS)}')


if __name__ == '__main__':
    main()
