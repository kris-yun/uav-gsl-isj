#!/usr/bin/env python3
import csv, hashlib, json, shlex, shutil, subprocess, zipfile
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

R=Path('/home/zyc/marked_encounter_pmfs_d0_20260927')
C=R/'execution'; P=R/'protocol'; I=R/'inputs'; K=R/'kernel'; B=R/'build'
N=Path('/home/zyc/native_pmfs_recovery_v1')
SRC=N/'src/gsl_server/src/gsl_server'
OLD=Path('/home/zyc/wind_alignment_d0_20260926')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v): p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def flags(target):
    result=[]
    for line in (N/f'build/gsl_server/CMakeFiles/{target}.dir/flags.make').read_text().splitlines():
        if line.startswith(('CXX_DEFINES =','CXX_INCLUDES =','CXX_FLAGS =')):
            result+=shlex.split(line.split('=',1)[1])
    return result
def compile_cmd(cmd):
    with (R/'build.log').open('a') as f:
        f.write(shlex.join(cmd)+'\n');f.flush()
        subprocess.run(cmd,cwd=N/'build/gsl_server',stdout=f,stderr=subprocess.STDOUT,check=True)

I.mkdir(exist_ok=True); K.mkdir(exist_ok=True); B.mkdir(exist_ok=True)
for line in (P/'SHA256SUMS.txt').read_text().splitlines():
    h,name=line.split('  ',1); assert sha(P/name)==h,name
Q=Path('/home/zyc/qa_pmfs_crossenv_f1_20260926')
assert sha(Q/'QA_PMFS_CROSSENV_F1_REVIEW_20260926.zip')=='20dd51ce283449e68b644245dec9306005de73a0e0f27504ebc95bbe186b1d35'
for name in ('E1_HOUSE_PROBE_CONTRACTS.tsv','E1_HOUSE_SOURCE_PANELS.tsv','JTD_E2_FRESH_TARGET_10x30.npy','JTD_E2_FRESH_TARGET_MANIFEST.tsv','JTD_E2_REFERENCE_12x10x30.npy'):
    assert sha(P/name)==sha(Q/'historical'/name),name

provenance=json.loads((OLD/'build_provenance.json').read_text())
for path,h in provenance['historical_library_sha256'].items(): assert sha(path)==h,path
for name,path in {'Simulations.cpp':SRC/'algorithms/PMFS/internal/Simulations.cpp',
                  'Simulations.hpp':SRC/'algorithms/PMFS/internal/Simulations.hpp',
                  'Math.cpp':SRC/'algorithms/Common/Utils/Math.cpp',
                  'Math.hpp':SRC/'algorithms/Common/Utils/Math.hpp'}.items():
    assert sha(path)==sha(OLD/'review_evidence/historical_kernel'/name),name
    shutil.copyfile(path,K/name)
shutil.copyfile(SRC/'algorithms/PMFS/internal/Settings.hpp',K/'Settings.hpp')
shutil.copyfile(SRC/'algorithms/Common/Grid2D.hpp',K/'Grid2D.hpp')
shutil.copyfile(OLD/'code/historical_replay.cpp',K/'historical_replay.cpp')
assert sha(K/'historical_replay.cpp')==provenance['historical_replay_source_sha256']
dump(I/'historical_build_provenance.json',provenance)

