"""Package the conditional HOLD with hashes; no scientific scoring."""
import argparse,hashlib,json,subprocess,zipfile
from pathlib import Path
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--occupancy',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    root=Path(a.root);out=Path(a.out);assert not out.exists()
    files={}
    for p in (root/'software_audit/actual_support_audit_v2').iterdir():
        if p.is_file():files['audit/'+p.name]=p.read_bytes()
    files['inputs/OccupancyGrid3D.csv']=Path(a.occupancy).read_bytes()
    report=json.loads(files['audit/RESULT.json']);assert hashlib.sha256(files['inputs/OccupancyGrid3D.csv']).hexdigest()==report['occupancy_sha256']
    for rel in ['amendment/07_VGR_NATIVE_LEGAL_SUPPORT_CLARIFICATION.md','CLOSED_LOOP_SUPPORT_INFRASTRUCTURE_AUDIT.md',
        'tools/audit_actual_native_exclusions_vm.py','integration/native_support_probe.cpp','tools/prepare_native_legal_support_vm.py',
        'native_baseline_snapshot/src/gsl_server/algorithms/Common/Grid2D.hpp','native_baseline_snapshot/src/gsl_server/algorithms/PMFS/PMFSLib.cpp']:
        files['execution/'+rel]=(root/rel).read_bytes()
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    files['PROVENANCE.json']=(json.dumps({'branch':'research/physical-cued-brg-closedloop-v0-20260927','commit':commit,
        'decision':report['decision'],'formal_campaign_runs':0,'new_gaden_plumes':0,'native_modified_to_rescue_truth':False,
        'frozen_truth_cases_deleted':False,'model_generation_continues':True},indent=2)+'\n').encode()
    inventory=''.join(hashlib.sha256(v).hexdigest()+'  '+k+'\n' for k,v in sorted(files.items()));files['SHA256SUMS']=inventory.encode()
    with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,b in sorted(files.items()):z.writestr(name,b)
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        for line in inventory.splitlines():
            h,name=line.split('  ',1);assert hashlib.sha256(z.read(name)).hexdigest()==h
    print(json.dumps({'path':str(out),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'verified_members':len(files)-1,'commit':commit},indent=2))
if __name__=='__main__':main()
