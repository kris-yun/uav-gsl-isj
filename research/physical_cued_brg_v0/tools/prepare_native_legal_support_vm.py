"""Native fixed legality masks. Never reads House03 concentration values."""
import csv,hashlib,json,subprocess,sys
from pathlib import Path
import numpy as np
ROOT=Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927');sys.path.insert(0,str(ROOT))
from pmfs_brg.bank import TemplateBank
BASE=Path('/home/zyc/marked_encounter_pmfs_d0_20260927')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    out=ROOT/'legal_support';out.mkdir(exist_ok=True)
    assert not (out/'LEGAL_SUPPORT_COMPLETE.json').exists()
    provenance=json.loads((BASE/'build_provenance.json').read_text());command=provenance['binaries'][1]['command'].copy()
    command=[str(ROOT/'integration/native_support_probe.cpp') if v==str(BASE/'execution/marked_forward.cpp') else v for v in command]
    binary=Path('/dev/shm/brg_native_support_probe');command[command.index('-o')+1]=str(binary)
    subprocess.run(command,cwd='/home/zyc/native_pmfs_recovery_v1/build/gsl_server',check=True,stdout=(out/'build.log').open('w'),stderr=subprocess.STDOUT)
    inputs=[]
    manifest=json.loads((BASE/'inputs/environment_manifest.json').read_text())
    for e in manifest:
        i=e['environment_index'];m=e['metadata'];start=(-3.17,-1.75) if i==0 else (-.5,-2.5)
        inputs.append((f'env_{i}',m,start,BASE/f'inputs/env_{i}/occupancy.u8',None))
    bank=TemplateBank.load(ROOT/'example_banks/h03_model_only.npz')
    occupancy=np.zeros(bank.n,np.uint8);occupancy[bank.cells]=1;ip=out/'h03_original_occupancy.u8';occupancy.tofile(ip)
    inputs.append(('h03',bank.meta,(2.,0.),ip,bank))
    report={'rule':'unmodified Native PMFSLib::PruneUnreachableCells, scale3, fixed source-blind start',
        'probe_sha256':sha(ROOT/'integration/native_support_probe.cpp'),'binary_sha256':sha(binary),
        'historical_library_sha256':provenance['historical_library_sha256'],'environments':[]}
    for label,m,start,ip,b in inputs:
        result=out/(label+'_occupancy.u8');args=[str(binary),str(m['width']),str(m['height']),str(m['resolution']),str(m['origin_x']),str(m['origin_y']),str(start[0]),str(start[1]),str(ip),str(result)]
        p=subprocess.run(args,text=True,capture_output=True,check=True)
        original=np.fromfile(ip,np.uint8);legal=np.fromfile(result,np.uint8);cells=np.flatnonzero(legal==1)
        removed=np.flatnonzero((original==1)&(legal!=1));assert len(cells)==int(p.stdout.split('NATIVE_LEGAL_COUNT ')[-1].split()[0])
        with (out/(label+'_removed.tsv')).open('w') as f:
            w=csv.writer(f,delimiter='\t');w.writerow(['source_id','grid_index','grid_i','grid_j','x_m','y_m','reason'])
            for c in removed:
                i=int(c)%m['width'];j=int(c)//m['width'];w.writerow([f'pmfs_{i}_{j}',int(c),i,j,m['origin_x']+(i+.5)*m['resolution'],m['origin_y']+(j+.5)*m['resolution'],'Native 8-neighbor propagation from fixed start does not reach this free cell; auxWeight stays -1'])
        if label=='h03':
            actual=json.loads(Path('/home/zyc/brg_closedloop_20260927/native_software_smoke_02_raw/beliefs.jsonl').read_text().splitlines()[0])
            assert cells.tolist()==actual['free_cells'],'probe/actual Native initialization mismatch'
            assert len(cells)==615 and len(removed)==9
            with Path('/home/zyc/aod_house03_f1_full624_20260927/protocol/frozen/HOUSE03_F1_TRUTH_PANEL_12.tsv').open() as f:truth=list(csv.DictReader(f,delimiter='\t'))
            lost=[r['source_id'] for r in truth if int(r['pmfs_i'])+m['width']*int(r['pmfs_j']) not in set(cells.tolist())]
            report['house03_truth_sources_removed']=lost
            if lost:
                (out/'HOLD_TRUTH_SOURCE_REMOVED.json').write_text(json.dumps(report,indent=2)+'\n');raise RuntimeError('STOP truth source removed: '+str(lost))
            take=[b.ids.index(f'pmfs_{int(c)%b.nx}_{int(c)//b.nx}') for c in cells]
            meta={**b.meta,'support_rule':'Native fixed start reachable support','original_model_bank_sha256':sha(ROOT/'example_banks/h03_model_only.npz'),'fixed_start_xy':list(start)}
            masked=TemplateBank(meta,np.array(b.ids)[take],b.xy[take],b.cells[take],b.p[take],b.u[take]);masked.save(out/'h03_native_legal_bank.npz')
            report['h03_bank_sha256']=sha(out/'h03_native_legal_bank.npz');report['h03_bank_id']=masked.fingerprint
        report['environments'].append({'label':label,'original_count':int((original==1).sum()),'native_legal_count':len(cells),'removed_count':len(removed),'fixed_start_xy':list(start),'mask_sha256':sha(result),'removed_tsv_sha256':sha(out/(label+'_removed.tsv')),'metadata':m})
    (out/'LEGAL_SUPPORT_COMPLETE.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
