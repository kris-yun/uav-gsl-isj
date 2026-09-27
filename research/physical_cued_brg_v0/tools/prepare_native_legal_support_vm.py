"""Source-blind Native fine occupancy -> scale3 -> unmodified reachability."""
import csv,hashlib,json,subprocess,sys
from pathlib import Path
import numpy as np
ROOT=Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927');sys.path.insert(0,str(ROOT))
from pmfs_brg.bank import TemplateBank
BASE=Path('/home/zyc/marked_encounter_pmfs_d0_20260927')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read_raw(house,m):
    path=Path('/mnt/hgfs/workspace/GADEN_files/scenarios')/house/'OccupancyGrid3D.csv'
    h={};v=[]
    for line in path.read_text().splitlines():
        t=line.split()
        if not t or t==[';']:continue
        if t[0].startswith('#'):h[t[0]]=t[1:]
        else:v.extend(map(int,t))
    nx,ny,nz=map(int,h['#num_cells']);origin=list(map(float,h['#env_min(m)']));dx=float(h['#cell_size(m)'][0]);z=int((.2-origin[2])/dx)
    assert nx//3==m['width'] and ny//3==m['height']
    assert abs(3*dx-m['resolution'])<1e-6 and abs(origin[0]-m['origin_x'])<1e-6 and abs(origin[1]-m['origin_y'])<1e-6
    plane=np.asarray(v,np.uint8).reshape(nz,nx,ny)[z]
    reduced=np.asarray([int(np.all(plane[3*i:3*i+3,3*j:3*j+3]==0)) for j in range(m['height']) for i in range(m['width'])],np.uint8)
    return path,z,reduced

def main():
    out=ROOT/'legal_support_v2';out.mkdir(exist_ok=False)
    assert (ROOT/'amendment/08_SIGNED_NATIVE_SUPPORT_RESOLUTION.json').exists()
    provenance=json.loads((BASE/'build_provenance.json').read_text());command=provenance['binaries'][1]['command'].copy()
    command=[str(ROOT/'integration/native_support_probe.cpp') if v==str(BASE/'execution/marked_forward.cpp') else v for v in command]
    binary=Path('/dev/shm/brg_native_support_probe');command[command.index('-o')+1]=str(binary)
    subprocess.run(command,cwd='/home/zyc/native_pmfs_recovery_v1/build/gsl_server',check=True,stdout=(out/'build.log').open('w'),stderr=subprocess.STDOUT)
    manifest=json.loads((BASE/'inputs/environment_manifest.json').read_text())
    inputs=[(f'env_{e["environment_index"]}',e['metadata'],(-3.17,-1.75) if e['environment_index']==0 else (-.5,-2.5),'House01' if e['environment_index']==0 else 'House02') for e in manifest]
    bank=TemplateBank.load(ROOT/'example_banks/h03_model_only.npz');inputs.append(('h03',bank.meta,(2.,0.),'House03'))
    report={'rule':'actual VGR z=0.20 fine slice, unmodified Native all-nine-free 3x3 reduction, unmodified Native 8-neighbor prune from fixed source-blind start',
        'probe_sha256':sha(ROOT/'integration/native_support_probe.cpp'),'binary_sha256':sha(binary),'historical_library_sha256':provenance['historical_library_sha256'],
        'amendment_sha256':sha(ROOT/'amendment/08_SIGNED_NATIVE_SUPPORT_RESOLUTION.json'),'environments':[]}
    for label,m,start,house in inputs:
        raw,z,reduced=read_raw(house,m);ip=out/(label+'_fine_reduced.u8');reduced.tofile(ip)
        result=out/(label+'_occupancy.u8');args=[str(binary),str(m['width']),str(m['height']),str(m['resolution']),str(m['origin_x']),str(m['origin_y']),str(start[0]),str(start[1]),str(ip),str(result)]
        p=subprocess.run(args,text=True,capture_output=True,check=True);(out/(label+'_prune.log')).write_text(p.stdout+p.stderr)
        legal=np.fromfile(result,np.uint8);cells=np.flatnonzero(legal==1)
        assert len(cells)==int(p.stdout.split('NATIVE_LEGAL_COUNT ')[-1].split()[0])
        assert not np.any((legal==1)&(reduced!=1))
        if label=='h03':
            actual=json.loads(Path('/home/zyc/brg_closedloop_20260927/native_software_smoke_02_raw/beliefs.jsonl').read_text().splitlines()[0])
            assert cells.tolist()==actual['free_cells'] and len(cells)==615
            assert sha(result)=='a44c6323e902b1f6c086ca95046e6eb1ce2d6d38b54ceaae891b0f4d517813e4'
            with Path('/home/zyc/aod_house03_f1_full624_20260927/protocol/frozen/HOUSE03_F1_TRUTH_PANEL_12.tsv').open() as f:truth=list(csv.DictReader(f,delimiter='\t'))
            lost=[r['source_id'] for r in truth if int(r['pmfs_i'])+m['width']*int(r['pmfs_j']) not in set(cells.tolist())]
            assert lost==['pmfs_24_13'];report['house03_truth_sources_outside_support']=lost
            assert set(cells.tolist())<=set(bank.cells.tolist())
            take=[bank.ids.index(f'pmfs_{int(c)%bank.nx}_{int(c)//bank.nx}') for c in cells]
            meta={**bank.meta,'support_rule':report['rule'],'original_model_bank_sha256':sha(ROOT/'example_banks/h03_model_only.npz'),'fixed_start_xy':list(start),'legal_mask_sha256':sha(result)}
            masked=TemplateBank(meta,np.array(bank.ids)[take],bank.xy[take],bank.cells[take],bank.p[take],bank.u[take]);masked.save(out/'h03_native_legal_bank.npz')
            report['h03_bank_sha256']=sha(out/'h03_native_legal_bank.npz');report['h03_bank_id']=masked.fingerprint
        report['environments'].append({'label':label,'house':house,'fine_reduced_free_count':int(reduced.sum()),'native_legal_count':len(cells),'reachability_removed_count':int(reduced.sum()-legal.sum()),'fixed_start_xy':list(start),'mask_sha256':sha(result),'raw_occupancy_sha256':sha(raw),'z_index':z,'metadata':m})
    (out/'LEGAL_MASKS_COMPLETE.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
