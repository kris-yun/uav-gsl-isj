"""Freeze selected historical inputs and extract 2026 forward kernels. No ROS or worlds."""
from pathlib import Path
import json, hashlib, shutil, re, sys, csv

R=Path(__file__).resolve().parents[1]
W=R.parent
P=W/'NATIVE_PMFS_WIND_RECOVERY_20261014/PORTABLE_DATA'
S=P/'native_pmfs/official_upstream/gsl_server/src/gsl_server'
OLD=W/'INTERMITTENCY_CAUSAL_AUDIT_20261017/cpp'
sys.path.insert(0,str(P.parent))
from cdr_grid import decode_grid

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def extract(t,signature):
    a=t.index(signature);b=t.index('{',a);n=1;j=b+1
    while n:n+=(t[j]=='{')-(t[j]=='}');j+=1
    return t[a:j]

for name in ['code','inputs','logs','results','lineage']:(R/name).mkdir(parents=True,exist_ok=True)
assert not (R/'FROZEN_PLAN.json').exists()
idx=json.loads((P/'CASE_INDEX.json').read_text())
chosen=[];manifest={}
for case,epochs in [('C4',[0,1]),('C3',[2])]:
    item=next(x for x in idx['cases'] if x['case']==case)
    native=P/item['native_path']
    rawmeta=None
    for line in (native/'runtime/raw_ros_cdr.jsonl').open():
        msg=json.loads(line)
        if msg['topic']=='/PioneerP3DX/map':
            rawmeta,_=decode_grid(bytes.fromhex(msg['cdr_hex']));break
    assert rawmeta is not None
    for ep in epochs:
        folder=native/f'runtime/updates/update_{ep}'
        m=json.loads((folder/'metadata.json').read_text())
        # The old JSON has six-digit origins. Restore float grid metadata from the actual captured map CDR.
        rounded_origin=[m['origin_x'],m['origin_y']]
        import struct
        f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
        m['origin_x']=f32(rawmeta['origin_xyz'][0]);m['origin_y']=f32(rawmeta['origin_xyz'][1])
        dest=R/f'inputs/{case}_update_{ep}'
        dest.mkdir()
        with (dest/'metadata.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(m));w.writeheader();w.writerow(m)
        record=dict(case=case,epoch=ep,native_update=str(folder),truth=item['metadata']['source_xyz'],
                    implementation='2026_4e141e162551e674f2f30ddb8859136c72139aac_corrected_wind',
                    identity=item['identity'],metadata=m,archived_rounded_origin=rounded_origin,
                    exact_origin_source='actual map CDR, cast to native float',fixture=str(dest))
        chosen.append(record)
    # The full source histories remain canonical; record hashes rather than copying them again.
    for p in native.rglob('*'):
        if p.is_file():manifest[str(p.relative_to(P))]=dict(bytes=p.stat().st_size,sha256=sha(p))
    shutil.copyfile(native/'runtime/resolved_GSL_parameters.yaml',R/f'lineage/{case}_parameters.yaml')
    shutil.copyfile(native/'runtime/measurement_events.csv',R/f'inputs/{case}_measurement_events.csv')
    (R/f'lineage/{case}_CASE_INDEX.json').write_text(json.dumps(item,indent=2))

plan=dict(
    scope='Fixed captured histories only; no new gas worlds, ROS episodes, training or algorithms',
    cases=chosen,normal_control_rule='C3 latest complete update, native converged error 0.433755 m; selected before new prediction runs',
    parameters=dict(deltaTime=.1,noiseSTDev=.5,iterationsToRecord=200,minWarmupIterations=200,maxWarmupIterations=500,blurSigmaX=1.5,blurSigmaY=1.5,sourceDiscriminationPower=.3),
    prediction_rng_states=[2026101701,2026101702,2026101703],
    parity='All archived candidates for both C4 updates and C3 update_2; source releases and Gaussian table/index restored; no contrast until raw and blurred maps match',
    A='Same final native source partition; three independent prediction states, unchanged measured maps/wind/scoring',
    B='For each legal source cell: one full simulation from its native final leaf versus one from its own 0.25m cell; all sources receive equal area allocation. Same number of simulations, release rate, recorded horizon and maximum warmup budget. Actual CPU/particle moves reported separately.',
    marginalization='Both score(mean_response) and area_weighted_mean(exp(logscore)) reported; fine cell posterior retained and likelihood integrated back into original leaves',
    competitor='Prior update posterior first row-major maximum from captured input.csv, frozen before new responses; epoch 0 abstains',
    truth_use='Only post-hoc metrics; never source selection, seeds, source weights or parameter tuning',
    event_semantics='No ppm-threshold surrogate without filament mass, radius/sigma, age, z and sensor response; report unavailable quantities',
    maximum_forward_calls=12000,maximum_child_cpu_s=1800,maximum_output_mib=200,
    termination='Stop after these contrasts and scientific verdict; no new ROS loop or innovation module')
(R/'FROZEN_PLAN.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
(R/'INPUT_MANIFEST_SHA256.json').write_text(json.dumps(manifest,indent=2))

shutil.copytree(OLD/'dda',R/'code/dda')
shutil.copyfile(OLD/'visibility.hpp',R/'code/visibility.hpp')
grid=(S/'algorithms/Common/Grid2D.hpp').read_text()
grid='\n'.join(l for l in grid.splitlines() if not l.startswith('#include'))
pose=extract(grid,'        Vector2Int coordinatesToIndices(const geometry_msgs::msg::Pose& pose) const')
grid=grid.replace(pose,'// ROS pose overload excluded in the offline adapter.')
(R/'code/grid.hpp').write_text(grid)
hp=(S/'algorithms/PMFS/internal/HitProbability.hpp').read_text()
hp='\n'.join(l for l in hp.splitlines() if not l.startswith('#include'))
(R/'code/hit.hpp').write_text(hp)
math=(S/'algorithms/Common/Utils/Math.cpp').read_text()
math_sigs=['    double lerp(', '    double clamp(', '    double logOddsToProbability(',
           '    double randomFromGaussian(', '    template <typename T> T uniformRandomT(',
           '    float uniformRandomF(', '    double uniformRandom(']
mf=[extract(math,s) for s in math_sigs]
(R/'code/native_math.cpp').write_text('#include "support.hpp"\nnamespace GSL::Utils {\nstatic thread_local std::minstd_rand0 RNGengine;\n'+ '\n'.join(mf)+'\nvoid restore_rng(const std::string&s){std::istringstream(s)>>RNGengine;}\nstd::string rng_state(){std::ostringstream s;s<<RNGengine;return s.str();}\n}\n')
text=(S/'algorithms/PMFS/internal/Simulations.cpp').read_text()
sigs=['    long double Simulations::sourceProbFromMaps(', '    double Simulations::probabilityFromSingleCell(',
      '    double Simulations::probabilitySingleFrequency(', '    void Simulations::moveFilament(',
      '    bool Simulations::filamentIsOutside(', '    void Simulations::simulateSourceInPosition(',
      '    Vector2 SimulationSource::getPoint(', '    bool Simulations::moveAlongPath(',
      '    void Simulations::blurHitMap(']
funcs=[extract(text,s) for s in sigs]
extraction=[]
for i,f in enumerate(funcs):
    extraction.append(dict(signature=sigs[i],official_sha256=hashlib.sha256(f.encode()).hexdigest(),
                           adapter='movement counter only' if 'void Simulations::moveFilament(' in f else 'archived release replay hook; disabled for all contrasts' if 'Vector2 SimulationSource::getPoint(' in f else 'verbatim'))
    if 'void Simulations::moveFilament(' in f:f=f.replace('{','{ ++diag::moves;',1)
    if 'Vector2 SimulationSource::getPoint(' in f:
        f=f.replace('return randP;', '++diag::releases; return diag::source_point(randP);')
    funcs[i]=f
(R/'code/native_forward.cpp').write_text('#include "support.hpp"\nnamespace GSL::PMFS_internal {\nthread_local Utils::PrecalculatedGaussian<2500> gaussian;\n'+'\n'.join(funcs)+'\n}\n')
(R/'lineage/EXTRACTED_KERNELS.json').write_text(json.dumps(extraction,indent=2))
for name,path in [('Simulations.cpp',S/'algorithms/PMFS/internal/Simulations.cpp'),('Math.cpp',S/'algorithms/Common/Utils/Math.cpp'),('Grid2D.hpp',S/'algorithms/Common/Grid2D.hpp'),('Math.hpp',S/'algorithms/Common/Utils/Math.hpp')]:
    shutil.copyfile(path,R/'lineage'/name)
print(json.dumps(dict(status='FROZEN',histories=len(chosen),hashed_files=len(manifest),root=str(R))))