panel=list(csv.DictReader((P/'E1_HOUSE_SOURCE_PANELS.tsv').open(),delimiter='\t'))
probes=list(csv.DictReader((P/'E1_HOUSE_PROBE_CONTRACTS.tsv').open(),delimiter='\t'))
envs=[('House01','1,3-2,4_fast'),('House02','3,5-1_slow'),('House02','4,5-3_slow')]
base=Path('/home/zyc/rmfe_v2_runtime_causal_20260814_a2_002/house123/runs_2seed_v4')
asset=[]; manifests=[]
for e,(house,wind) in enumerate(envs):
    folder=I/f'env_{e}';folder.mkdir(exist_ok=True)
    id0='H01_air_seed' if house=='House01' else 'H02_seed'
    geometry=base/(id0+'0')/'off/geometry_export'
    meta=json.loads((geometry/'pruned_meta.json').read_text())
    a=geometry/'pruned_occupancy.bin'; a1=base/(id0+'1')/'off/geometry_export/pruned_occupancy.bin'
    assert sha(a)==sha(a1)
    shutil.copyfile(a,folder/'occupancy.u8'); shutil.copyfile(geometry/'pruned_meta.json',folder/'meta.json')
    nav=np.fromfile(a,np.uint8); assert nav.size==meta['width']*meta['height']; assert set(nav)<= {0,1}
    free=np.flatnonzero(nav==1); ij=np.array([free%meta['width'],free//meta['width']]).T
    q=np.array([meta['origin_x'],meta['origin_y']])+ (ij+.5)*meta['resolution']
    q=np.c_[q,np.full(len(q),.2)]
    ss=[r for r in panel if r['house']==house]; pp=[r for r in probes if r['house']==house]
    assert len(ss)==6 and len(pp)==30
    with (folder/'sources.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['source_index','source_id','x','y','z','pair_id'])
        for si,row in enumerate(ss):
            x,y,z=map(float,(row['x_m'],row['y_m'],row['z_m']))
            assert z==.2
            ix=int(np.floor((x-meta['origin_x'])/meta['resolution'])); iy=int(np.floor((y-meta['origin_y'])/meta['resolution']))
            assert (ix,iy)==(int(row['pmfs_i']),int(row['pmfs_j'])) and nav[ix+iy*meta['width']]==1
            assert abs(x-(meta['origin_x']+(ix+.5)*meta['resolution']))<1e-5
            assert abs(y-(meta['origin_y']+(iy+.5)*meta['resolution']))<1e-5
            w.writerow([si,row['source_id'],x,y,z,row['pair_id']])
    with (folder/'probes.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['probe_rank','cell_index','x','y'])
        for row in pp:
            x,y=map(float,(row['center_x_m'],row['center_y_m']))
            ix=int(np.floor((x-meta['origin_x'])/meta['resolution']));iy=int(np.floor((y-meta['origin_y'])/meta['resolution']))
            index=ix+iy*meta['width']; assert 0<=index<len(nav) and nav[index]==1
            w.writerow([row['probe_rank'],index,x,y])
    with (folder/'meta.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['width','height','resolution','origin_x','origin_y']);w.writerow([meta[k] for k in ['width','height','resolution','origin_x','origin_y']])
    scen=Path('/mnt/hgfs/workspace/GADEN_files/scenarios')/house
    for st in range(11):
        path=scen/'wind_simulations'/wind/f'{wind}_{st}.csv'
        if not path.exists(): path=scen/house/'wind_simulations'/wind/f'{wind}_{st}.csv'
        windcsv=np.loadtxt(path,delimiter=',',skiprows=1)
        assert windcsv.ndim==2 and windcsv.shape[1]==6 and np.isfinite(windcsv).all()
        pos=windcsv[:,3:6]; tree=cKDTree(pos); dist,two=tree.query(q,k=2)
        near=two[:,0].copy()
        # Resolve possible ties by exact historical first-row numpy argmin.
        for index in np.flatnonzero(np.abs(dist[:,1]-dist[:,0])<=1e-12):
            near[index]=int(np.argmin(np.sum((pos-q[index])**2,axis=1)))
        uv=windcsv[near,:2].astype(np.float32)
        target=folder/f'wind_{st}.csv'
        with target.open('w',newline='') as f:
            w=csv.writer(f);w.writerow(['cell_index','u','v']);w.writerows((int(idx),repr(float(u)),repr(float(v))) for idx,(u,v) in zip(free,uv))
        asset.append({'environment_index':e,'house':house,'wind':wind,'state':st,'asset_path':str(path),'asset_bytes':path.stat().st_size,'asset_sha256':sha(path),'export_sha256':sha(target),'nearest_rows':near.tolist(),'z_m':.2,'wind_semantics':'map Cartesian downwind'})
    manifests.append({'environment_index':e,'house':house,'wind':wind,'metadata':meta,'free_cells':len(free),'occupancy_sha256':sha(a),'source_count':6,'probe_count':30,'state_count':11,'replica_seeds':list(range(1,9))})
    print('ENVIRONMENT_ASSETS_VERIFIED',e,house,wind,flush=True)
dump(I/'wind_manifest.json',asset);dump(I/'environment_manifest.json',manifests)
dump(I/'asset_audit.json',{'passed':True,'supplied_package_files_verified':13,'historical_QA_review_sha256':sha(Q/'QA_PMFS_CROSSENV_F1_REVIEW_20260926.zip'),'environment_count':3,'wind_state_files':33,'source_units':18,'target_values_read':False,'protected_assets_read':False,'kernel_hashes':{p.name:sha(p) for p in K.iterdir()}})

# One optional observer pointer; original simulation and RNG calls untouched.
s=(K/'Simulations.cpp').read_text()
needle='    static thread_local Utils::PrecalculatedGaussian<2500> gaussian;'
assert s.count(needle)==1
s=s.replace(needle,needle+'\n    static thread_local std::vector<float>* markedMultiplicityCounter = nullptr;\n    void setMarkedMultiplicityCounter(std::vector<float>* counter) { markedMultiplicityCounter = counter; }')
needle='                // mark as updated so it doesn\'t count multiple filaments in the same timestep'
assert s.count(needle)==1
s=s.replace(needle,'                if (markedMultiplicityCounter) (*markedMultiplicityCounter)[index] += 1.0f;\n'+needle)
needle='                hitMap[i] = hitMap[i] / timesteps;'
assert s.count(needle)==1
s=s.replace(needle,'            {\n'+needle+'\n                if (markedMultiplicityCounter) (*markedMultiplicityCounter)[i] /= timesteps;\n            }')
(C/'Simulations_marked.cpp').write_text(s)
math=(K/'Math.cpp').read_text().replace('    static thread_local std::minstd_rand0 RNGengine;', '    static thread_local std::minstd_rand0 RNGengine;\n    void seedMarkedReplay(unsigned int seed) { RNGengine.seed(seed); }')
(C/'Math_seeded.cpp').write_text(math)
h=(K/'historical_replay.cpp').read_text()
h=h.replace('namespace fs = std::filesystem;', 'namespace GSL::PMFS_internal { void setMarkedMultiplicityCounter(std::vector<float>*); }\nnamespace fs = std::filesystem;')
needle='        std::vector<float> map(measuredHitProb.data.size(), 0.0f);'
assert h.count(needle)==1
h=h.replace(needle,needle+'\n        std::vector<float> count(map.size(),0);\n        setMarkedMultiplicityCounter(std::getenv("MARK_EXPORT_ON") ? &count : nullptr);')
(C/'native_parity_replay.cpp').write_text(h)
compile_cmd(['/usr/bin/c++',*flags('PMFS'),'-c',str(C/'Simulations_marked.cpp'),'-o',str(B/'Simulations_marked.o')])
compile_cmd(['/usr/bin/c++',*flags('GSL_common'),'-c',str(C/'Math_seeded.cpp'),'-o',str(B/'Math_seeded.o')])
args=shlex.split((N/'build/gsl_server/CMakeFiles/native_pmfs_r1_forward_replay.dir/link.txt').read_text())
objects=[]
for src,out,extra in [('native_parity_replay.cpp','native_parity_replay',[str(B/'Simulations_marked.o')]),('marked_forward.cpp','marked_forward',[str(B/'Simulations_marked.o'),str(B/'Math_seeded.o')])]:
    cmd=args.copy()
    for i,v in enumerate(cmd):
        if v.endswith('.cpp.o'):cmd[i]=str(C/src)
        if i>0 and cmd[i-1]=='-o':cmd[i]=str(B/out)
    cmd=cmd[:1]+flags('native_pmfs_r1_forward_replay')+extra+cmd[1:]
    assert 'R1_R2_REFERENCE_SOURCE' not in ' '.join(cmd)
    compile_cmd(cmd); objects.append({'binary':out,'sha256':sha(B/out),'command':cmd})
dump(R/'build_provenance.json',{'binaries':objects,'historical_library_sha256':provenance['historical_library_sha256'],'kernel_sha256':{p.name:sha(p) for p in K.iterdir()},'patched_source_sha256':{p.name:sha(p) for p in C.glob('*.cpp')}})
print('BUILD_COMPLETE',flush=True)
