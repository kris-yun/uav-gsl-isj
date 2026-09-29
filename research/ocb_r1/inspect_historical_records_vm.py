#!/usr/bin/env python3
"""Read only historical file names and binary headers; no concentration decoding."""
import csv
import json
import struct
import zlib
from pathlib import Path

BASE = Path('/mnt/hgfs/workspace/GADEN_files/scenarios/House02/House02')
GAS = BASE / 'gas_simulations/3,5-1_slow/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20'
OUT = Path('/home/zyc/ocb_r1_assets/HISTORICAL_FILE_HEADERS.tsv')
IDS = sorted(set(range(5)) | set(range(998, 1003)) | set(range(1995, 2000)) | set(range(100, 551, 50)))


def main():
    names = sorted(p.name for p in GAS.iterdir() if p.name.startswith('iteration_'))
    numbers = {int(name.split('_', 1)[1]) for name in names}
    if len(names) != 2000 or numbers != set(range(2000)):
        raise RuntimeError('historical sequence not 0..1999')
    rows = []
    for i in IDS:
        path = GAS / f'iteration_{i}'
        data = zlib.decompress(path.read_bytes())
        version, = struct.unpack_from('<i', data, 0)
        wind, = struct.unpack_from('<i', data, 132)
        if version != 1 or not (0 <= wind <= 10):
            raise RuntimeError(f'header not consistent with old format at {i}: {version}, {wind}')
        rows.append((i, path.name, len(data), version, wind, path.stat().st_mtime_ns,
                     'no serialized simulation time or integration step in 2021 format'))
    with OUT.open('w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t', lineterminator='\n')
        writer.writerow(('record_id', 'filename', 'uncompressed_bytes', 'format_version',
                         'embedded_wind_index', 'filesystem_mtime_ns', 'notes'))
        writer.writerows(rows)
    print(json.dumps(dict(directory=str(GAS), count=len(names), first=min(numbers),
                          last=max(numbers), inspected=len(rows), header_version=1,
                          embedded_time=False, output=str(OUT))))


if __name__ == '__main__':
    main()
