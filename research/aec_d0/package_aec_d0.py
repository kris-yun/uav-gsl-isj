#!/usr/bin/env python3
"""Compact source-level AEC-D0 review archive with a complete SHA inventory."""
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(r'D:\ZYC\A-gas\_staging\AEC_D0_SELF_COMPETENCE_REVIEW_20260929.zip')
FILES=[
 'research/aec_d0/AEC_D0_PROTOCOL_FREEZE_20260929.md',
 'research/aec_d0/AEC_D0_INFRASTRUCTURE_NOTE_20260929.md',
 'research/aec_d0/AEC_D0_RESULT_20260929.md',
 'research/aec_d0/prepare_routes.py',
 'research/aec_d0/aec_forward_asset_probe.py',
 'research/aec_d0/build_pseudo_vectors_vm.py',
 'research/aec_d0/score_simulator_competence.py',
 'research/aec_d0/evaluate_aec_d0.py',
 'research/aec_d0/package_aec_d0.py',
 'research/ds_pmfs_identity_d1/score_shadow.py',
 'evidence/aec_d0/ROUTE_POSITIONS_ONLY.json',
 'evidence/aec_d0/PSEUDO_VECTORS.npz',
 'evidence/aec_d0/SIMULATOR_ONLY_FREEZE.json',
 'evidence/aec_d0/SIM_COMPETENCE_PER_ROUTE.csv',
 'evidence/aec_d0/SIM_COMPETENCE_PER_SOURCE.csv',
 'evidence/aec_d0/SIM_DELTA_C_PER_SOURCE.csv',
 'evidence/aec_d0/SIM_COMPETENCE_FREEZE.json',
 'evidence/aec_d0/AEC_D0_SOURCE_RESULTS.csv',
 'evidence/aec_d0/AEC_D0_RESULT.json',
 'evidence/aec_d0/DETERMINISTIC_REPEAT.json',
 'evidence/aec_d0/FIRST_OUTPUT_HASHES.json',
 'evidence/aec_d0/assets/env_0_bank.npz',
 'evidence/aec_d0/assets/env_1_bank.npz',
 'evidence/aec_d0/assets/env_2_bank.npz',
 'evidence/aec_d0/assets/env_0_occupancy.u8',
 'evidence/aec_d0/assets/env_1_occupancy.u8',
 'evidence/aec_d0/assets/env_2_occupancy.u8',
 'evidence/ds_pmfs_identity_d1/ASSET_FREEZE.json',
 'evidence/ds_pmfs_identity_d1/COMPACT_EVENTS.json',
 'evidence/r075_relative_action/R075_RESULT.json',
 'evidence/r1_centered_aod/TARGET_METRICS.csv',
 'research/aod_house03_f1_full624_20260927/templates/candidate_path_templates.npz',
 'research/aod_house03_f1_full624_20260927/templates/CANDIDATE_SUPPORT.csv',
 'research/aod_house03_f1_full624_20260927/protocol/frozen/HOUSE03_F1_TRUTH_PANEL_12.tsv',
 'evidence/aod_house03_f1_full624_20260927/TEMPLATE_FREEZE.json',
]


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    assert len(FILES)==len(set(FILES))
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    assert branch=='codex/aec-d0-self-competence-20260929'
    result=json.loads((ROOT/'evidence/aec_d0/AEC_D0_RESULT.json').read_text())
    assert result['decision']=='AEC_D0_NO_CROSS_HOUSE_PREDICTIVE_SIGNAL'
    content={name:(ROOT/name).read_bytes() for name in FILES}
    sums='sha256\tbytes\tpath\n'+''.join(f'{sha(data)}\t{len(data)}\t{name}\n'
        for name,data in sorted(content.items()))
    content['SHA256SUMS.tsv']=sums.encode()
    content['PACKAGE_META.json']=(json.dumps(dict(branch=branch,commit=commit,
        decision=result['decision'],new_gaden_runs=0,new_vgr_runs=0,
        purpose='independent source-level recomputation from compact PMFS pseudo-vectors and prior outcomes'),
        indent=2,sort_keys=True)+'\n').encode()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(OUT,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(content.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,9,29,0,0,0))
            z.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    with zipfile.ZipFile(OUT) as z:
        assert z.testzip() is None
        for name,data in content.items():assert z.read(name)==data
    print(json.dumps(dict(path=str(OUT),bytes=OUT.stat().st_size,sha256=sha(OUT.read_bytes()),
                          branch=branch,commit=commit),indent=2))


if __name__=='__main__':main()
