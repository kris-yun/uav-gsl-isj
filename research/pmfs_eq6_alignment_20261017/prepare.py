"""Freeze a named Eq6-only reconstruction and existing-history score controls."""
from pathlib import Path
import csv, difflib, hashlib, json, re, shutil, subprocess, sys
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
AUDIT=PROJECT/'_staging/FSR_S2_PMFS_PAPER_BASELINE_AUDIT_V1_20261018'
SEP=AUDIT/'source/AUTHOR_FIX_20240918'
DATA=PROJECT/'workspace/NATIVE_PMFS_WIND_RECOVERY_20261014/PORTABLE_DATA/cases'
COMMIT='a8d5a764b7cbfc1d5d1887aebfe890e2c75d7533'
REL=Path('gsl_server/src/gsl_server/algorithms/PMFS/PMFSLib.cpp')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rows(p): return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def body(text,signature):
    i=text.index(signature);a=text.index('{',i);depth=0
    for b in range(a,len(text)):
        depth+=(text[b]=='{')-(text[b]=='}')
        if depth==0: return text[i:b+1]
    raise ValueError(signature)
assert not (ROOT/'FROZEN_PLAN.json').exists(),'Do not overwrite a frozen plan'
lock=json.loads((AUDIT/'BASELINE_LOCK.json').read_text(encoding='utf-8'))
manifest=[]
for row in lock['candidate_source_files']:
    src=SEP/row['path'];assert sha(src)==row['sha256']
    dst=ROOT/'author_release'/row['path'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    manifest.append(dict(path=row['path'],sha256=sha(dst),git_blob_oid=row['git_blob_oid']))
put(ROOT/'AUTHOR_SOURCE_LOCK.json',dict(commit=COMMIT,scope='All candidate-source files already enumerated by the prior verified lock; not a complete ROS dependency distribution',files=manifest))
src=ROOT/'author_release'/REL
original=src.read_bytes().decode('utf-8')
old='double exponent = -cell.omega / std::pow(settings.confidenceMeasurementWeight, 2);'
new='double exponent = -(cell.omega * cell.omega) / std::pow(settings.confidenceMeasurementWeight, 2);'
assert original.count(old)==1
patched=original.replace(old,new)
dst=ROOT/'paper_eq6'/REL;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(patched.encode('utf-8'))
patch=''.join(difflib.unified_diff(original.splitlines(True),patched.splitlines(True),fromfile='a/'+REL.as_posix(),tofile='b/'+REL.as_posix()))
(ROOT/'paper_eq6_only.patch').write_bytes(patch.encode('utf-8'))
q=subprocess.run(['git','apply','--check',str(ROOT/'paper_eq6_only.patch')],cwd=ROOT/'author_release',capture_output=True,text=True)
put(ROOT/'PATCH_CHECK.json',dict(argv=['git','apply','--check','paper_eq6_only.patch'],exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr,original_sha256=sha(src),patched_sha256=sha(dst),changed_lines=1))
assert q.returncode==0,q.stderr
math_text=(ROOT/'author_release/gsl_server/src/gsl_server/algorithms/Common/Utils/Math.cpp').read_text()
sim_text=(ROOT/'author_release/gsl_server/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp').read_text()
parts={s:body(math_text,s) for s in ['double lerp(', 'double evaluate1DGaussian(', 'double logOddsToProbability(']}
score=body(sim_text,'double Simulations::sourceProbFromMaps(')
confidence='''void updateConfidence(HitProbability& cell, const HitProbabilitySettings& settings) {
    double exponent = -cell.omega / std::pow(settings.confidenceMeasurementWeight, 2);
    cell.confidence = 1 - std::exp(exponent);
}'''
assert old in confidence
generated='''// Extracted source components. Minimal data containers replace ROS/grid storage only.
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#define ZoneScoped
#define GSL_ASSERT(x) do {if(!(x))throw std::runtime_error("native assertion");}while(0)
namespace GSL {
enum class Occupancy {Obstacle=0,Free=1};
struct HitProbability {double logOdds=0,omega=0,confidence=0;};
struct HitProbabilitySettings {double confidenceMeasurementWeight=1;};
template<class T> struct Grid2D {std::vector<T>data;std::vector<Occupancy>occupancy;};
namespace Utils {
'''+ '\n'.join(parts.values())+'''
}
namespace native {
'''+confidence+'''
}
namespace eq6 {
'''+confidence.replace(old,new)+'''
}
namespace PMFS_internal {
struct Simulations {struct Settings {double sourceDiscriminationPower=1;}settings;
double sourceProbFromMaps(const Grid2D<HitProbability>&,const std::vector<float>&)const;};
'''+score+'''
}
}
'''
(ROOT/'cpp').mkdir(exist_ok=True)
(ROOT/'cpp/extracted_native.hpp').write_text(generated,encoding='utf-8',newline='\n')
contexts=[]
for case in ['A2','B2']:
    runtime=DATA/case/'native_execution/runtime'
    config=(runtime/'resolved_GSL_parameters.yaml').read_text()
    def param(key):
        m=re.search(r'^\s*'+re.escape(key)+r':\s*([-+0-9.eE]+)\s*$',config,re.M);assert m,key;return float(m[1])
    w=param('confidenceMeasurementWeight');power=param('sourceDiscriminationPower')
    for up in sorted((runtime/'updates').iterdir()):
        assert up.is_dir()
        key=case+'_'+up.name;dest=ROOT/'fixtures'/key;dest.mkdir(parents=True)
        for name in ['input.csv','metadata.json','candidates.csv','final_tree.csv','posterior.f64','raw_cell_scores.csv','normalization.txt']:
            shutil.copyfile(up/name,dest/name)
        shutil.copyfile(runtime/'resolved_GSL_parameters.yaml',dest/'resolved_GSL_parameters.yaml')
        shutil.copyfile(runtime/'measurement_events.csv',dest/'measurement_events.csv')
        inp=rows(up/'input.csv');candidates=rows(up/'candidates.csv')
        maps=[]
        for k,row in enumerate(candidates):
            rel=Path(row['map_file']);assert not rel.is_absolute() and '..' not in rel.parts
            target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(up/rel,target)
            maps.append(dict(serial=int(row['serial']),candidate_id=row['candidate_id'],map_file=rel.as_posix(),sha256=sha(target)))
        lines=[f'{len(inp)} {len(candidates)} {w:.17g} {power:.17g}']
        for r in inp:lines.append(' '.join(r[k] for k in ['occupancy','logOdds','omega','confidence']))
        for r in maps:lines.append(f"{r['serial']} {r['map_file']}")
        (dest/'request.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
        meta=json.loads((dest/'metadata.json').read_text())
        contexts.append(dict(case=case,update=up.name,key=key,original= str(up),metadata=meta,candidates=len(candidates),weight=w,power=power,maps=maps))
# Preserve all six 2024 repeat identities. Missing candidate/Omega state is not imputed.
exports=PROJECT/'workspace/PMFS_OFFICIAL_REPRO_AUDIT_20261016/PRO_NATIVE_PMFS_EXPORT'
prior=[]
for case in ['A2','B2']:
    for repeat in range(1,4):
        name=f'P24_{case}_WALL5_VALID_V2_R{repeat:02d}';srcdir=exports/name
        if not srcdir.exists():continue
        dest=ROOT/'historical_2024'/name;dest.mkdir(parents=True)
        for n in ['CASE_META.json','RUN_RESULT.json','native_results.csv','native_window_consumption.csv','resolved_GSL_parameters.json','CLOCK_SENSOR_RATE_PREFLIGHT.json']:
            if (srcdir/n).exists():shutil.copyfile(srcdir/n,dest/n)
        head=rows(srcdir/'native_posterior_updates.csv')
        cols=list(head[0]) if head else []
        prior.append(dict(id=name,case=case,columns=cols,omega_saved='omega' in cols,candidate_response_maps_saved=bool(list(srcdir.glob('**/candidates.csv'))),original=str(srcdir),posterior_rows=len(head),posterior_sha256=sha(srcdir/'native_posterior_updates.csv')))
        shutil.copyfile(srcdir/'native_posterior_updates.csv',dest/'native_posterior_updates.csv')
put(ROOT/'HISTORICAL_2024_ELIGIBILITY.json',dict(records=prior,full_eq6_source_replay_qualified=False,reason='Exported posterior/alpha alone does not preserve candidate predictions, adaptive-tree ownership or full Omega; no historical RNG is fabricated.'))
plan=dict(status='FROZEN_BEFORE_NEW_COMPONENT_EXECUTION',author_commit=COMMIT,formula_change='Omega -> Omega*Omega in confidence exponent only',paper_reconstruction_complete=False,age_radius_rule_missing=True,provided_pro_patch_present=False,contexts=contexts,conditions=dict(fixed_real_observation_history=True,fixed_predicted_maps=True,fixed_native_final_tree=True,fixed_source_support=True,fixed_score_power=True,new_worlds=0,new_ros=0,new_forward_simulations=0,new_rng_states=0),tolerances=dict(confidence_abs=2e-14,logscore_abs=2e-10,native_posterior_abs=2e-10,unit_abs=2e-14),scope='2024 Sep source-component test + 2026 captured A2/B2 confidence-only fixed-tree score diagnostic, NOT a counterfactual closed loop or full 2024 paper reproduction',max_guest_wall_s=180)
put(ROOT/'FROZEN_PLAN.json',plan)
print(json.dumps(dict(contexts=len(contexts),maps=sum(c['candidates']for c in contexts),author_files=len(manifest),patch_check='PASS',new_forward_calls=0)))
