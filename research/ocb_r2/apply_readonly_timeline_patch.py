#!/usr/bin/env python3
"""Patch only the isolated GADEN copy with a read-only writer timeline."""
from __future__ import annotations

import hashlib
from pathlib import Path

SOURCE = Path('/home/zyc/ocb_r2_seeded_gaden/src/GADEN/gaden_common/third_party/gaden_core/src/RunningSimulation.cpp')
EXPECTED_SHA = '00d0763dc7f369bb716cb8ddf151b3f1112b9b832f137e3cea2d1ee852aabb9a'
OLD_INCLUDE = '#include <fstream>\n'
NEW_INCLUDE = '#include <fstream>\n#include <iomanip>\n'
OLD_COUNTER = '        last_saved_step++;\n'
NEW_COUNTER = '''        // OCB-R2 provenance only: read current writer clock/wind without advancing
        // simulation state or consuming any RNG. The benchmark runs one OpenMP worker.
        {
            std::ofstream timeline(parameters.saveDataDirectory / "RECORD_TIMELINE.tsv", std::ios::app);
            if (last_saved_step == 0)
                timeline << "record_index\\tinternal_simulation_time_s\\twind_index\\n";
            timeline << last_saved_step << '\\t' << std::setprecision(9)
                     << currentTime << '\\t' << windIndex << '\\n';
            GADEN_VERIFY(static_cast<bool>(timeline), "Failed to write OCB-R2 record timeline");
        }
        last_saved_step++;
'''


def main() -> None:
    before = SOURCE.read_bytes()
    if hashlib.sha256(before).hexdigest() != EXPECTED_SHA:
        raise RuntimeError('Refusing patch: isolated source hash differs from frozen source')
    content = before.decode('utf-8')
    if content.count(OLD_INCLUDE) != 1 or content.count(OLD_COUNTER) != 1:
        raise RuntimeError('Source insertion context is not unique')
    content = content.replace(OLD_INCLUDE, NEW_INCLUDE).replace(OLD_COUNTER, NEW_COUNTER)
    SOURCE.write_text(content, encoding='utf-8', newline='\n')
    print(hashlib.sha256(SOURCE.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
