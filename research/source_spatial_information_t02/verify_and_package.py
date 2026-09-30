"""Independent arithmetic, repeat verification and compact T02 review delivery."""
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import subprocess
import zipfile

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
E=ROOT/'evidence/source_spatial_information_t02'
R=ROOT/'research/source_spatial_information_t02'
I=ROOT/'evidence/ocb_r2/mechanism_census_r0/inputs'
ARMS=('TOTAL_RATE_1D','STATIC_SPATIAL_30D','AMPLITUDE_REMOVED_SPATIAL_30D','COMPOSITIONAL_SPATIAL_30D','LOCATION_DESTROYED')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p,value):
    p.write_text(value,encoding='utf-8',newline='\n')


def rows(p):
    with p.open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f,delimiter='\t'))


def verify():
    first,second=E/'pass1',E/'pass2'
    names=sorted(p.name for p in first.iterdir() if p.is_file())
    assert names==sorted(p.name for p in second.iterdir() if p.is_file())
    checks=[]
    for name in names:
        assert (first/name).read_bytes()==(second/name).read_bytes(),name
        checks.append(dict(file=name,bytes=(first/name).stat().st_size,sha256=sha(first/name),byte_identical=True))
    write(E/'DETERMINISTIC_REPEAT.json',json.dumps(dict(pass_=True,compared_files=len(checks),checks=checks),indent=2,sort_keys=True)+'\n')
    manifest=rows(first/'EXACT_64_RUN_MANIFEST.tsv')
    nulls=rows(first/'EXACT_70_ASSIGNMENT_NULLS.tsv')
    old=rows(ROOT/'evidence/cdsi_t01b/pass1/EXACT_70_ASSIGNMENT_NULLS.tsv')
    assignments=list(itertools.combinations(range(8),4))
    arithmetic=[]
    for c in range(8):
        context=f'X{c:02d}'
        rr=sorted([r for r in manifest if r['context']==context],key=lambda r:(r['source_id'],int(r['replicate_ordinal'])))
        b=np.stack([np.load(I/(r['run_id']+'.pooled.npy'),allow_pickle=False)>0 for r in rr])
        v=b.sum(axis=1).astype(float)/10
        q=np.zeros_like(v)
        for j in range(8):
            if v[j].sum()>0:
                q[j]=v[j]/v[j].sum()
        rep={ARMS[0]:b.sum(axis=(1,2))[:,None].astype(float)/300,
            ARMS[1]:v,ARMS[2]:v-v.mean(axis=1)[:,None],ARMS[3]:q}
        for arm,x in rep.items():
            distance=np.empty((8,8))
            for i in range(8):
                for j in range(8):
                    distance[i,j]=math.sqrt(sum(float(t)**2 for t in x[i]-x[j])/x.shape[1])
            direct=[]
            for a in assignments:
                alt=[i for i in range(8) if i not in a]
                ab=sum(distance[i,j] for i in a for j in alt)/16
                aa=sum(distance[i,j] for i in a for j in a)/16
                bb=sum(distance[i,j] for i in alt for j in alt)/16
                direct.append(2*ab-aa-bb)
            saved=sorted([r for r in nulls if r['context']==context and r['arm']==arm],key=lambda r:int(r['assignment_index']))
            err=max(abs(d-float(r['energy'])) for d,r in zip(direct,saved))
            assert len(saved)==70 and err<1e-12
            arithmetic.append(dict(context=context,arm=arm,permutation_checks=70,max_abs_error=err))
            if arm==ARMS[1]:
                previous=sorted([r for r in old if r['context']==context and r['arm']=='STATIC_COLLAPSED_30D'],key=lambda r:int(r['assignment_index']))
                assert all(r['energy']==s['energy'] and r['z']==s['z'] for r,s in zip(saved,previous))
    draw_values=np.load(first/'LOCATION_ALL_ASSIGNMENT_DRAW_ENERGIES.npy',allow_pickle=False)
    assert draw_values.shape==(8,70,1000)
    for c in range(8):
        saved=sorted([r for r in nulls if r['context']==f'X{c:02d}' and r['arm']=='LOCATION_DESTROYED'],key=lambda r:int(r['assignment_index']))
        assert np.allclose(draw_values[c].mean(axis=1),[float(r['energy']) for r in saved],atol=1e-12,rtol=0)
    verification=dict(pass_=True,direct_assignment_checks=2240,checks=arithmetic,
        all_static_exact_nulls_identical_to_t01b=True,location_draw_mean_matches_all_exact_nulls=True,
        arithmetic_only_no_new_scorer=True,script_sha256=sha(Path(__file__)))
    write(E/'INDEPENDENT_ARITHMETIC_CHECK.json',json.dumps(verification,indent=2,sort_keys=True)+'\n')
    result=json.loads((first/'T02_RESULT.json').read_text(encoding='utf-8'))
    context_rows=rows(first/'CONTEXT_REPRESENTATION_RESULTS.tsv')
    location=rows(first/'LOCATION_IDENTITY_EFFECTS.tsv')
    report=['# T02 静态空间源信息诊断','',
        '日期：2026-10-01','',
        '分支：`research/source-spatial-information-t02-20261001`','',
        '前置冻结提交：`04215e6b`（协议、代码、8/8 metadata contract）。','',
        f"## 机制标签：`{result['decision']}`",'',
        '**仅为已批准规则下的机制诊断，不是主创新 PASS，也不是纯 XY 可辨识结论。**','',
        '## 表示层汇总','',
        '| 表示 | exact p≤0.05 的context | 高于null中位数 | source-stability |',
        '|---|---:|---:|---|']
    for arm in ARMS:
        s=result['source_stability'][arm]
        report.append(f"| {arm} | {s['exact_p_le_005_contexts']}/8 | {s['above_null_median_contexts']}/8 | {s['stable']} |")
    report+=['','## 每个 context 的标准化证据','',
        '| Context | House | TOTAL Z | STATIC Z | CENTERED Z | COMPOSITION Z | LOCATION Z | STATIC−LOCATION Z |',
        '|---|---|---:|---:|---:|---:|---:|---:|']
    for x in location:
        vals=[float(x[k]) for k in ('z_total','z_static','z_centered','z_composition','z_location_destroyed','delta_location_z')]
        report.append('| '+x['context']+' | '+x['house']+' | '+' | '.join(f'{v:.8f}' for v in vals)+' |')
    drop=result['location_identity_drop']
    report+=['','## 三个问题的直接回答','',
        '1. **总量是否足以解释所有 context？未建立。** TOTAL 单独在6/8 context达到 '
        'exact p≤0.05，符合整体稳定规则，但 H02 X04/X05 分别 p=0.142857/0.171429；'
        '同样两个 context 的 STATIC、CENTERED、COMPOSITION 都是 p=0.028571。'
        '总量有明显信息，不能说它没有作用；本轮也没有计算条件互信息来证明严格 sufficiency。','',
        '2. **去掉总体水平后是否仍保留源信号？是。** CENTERED 与 COMPOSITION 均在8/8 '
        'context达到 p=0.028571；同一评分器及全部70标签分配完成核验。'
        '它们仍保留各自的空间形状与部分 histogram 结构，不能声称移除了所有 nuisance。','',
        f"3. **去掉probe身份是否下降？按冻结Z差规则，是。** 7/8为正，median差 "
        f"{drop['median_delta_z']:.8f}，exact one-sided sign-test p={drop['exact_one_sided_p']:.8f}。",
        'LOCATION_DESTROYED 仍在7/8 context显著，而且仍符合整体 source-stability 标准。'
        '因此 probe identity 有增量，但不是唯一承载；value multiset/histogram 仍然有较强源信息。','',
        '“PRIMARILY_SPATIAL_PATTERN”遵循人工事前确认的诊断归类，不是因果贡献比例估计。'
        'TOTAL稳定与该标签并不矛盾，批准的层级规则在两种去幅值表示稳定且位置打乱下降时采用该标签。','',
        '## 复核与封存','',
        f"完整两遍输出的{len(checks)}个文件逐字节相同，包含全部exact null、LOCATION draw数组和aggregate-null字节哈希。",
        '独立直接求和核对8×4×70=2,240个Energy值；STATIC全部560个exact-null Energy/Z '
        '与T0.1B原记录完全一致。LOCATION保持64,000个profile multiset，sum/mean/norm不变；'
        '预选draw的全部70标签结果与直接距离计算一致。','',
        f"全零样本数：{result['zero_profile_count']}/64。预冻结的全零映射规则未触发。",
        '每个context穷举70标签分配；5个表示的跨context联合null采用固定seed的 '
        '1,000,000次分层Monte Carlo，不能称穷举70^8。surrogate不增加物理样本数。','',
        '## 理论边界与下一步权限','',
        '本轮仍是每context仅两个配置源、每源4个独立plume。H01 z=0.4/−0.3 m，'
        'H02 z=0.2/−0.1 m；因此该诊断不能分离XY与释放高度的贡献。'
        '数据为已使用的discovery，不是新确认集；不宣称全source-map连续定位成立。','',
        '本轮没有模拟、PMFS、网络、confirmation/H03或闭环；未改观测规则、source、seed或scorer。'
        '未执行12条fixed-z实验，也未新建其运行清单。','',
        '后续即使3个source在几何上不共线，也只说明source位移设计矩阵rank=2；'
        '不能仅凭几何rank宣称连续逆问题可辨识。另一个fixed-z实验失败也不单独证明必须3D：'
        '需要区分高度、观测可达性、信噪比和具体采样合同。本轮不执行这些后续设计。','',
        '**完成后 STOP，保留全部历史结果。**','']
    write(R/'T02_DIAGNOSTIC_REPORT.md','\n'.join(report))
    theory=f'''# T02 interpretation

Diagnostic label: **{result['decision']}**.

Removing the profile common level and normalizing to its composition retain
source evidence in all eight contexts under the frozen Energy label tests.
Destroying probe identity reduces the standardized effect in seven contexts,
with exact sign-test p={drop['exact_one_sided_p']}, yet the destroyed-identity
histogram information remains significant in seven contexts. Total encounter
rate alone is significant in six contexts. These overlapping signals do not
support a claim that source information is exclusively spatial location or
that its causal information fraction has been measured.

The label is the pre-approved operational diagnostic hierarchy. It authorizes
no new main-innovation PASS, calibrated source likelihood, causal attribution,
pure XY identifiability, or complete-source-map localization claim. Both
Houses' source pairs change z as well as xy. Centering only removes an additive
level; composition removes positive profile scale but preserves relative
shape and histogram effects. Zero profiles would retain a no-encounter flag;
there are no such profiles among these 64 runs.

The old paired CDSI contract failure, T0.1B dynamic HOLD and R0/R1/R2 evidence
are unchanged. No alternate scorer or surrogate was tuned to reverse any of
them. This diagnosis is on already-used discovery data, not fresh confirmation.

No fixed-z source or run is selected or generated in this task. Noncollinear
coordinates alone do not prove inverse-map local rank or continuous source
identifiability; that requires the observation response itself and nuisance
assessment. STOP for human review before any prospective experiment.
'''
    write(R/'THEORY_INTERPRETATION.md',theory)
    print(json.dumps(dict(decision=result['decision'],repeat_files=len(checks),direct_checks=2240,pass_=True),sort_keys=True))


