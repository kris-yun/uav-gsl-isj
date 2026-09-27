#!/usr/bin/env python3
"""Infrastructure completeness and exact scientific repeat, no gate changes."""
import argparse,json
from resume_amended_f1_vm import R,A,O,sha,read,write

def extraction():
    f=json.loads((O/'TARGET_DATA_FREEZE.json').read_text())
    assert f['passed'] and len(f['runs'])==96
    ids=[int(s['save_record_id']) for s in read(A/'NATIVE_SNAPSHOT_SCHEDULE_SIGNED.tsv')]
    for r in f['runs']:
        row=r['manifest_row'];d=O/'target_data'/f"source_{row['source_index']}_replica_{row['realization_index']}"
        log=(d/'extraction.log').read_text()
        frames=[int(line.split()[1]) for line in log.splitlines() if line.startswith('FRAME_DONE ')]
        assert frames==ids and 'ITER_MISSING' not in log and 'ENV_READ_FAILED' not in log
        m=json.loads((d/'spatial_metadata.json').read_text())
        assert m['iters']==ids and m['gx']==138 and m['gy']==83 and m['nF']==10
        for n,h in r['artifacts_sha256'].items():assert sha(d/n)==h
    write(O/'EXTRACTION_COMPLETENESS.json',dict(passed=True,targets=96,frames_per_target=10,
          all_frame_loads_confirmed=True,frozen_file_ids_used=True,missing_frames=0))

def repeat():
    x=O/'evaluation';y=O/'evaluation_repeat'
    fx={f.name:sha(f) for f in x.iterdir() if f.is_file()}
    fy={f.name:sha(f) for f in y.iterdir() if f.is_file()}
    assert fx==fy,(fx,fy)
    write(O/'DETERMINISTIC_SCIENTIFIC_REPEAT.json',dict(passed=True,byte_identical=True,
          scientific_files=len(fx),files_sha256=fx,runtime_diagnostics_excluded=True))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['extraction','repeat']);a=p.parse_args()
    {'extraction':extraction,'repeat':repeat}[a.mode]()
