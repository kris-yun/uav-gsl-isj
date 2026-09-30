"""Finish field/semantic checks and human-readable Phase 0 evidence."""
import csv,math
from collections import Counter
from pathlib import Path
from audit_open49 import OUT,ROOT,CACHE,load,dump,sha,rows

def main():
    audit=load(OUT/'OPEN49_TRAINABILITY.json');raw=load(OUT/'OPEN49_RAW_AUDIT.json');checks=[]
    for t in raw['trajectories']:
        p=Path(t['raw_cache']);b=load(p/'runtime_binding.json')['effective_launch_args'];f=load(p/'case_result.json')
        assert t['house']==b['house'] and t['wind']==b['config_id']
        assert all(abs(float(b[k])-truth)<1e-10 for k,truth in zip(['source_x','source_y'],f['truth_xy']))
        maxerr=0.
        for event,block in zip(rows((p/'measurement_events.csv').read_bytes()),rows((p/'measurement_blocks.csv').read_bytes())):
            angle=math.atan2(float(block['wind_direction_used_y']),float(block['wind_direction_used_x']));err=abs(math.atan2(math.sin(angle-float(event['wind_direction'])),math.cos(angle-float(event['wind_direction']))));maxerr=max(maxerr,err)
        assert maxerr<1e-5
        checks.append(dict(case_id=t['case_id'],source_binding_matches=True,wind_world_vector_event_match=True,max_angle_difference_rad=maxerr,source_truth_used_for_labels_only=True))
    dump(OUT/'SOURCE_WIND_SEMANTICS_AUDIT.json',dict(decision='D0B_SOURCE_WIND_SEMANTICS_PASS',trajectories=checks,
        wind='Archived completed event world-frame downwind vector; converted to official robot-local upwind clockwise angle using recorded causal yaw. No /wind_value full-field input.',
        yaw='Nearest causal VGR pose at completed block end; age <=.2s and XY difference <=.001m checked for each event.'))
    with (OUT/'PHYSICAL_RUN_SPLIT.tsv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f,delimiter='\t',lineterminator='\n');writer.writerow(['case_id','house','source_id','wind','physical_seed','split','positive_prefixes','input_sha256','raw_cache'])
        byid={t['case_id']:t for t in raw['trajectories']}
        for t in audit['trajectories']:
            e=byid[t['case_id']];writer.writerow([t[k] for k in ['case_id','house','source_id','wind','physical_seed','split','positive_prefixes']]+[e['input_sha256'],e['raw_cache']])
    lines=['# D0B historical OPEN49 training audit','',f'**Decision: {audit["decision"]}**','',
        '- Exact historical cohort: 49 Native trajectories, 16 House01 + 33 House02; 48 archive hashes and 1 raw-log hash set verified.',
        '- Maps: original occupancy SHA in each historical launch log matches restored 3D occupancy; exact z=0.20m slice and logged uncropped domain reconstructed. No propagated measured-map probabilities are training inputs.',
        '- Pose, completed block time, actual hit/miss and local measured wind are present in all 49. Causal pose age and event/block XY agreement pass.',
        '- Labels use only the archived truth XY, checked against runtime bindings. Labels are excluded from input channels.',
        '- 697 encounter prefixes; 4 official rotations = 2,788 tensor samples. These remain 49 physical trajectories, not 2,788 independent plumes.',
        '- Five trajectories have no encounter and yield no official encounter-index prefix; retained in audit, no synthetic hit/label invented.',
        '- 553 training + 144 validation prefixes. Historical train/dev source split is retained; the extra historical OPEN House02 source joins training. All prefix/rotation samples from a physical trajectory remain in one split.',
        '- Current ocb_r2_cfg00_r01 realization excluded. No confirmation or House03 read. No GADEN, PMFS run or closed loop.',
        '- Exact official label-constructor and incremental-vs-cumulative adapter parity checked on 3 representative prefixes across both Houses.',
        '', '## Scope and limitations','',
        'Historical custom source panel and legacy generator are training data only. The current original-source prospective target uses a different generator and sensor altitude (0.30m vs training 0.20m). This is a transfer headroom test, not a matched benchmark.',
        'Validation contains the two historically held-out House01 sources; there is no House02 validation source in the preserved historical split. Do not imply House02 validation performance.',
        'Original notebooks train 100 epochs. This bounded engineering test freezes 20 epochs, with the same architecture, loss, optimizer, batch size and initial learning rate. The checkpoint is selected solely by validation loss; target error cannot affect any choice.',
        '', '## Execution boundary','', 'Train once from random initialization. Evaluate only the existing D0-Lite event stream, then STOP. No new case, model changes, PMFS-3D, or 64-run campaign.']
    (OUT/'OPEN49_TRAINING_AUDIT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('OPEN49_TRAINABLE: source/wind semantics and grouped manifests finalized')
if __name__=='__main__':main()