def package():
    files=[p for folder in (R,E) for p in folder.rglob('*') if p.is_file() and '__pycache__' not in str(p)]
    files+=list(I.glob('*.pooled.npy'))
    for rel in ('research/cdsi_t01b/run_audit.py','research/cdsi_t01b/IMPLEMENTATION_FREEZE.md',
        'research/cdsi_t01b/CDSI_T01B_REPORT.md','evidence/cdsi_t01b/pass1/CDSI_T01B_RESULT.json',
        'evidence/cdsi_t01b/pass1/CONTEXT_ENERGY_RESULTS.tsv',
        'evidence/cdsi_t01b/pass1/EXACT_70_ASSIGNMENT_NULLS.tsv',
        'evidence/ocb_r2/mechanism_census_r0/R0_INPUT_HASHES.json',
        'evidence/cdsi_t01/EXACT_64_RUN_MANIFEST.tsv',
        'research/ocb_r2/OCB_R2_GENERATOR_CONTRACT.md',
        'research/ocb_r2/RNG_THREAD_DETERMINISM_AUDIT.md'):
        files.append(ROOT/rel)
    files+=list((ROOT/'evidence/ocb_r2/s2_runs').glob('*.RUN_MANIFEST.json'))
    files+=list((ROOT/'evidence/ocb_r2/s2x/runs').glob('*.RUN_MANIFEST.json'))
    files=sorted(set(files))
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    result=json.loads((E/'pass1/T02_RESULT.json').read_text(encoding='utf-8'))
    inventory=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in files]
    provenance=dict(commit=commit,branch=branch,pre_score_freeze='04215e6b',decision=result['decision'],diagnostic_only=True,files=inventory)
    destination=Path('C:/Users/50176/Downloads/SOURCE_SPATIAL_INFORMATION_T02_REVIEW_20261001.zip')
    assert not destination.exists(),'Refusing overwrite'
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files:
            z.write(p,p.relative_to(ROOT).as_posix())
        z.writestr('PACKAGE_PROVENANCE.json',json.dumps(provenance,indent=2,sort_keys=True)+'\n')
    with zipfile.ZipFile(destination) as z:
        assert z.testzip() is None
        for entry in inventory:
            assert hashlib.sha256(z.read(entry['path'])).hexdigest()==entry['sha256']
    meta=dict(path=str(destination),bytes=destination.stat().st_size,sha256=sha(destination),commit=commit,branch=branch,decision=result['decision'])
    write(destination.with_suffix('.json'),json.dumps(meta,indent=2,sort_keys=True)+'\n')
    print(json.dumps(meta,sort_keys=True))


if __name__=='__main__':
    import sys
    package() if '--package' in sys.argv else verify()
