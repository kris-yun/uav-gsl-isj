#!/usr/bin/env python3
"""Retain exact historical source and parity records without opening gas data."""
import hashlib
import json
import shutil
from pathlib import Path

R = Path('/home/zyc/aod_house03_f1_full624_20260927')
D0 = Path('/home/zyc/marked_encounter_pmfs_d0_20260927')
G = Path('/home/zyc/hcmc_gaden_seed_build_20260922')


def main():
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    previous = json.loads((D0 / 'build_provenance.json').read_text())
    out = R / 'provenance'
    out.mkdir(exist_ok=False)
    inventory = {}
    for category, hashes in [('kernel', previous['kernel_sha256']),
                             ('execution', previous['patched_source_sha256'])]:
        dest = out / 'historical_pmfs' / category
        dest.mkdir(parents=True)
        for name, expected in hashes.items():
            source = D0 / category / name
            assert sha(source) == expected, name
            target = dest / name
            shutil.copyfile(source, target)
            assert sha(target) == expected
            inventory[str(target.relative_to(out))] = dict(source_path=str(source), sha256=expected)
    for name in ['build_provenance.json', 'NATIVE_PARITY.json']:
        target = out / 'historical_pmfs' / name
        shutil.copyfile(D0 / name, target)
        inventory[str(target.relative_to(out))] = dict(source_path=str(D0 / name), sha256=sha(target))
    sources = [G / 'src/GADEN/gaden_common/third_party/gaden_core/src/RunningSimulation.cpp',
               G / 'src/GADEN/gaden_common/third_party/gaden_core/include/gaden/internal/MathUtils.hpp',
               G / 'src/GADEN/gaden_filament_simulator/src/filament_simulator.cpp',
               G / 'src/GADEN/gaden_filament_simulator/src/filament_simulator.h']
    dest = out / 'historical_gaden'
    dest.mkdir()
    for source in sources:
        target = dest / source.name
        shutil.copyfile(source, target)
        inventory[str(target.relative_to(out))] = dict(source_path=str(source), sha256=sha(target))
    (out / 'SOURCE_PROVENANCE.json').write_text(json.dumps(dict(
        scope='Existing execution sources and parity metadata only; no gas data read',
        sources=inventory), indent=2) + '\n')
    print('EXACT_EXISTING_EXECUTION_SOURCES_RETAINED', len(inventory))


if __name__ == '__main__':
    main()
