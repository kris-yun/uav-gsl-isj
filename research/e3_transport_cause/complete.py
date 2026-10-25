"""Seal the finite causal campaign, audit fidelity, and deliver its evidence."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,re,shutil,subprocess,sys,zipfile
import numpy as np
from analyze import O,P,load,put,rows,decode

REPO=Path(__file__).resolve().parents[2];DOWNLOADS=Path('C:/Users/50176/Downloads')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def prepare():
    plan=load(O/'PREREGISTERED_CAUSAL_CONTRACT.json');cost=load(O/'EXECUTION_RECEIPT.json');extension=load(O/'UV_EXTENSION_RECEIPT.json');assert extension['cumulative_execution_wall_s']<900
    for r in load(O/'INPUT_SHA256.json'):assert sha(O/r['path'])==r['sha256']
    for r in load(P/'PHYSICAL_FRAME_SHA256.json'):assert sha(P/r['path'])==r['sha256']
    for pred in plan['prediction_streams']:
        selected=list((O/'runs').glob('*_'+pred['id']))
        for name in ['RNG.GAUSSIAN.initial.txt','RNG.UNIFORM.initial.txt','RNG.cache.f32','RNG.cache.initial.txt']:
            assert len({sha(d/name) for d in selected})==1,(pred['id'],name)
        actual=np.fromfile(selected[0]/'RNG.cache.f32',dtype='<f4');prior=np.fromfile(P/'event_control'/(pred['id']+'.cache.f32'),dtype='<f4');assert np.array_equal(actual,prior[:1000])
    count=0
    for d in (O/'runs').iterdir():
        if not d.is_dir():continue
        task=load(d/'TASK.json');result=load(d/'RESULT.json');assert len(rows(d/'RESPONSES.csv'))==604
        if task['strict_bounds']:assert result['outside_particle_time_samples']==0
        initial=(d/'RNG.cache.initial.txt').read_text();final=(d/'RNG.cache.final.txt').read_text();i0=int(re.search(r'index=(\d+)',initial)[1]);i1=int(re.search(r'index=(\d+)',final)[1]);calls=int(re.search(r'calls=(\d+)',final)[1]);assert (i0+calls)%1000==i1 and calls%3==0
        assert len(list((d/'anchors').iterdir()))==13;count+=1
    assert count==27,count
    assert load(O/'ORIGINAL_KERNEL_PARITY.json')['max_abs_error_ppm']==0
    # Original-generator parity is also checked at every retained anchor state.
    schedule=rows(O/'inputs/QUERIES.csv');expected={r['query_id']:r for r in rows(O/'inputs/ORIGINAL_REPLAY_EXPECTED.csv')};anchors=[]
    for stop in range(1,14):
        q=max((r for r in schedule if r['group']=='historical' and int(r['stop'])==stop),key=lambda r:float(r['physical_s']));a=decode(O/'runs/qualification_original_true_r0/anchors'/f'stop_{stop}');b=decode(P/'worlds/true_r0/saved_world'/('iteration_'+expected[q['query_id']]['frame']));assert np.array_equal(a,b)
        anchors.append(dict(stop=stop,all_filaments_exact=True,filaments=len(a)))
    states=rows(O/'STATION_RECOVERY.csv')
    def positives(arm,rep,stops):return sum(int(r['positive_windows']) for r in states if r['arm']==arm and r['source']=='true' and r['prediction']==rep and int(r['stop']) in stops)
    for pred in plan['prediction_streams']:
        rep=pred['id'];assert positives('strict_bounds_full3d',rep,range(10,14))==20;assert positives('strict_bounds_plane',rep,range(10,14))==0;assert positives('strict_bounds_no_vertical_wind',rep,range(10,14))==20;assert positives('strict_bounds_fixed_uv',rep,[12,13])==0
    original=rows(O/'ORIGINAL_E3_HEIGHT_AND_BOUNDARY_AUDIT.csv');assert all(int(r['positive_windows_after_readonly_invalid_center_exclusion'])==5 for r in original if int(r['stop'])>=8)
    frozen=Path('D:/ZYC/A-gas/workspace/FROZEN_O24_1M2_SCREEN12_20261024/verify_frozen_baseline.py');r=subprocess.run([sys.executable,'-X','utf8',str(frozen)],capture_output=True,encoding='utf8',timeout=60);assert r.returncode==0;put(O/'FROZEN_O24_GUARD.json',dict(status='PASS',stdout=r.stdout,stderr=r.stderr))
    put(O/'CAUSAL_VERDICT.json',dict(identity='E3_HEIGHT_CONDITIONED_TRANSPORT_CAUSAL_CHAIN_IDENTIFIED',
        case_scope='frozen O24 E3 legal-source failure, archived butane/type10 gas, one stationary3D wind, two locked sources andtwo independent candidate streams; retrospective mechanism diagnosis',
        supported_chain=['Native source-hypothesis response misses late positive observations','Longer warmup and reference horizontal slice alone do not rescue','Same fine-grid GADEN kernel understrict bounds: fixed plane0of20late positive windows, free3D20of20in each stream','Zero vertical wind retains20of20, so w is not required for this rescue','Removing buoyancy dramatically weakens response and is inconsistent between streams','Keep3D motion but sample u/v at sourceheight: stops12/13lose all10positive windows in both streams'],
        interpretation='Omitted gas-height evolution and height-conditioned horizontal transport are a sufficient causal mechanism for the response failure in this case. Buoyancy-driven settling is important in this butane model; no claim that it is uniquely necessary in every realization.',
        numerical_generator_issue='Legacy native truncation admits centers in the negative fractional-voxel lower-bound layer. This is a GADEN physical-domain qualification issue, not an O24 defect. Strict-bounds controls remove it and retain the vertical rescue; read-only exclusion of direct invalid contributions keeps30of30original critical hits.',
        observation_representation='Critical binary vectors collide across the4oldtarget worlds. Correct transport plus binary alone does not establish accurate source discrimination.',
        ordinary_source_pair_results=dict(strict3d_fixed_release_continuous='8of8 across4oldworlds x2independent predictions; not8independent worlds',strict3d_unknown_gain='6of8',strict3d_binary='4of8 tie-aware; no stable8-way gain',fixed_uv_fixed_release_continuous='4of8, true-world combinations0of4'),
        not_established=['full1132cell new posterior, MAP,Top5or ROS improvement','same-information deployable local-wind rescue','cross-house/cross-gas generalization','main innovation success','old physical worlds free of boundary defects'],
        no_ROS=True,frozen_O24_unchanged=True,new_target_dataset_worlds=0,candidate_forward_calls=24,engineering_replay_calls=3))
    put(O/'ENGINEERING_HISTORY.json',dict(scientific_forward_retries=0,completed_calls_preserved_on_resume=True,
        first_compile_failure='Serialization WriteString expects std::string pointer; initial literal corrected before propagation. Original compiler stderr andCPU/wall cost retained.',
        post_stage1_stop='NumPy int64 JSON serialization failed after13complete calls. Serializer fixed; all completed TASK/results/cost validated and reused without reexecution.',
        stop_receipt_scope='The earlier STOP summary was overwritten by the post-stage1 JSON exception in the first orchestrator. Initial compiler stderr and COST entry remain original; no missing receipt has been fabricated.',
        final_status='EXECUTION_RECEIPT andUV_EXTENSION_RECEIPT supersede historical error status; no result-dependent parameter change.'))
    report=f'''# E3 因果归因完成：气团高度变化与分层水平输运

## 1. 这次查到了什么

本E3已有一条有受控实验支持的具体原因链：**GADEN丁烷模型中的下沉使气团进入较低高度；较低高度的水平风把气体带向后段测点。单层二维源响应没有表示这段高度—水平输运耦合，因此真源响应缺失。**

这里“风误差”和“二维限制”并非完全独立：即使0.7米层水平风读得准确，气团已经进入其他高度，该层风也不是它实际经历的风。增加等待时间不会自动补上缺失的高度状态。

这是一条足以产生该响应缺口的因果机制，不是对原O24最终误差的百分比方差分摊，也不等于宣布所有失效只有一个原因。后验评分和二值表示还有独立的限制，见下文。

## 2. 如何避免再把多个变化混在一起

使用同一个原生GADEN输运内核、同一0.1米三维几何、同一原E3三维风文件、同一10团/秒释放、源高0.7米、type10丁烷、298K/1atm、初始10ppm与10cm展宽、gamma15、原生噪声输入0.015（内核兼容缩放后0.15），只在隔离副本开启明确的因果开关。

所有模型从独立空场沿同一240秒物理时间推进，按原冻结604条查询读取；不是拿一个世界的气团平移到另一个源，也不是临时选高浓度测点。两套预测初态沿用此前预注册cache_seed_words/uniform_seed；与四个目标世界的RNG不同，没有用目标自身随机状态做候选预测。保留原生循环Gaussian缓存，不能称逐步噪声独立同分布。

先原样重放旧true_r0：604条原始浓度和13个完整气团锚状态完全一致，证明默认原模式没有被工程移植改写。严格边界模型之间，细网格、质量、释放、噪声、时钟、浓度公式、3σ截断及LOS完全相同；固定平面仍消费全部xyz随机数，只在位移末端约束z=0.7米。

模型分叉后，气团存活和随机消耗可能不同，因此只保证相同初始引擎/缓存及确定的程序干预，不能声称后续每个气团得到相同随机增量。

## 3. 决定性的消融

评价原E3第10–13站的20个已冻结观测窗口。下表每格对应一条预测流；这些窗口相关，不是20个独立世界。

| 同内核模型 | 流0正检出窗口 | 流1正检出窗口 |
|---|---:|---:|
| 严格边界、完整三维 | 20/20 | 20/20 |
| 同参数、固定0.7米平面 | 0/20 | 0/20 |
| 完整三维、只去掉竖直风w | 20/20 | 20/20 |
| 完整三维、只去掉浮力漂移 | 0/20 | 17/20，浓度大幅减弱 |
| 保留三维运动，u/v始终取0.7米层 | 10/20 | 10/20 |

最后一组第10/11站恢复，但第12/13站均0/10；完整三维则两流均10/10。这项扩展在看其结果前单独登记，只有4次新候选调用和2次新二进制一致性重放，没有按结果搜索高度或种子。

这几项共同排除了一个过于简单的解释：并非“只要有竖直风w就好”。去掉w仍恢复，说明在这个丁烷实现中，气体自身浮力项导致的下沉及其进入的水平风层更重要。去掉浮力后有一条流偶尔仍检出，所以不能写“浮力在所有随机情况下都严格必要”。

旧E3第8–13站正浓度贡献的加权中心高度约0.21–0.40米；其中约63%–89%来自低于0.5米的中心。它们与0.7米释放高度不同。严格边界三维预测中也存在大量低层气团，并没有依靠允许气团越界来获得恢复。

0.2、0.5、0.7和1.0米细网格平面上，真源与各观测位置均存在自由空间图路径。因此本例也不能简单解释为“在0.7米平面两点拓扑完全不连通”。实际的风向、漂移及高度条件化输运决定气团是否走到那里。

## 4. 这与原生O24失败的关系

前两轮已经固定：原生真源响应缺失，220秒预热仍缺失，替换为0.7米水平参考风只恢复第8/9站，后四站仍失败。本轮用正确细网格、统一物理内核和正确的参考风重做固定平面后，缺失仍出现；放开高度后恢复。

因此，原生0.25米网格、0.5噪声、局地GMRF误差、遇障碍停止规则并不是制造后四站缺失的必要条件：即使换成更细的普通物理控制，只要束缚在单层，仍会失败。它们可能继续放大误差，本轮未为每个因素分摊数值贡献。

严格解释应为：**在此E3条件下，遗漏气团高度变化和相应的水平风层切换，已被验证为能造成关键源响应缺失的机制。**它解释“闻到气体却把真源模型判为不相容”的前向环节；不等于已经重算原O24全部候选后验、证明其3.39米误差只由这一个环节造成。

三维对照使用完整细三维参考风，是明示的诊断oracle。部署时只有局地风，能否恢复所需低层输运信息仍未证明。不能把这里的恢复当作同权限新算法胜过O24。

## 5. 有响应之后，真的能区分源吗

候选计算从物理方程、源位置和独立预测RNG产生，没有已知源响应参考库或训练拟合。四个旧目标世界仅用于评价。锁定两源、全13站、两套独立预测的普通评分如下：

| 模型 | 固定释放量连续MSE | 非负未知幅度MSE | 二值Brier |
|---|---:|---:|---:|
| 严格边界完整三维 | 8/8 | 6/8 | 4/8 |
| 同内核固定平面 | 6/8 | 4/8 | 4/8 |
| 去竖直风w | 8/8 | 6/8 | 3/8 |
| 去浮力项 | 6/8 | 4/8 | 4/8 |
| 三维运动、固定u/v高度 | 4/8 | 4/8 | 4/8 |

8个评分组合仍然只有4个目标传播世界、两个源位置及同一个风环境；不是8次独立实验。所有正反例和逐源结果保留，未做显著性或未知源泛化声明。

严格三维的8/8是固定释放合同下的源对正向结果。未知幅度后仍有2个组合错误，说明绝对浓度尺度有重要作用。二值模式没有稳定收益，因为后6站四个旧目标世界均30/30检出，已经形成实际的二值碰撞。正确传播不能凭空恢复被表示丢掉的幅值信息。

对原始E3以及直接扣除越界中心贡献的原E3，严格三维连续评分两条预测流均支持真源；固定u/v高度的三维模型两条流均仍选错源。这给高度条件化水平输运增加了源判别层面的证据，但仍只有锁定两源。

本轮没有1132源格的新后验、全域MAP、Top-5%、90%HPD或新ROS误差。不得把两源诊断结果改写成完整定位成功率。

## 6. 新发现的生成器边界缺陷，单独更正

原GADEN `Environment::coordsToIndices` 将浮点向量直接转整数，略低于minCoord的负小数会截向0，而不是floor到-1。因而-0.05米的z在0.1米格中会映射第0层，通过索引边界检查。旧E3确有z落在(-0.1,0)内的气团；四个配对目标世界最后帧分别有1071/2286、504/1240、889/2116、1171/2298个中心越出连续仿真域下界。

此前完成的是生成器血统、源合法性、RNG与原生浓度一致性验证，没有覆盖所有气团中心的连续边界合法性。**这一项此前漏检，本轮明确补上。旧数据的“无边界缺陷物理真值”资格不成立，不能静默追认。**原始世界、日志和负结果均不修改。

这是生成器数值边界问题，不属于O24算法缺陷。严格对照只将坐标换算改为floor，继续使用原生OutOfBounds碰撞投影规则；不是删除气团、关闭LOS或挖通地图。所有严格模型的完整2400步连续域越界中心数均为0。

它也不能单独解释关键正检出：旧E3后6站浓度中，越界中心的直接贡献约2.2%–23.7%；只读扣除后仍30/30正检出。严格边界三维内核自身也恢复30/30，而严格边界平面仍缺失后四站。故本轮的垂向输运对照不依赖放任负z气团。

但“扣除直接贡献”不是把整个旧世界物理修好了：越界历史可能影响后续轨迹，且本轮目标世界仍是旧数据。因此这些结果仍是回顾性机制证据。正式独立确认需另立无边界缺陷的数据合同，不能把旧世界改名成新合格数据。

## 7. 已经找到的原因与未完成的工作

已有受控支持的原因链是：

**该丁烷模型的垂向漂移 → 气团高度改变 → 进入不同的水平风层 → 迟到的低层气体到达后段测点 → 单层二维源响应漏报 → 原评分不利于真源；二值化与空间证据扩展使后续源判别更困难。**

前五步由本轮同核消融及此前原生响应审计支持；最后的空间放大有此前固定原生缓存复核支持，尚未完成原生全候选的修复后闭环验证。不要把这条链写成跨气体、跨House的唯一普遍失效定律。

这也不是任务记忆网络或主创新PASS。普通三维物理加连续读出已经能在该oracle源对恢复判别，下一步若研究算法，必须处理局地风权限、计算预算、未知释放量及独立确认，而不是把三维适配本身重新包装成主创新。

## 8. 资源、失败记录与交付

初始有限阶梯20次候选前向；另行事前登记的固定u/v高度控制4次；加原生成器复算1次、扩展二进制复算2次，共24次候选计算和3次工程重放。没有新源、随机种子、目标气体数据集、ROS或神经训练；只保存查询响应及每次13个锚状态，没有生成整套新世界归档。

记录的累计编译/执行墙钟约{extension['cumulative_execution_wall_s']:.2f}秒，最大单命令CPU约{max(cost['max_child_CPU_s'],extension['max_child_CPU_s']):.2f}秒，均在900/120秒上限内。模型240秒不是实时ROS墙钟。首次编译签名错误与阶段中断已保留；JSON写出中断后的13次完成调用经TASK/结果/成本核验后复用，没有重算或按结果重试。

交付包括预注册、源代码和实际补丁、两个驱动ELF、原生成器604浓度/13状态精确重放、24组候选的全部查询/随机状态/锚状态、所有逐源评分、旧气团边界与贡献审计、原始历史输入、成本、独立复算及SHA。冻结O24源码、参数、ELF和1153文件校验继续PASS；A2正常与B2源域参考保持原身份。
'''
    (O/'中文科学裁决报告.md').write_text(report,encoding='utf8')
    (O/'FOR_PRO_原因与后续边界.md').write_text('E3已找到一条受控原因链：该type10丁烷模型下沉改变气团高度，继而需要使用不同高度的水平风。相同GADEN细核/噪声/几何/读出，固定平面晚段0/20，自由3D20/20（两流）；去w仍20/20，去浮力大幅变弱且不稳定；保持3D运动却锁定u/v到0.7m，最后两站又0/10，连续源对真源组合由4/4降到0/4。注意原生GADEN负小数坐标截断还会允许负z中心，旧世界物理边界资格应降级；严格floor对照全程无越界且仍出现相同垂向机制，直接扣除旧越界贡献仍30/30检出。普通严格3D连续源对8/8、未知幅度6/8、二值4/8；只有4世界x2预测，不是全域定位或主创新成功。未运行ROS或改变O24。\n',encoding='utf8')
    # Portable inputs include the original nonuniform saved frames, not new worlds.
    parent=O/'parent_pair';(parent/'original_E3_decomposition').mkdir(parents=True,exist_ok=True);(parent/'schedule').mkdir(exist_ok=True)
    for name in ['FILAMENT_CONTRIBUTIONS.csv','DECOMPOSED_QUERIES.csv']:shutil.copy2(P/'original_E3_decomposition'/name,parent/'original_E3_decomposition'/name)
    for world in ['true_r0','true_r1','rival_r0','rival_r1']:
        dest=parent/'worlds'/world/'saved_world';dest.mkdir(parents=True,exist_ok=True)
        for path in (P/'worlds'/world/'saved_world').glob('iteration_*'):shutil.copy2(path,dest/path.name)
        for name in ['TASK.json','RESPONSES.csv','PHYSICAL_FRAME_TIME.csv','REPLAY_QA.json','RNG.GAUSSIAN.initial.txt','RNG.UNIFORM.initial.txt','RNG.cache.f32','RNG.cache.initial.txt','RNG.cache.final.txt']:shutil.copy2(P/'worlds'/world/name,dest.parent/name)
    shutil.copytree(P/'historical_controls',O/'historical_controls',dirs_exist_ok=True);shutil.copytree(P/'parent_audit',O/'original_native_cache',dirs_exist_ok=True);shutil.copytree(P/'build_source',O/'build_source',dirs_exist_ok=True);shutil.copy2(P/'native_runtime/libbsc.so',O/'libbsc.so')
    code=O/'code';code.mkdir(exist_ok=True)
    for p in Path(__file__).parent.iterdir():
        if p.is_file():shutil.copy2(p,code/p.name)
    for name in ['Environment.cpp','RunningSimulation.cpp','MathUtils.instrumented.hpp','YAML_Conversions.hpp']:
        d=Path(__file__).parent/'core_patch';d.mkdir(exist_ok=True);shutil.copy2(O/'core_patch'/name,d/name)
    portable=O.parent/('E3_TRANSPORT_CAUSE_PORTABLE_QA_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));shutil.copytree(O,portable,ignore=shutil.ignore_patterns('__pycache__'))
    env=dict(os.environ,E3_CAUSE_OUTPUT=str(portable),E3_PAIR_OUTPUT=str(portable/'parent_pair'),OPENBLAS_NUM_THREADS='1');r=subprocess.run([sys.executable,'-X','utf8',str(portable/'code/analyze.py')],env=env,capture_output=True,encoding='utf8',timeout=90);assert r.returncode==0,r.stderr
    compared=[]
    for p in O.glob('*.csv'):
        assert sha(p)==sha(portable/p.name),p.name
        compared.append(dict(path=p.name,sha256=sha(p)))
    assert sha(O/'ANALYSIS_SUMMARY.json')==sha(portable/'ANALYSIS_SUMMARY.json')
    put(O/'INDEPENDENT_QA.json',dict(status='PASS_SAME_KERNEL_CAUSAL_AND_PORTABLE_QA',original604queries_exact=True,original13anchor_states_exact=anchors,prediction_initial_states_shared=True,Gaussian_cache_matches_preexisting_stream_first1000values=True,completed_native_processes=27,formal_prediction_calls=24,completed_calls_not_retried=True,all_strict_bounds_candidate_states_in_domain=True,old4world_frames_original_SHA_unchanged=1372,frozen_O24_guard='PASS',portable_tables_byte_exact=compared,summary_byte_exact=True,portable_directory=str(portable),new_ROS=0))
    evidence=Path(__file__).parent/'evidence';evidence.mkdir(exist_ok=True)
    for p in O.iterdir():
        if p.is_file() and p.suffix in ['.json','.csv','.md'] and p.name!='OccupancyGrid3D.csv' and p.stat().st_size<2000000:shutil.copy2(p,evidence/p.name)
    print('PASS_CAUSAL_REPORT_AND_RECOMPUTATION',len(compared),flush=True)

def archive():
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,encoding='utf8').strip();remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/codex/o24-e3-transport-cause-20261025'],cwd=REPO,encoding='utf8').split()[0];assert commit==remote
    put(O/'GITHUB_DELIVERY_RECEIPT.json',dict(commit=commit,branch='codex/o24-e3-transport-cause-20261025',url='https://github.com/kris-yun/uav-gsl-isj/commit/'+commit,remote_verified=True))
    files=sorted(p for p in O.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='PAYLOAD_SHA256.json');manifest=[dict(path=p.relative_to(O).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in files];put(O/'PAYLOAD_SHA256.json',manifest);files.append(O/'PAYLOAD_SHA256.json');size=sum(p.stat().st_size for p in files);assert size<134217728
    dest=DOWNLOADS/'O24_E3_TRANSPORT_CAUSE_20261025.zip';assert not dest.exists()
    with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,'E3_TRANSPORT_CAUSE_20261025/'+p.relative_to(O).as_posix())
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        for r in manifest:assert hashlib.sha256(z.read('E3_TRANSPORT_CAUSE_20261025/'+r['path'])).hexdigest()==r['sha256']
    digest=sha(dest);dest.with_suffix('.zip.sha256').write_text(digest+'  '+dest.name+'\n',encoding='ascii');receipt=dict(status='PASS_COMPLETE_PAYLOAD_SHA256_READBACK',zip=str(dest),zip_bytes=dest.stat().st_size,zip_sha256=digest,payload_files=len(manifest),uncompressed_bytes=size,commit=commit,frozen_O24_unchanged=True,new_ROS=0,causal_scope='case-specific source response mechanism, not a new full-domain localization result');put(dest.with_suffix('.zip.receipt.json'),receipt)
    shutil.copy2(O/'中文科学裁决报告.md',DOWNLOADS/'O24_E3_输运原因已定位_中文报告_20261025.md');shutil.copy2(O/'FOR_PRO_原因与后续边界.md',DOWNLOADS/'O24_E3_输运原因_给Pro说明_20261025.md');print(json.dumps(receipt,ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','archive']);a=parser.parse_args();prepare() if a.mode=='prepare' else archive()
