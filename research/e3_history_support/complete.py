"""Evidence QA and incremental delivery for the completed history intervention."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,shutil,subprocess,sys,zipfile
import numpy as np
from analyze import O,OLD,load,put,rows

REPO=Path(__file__).resolve().parents[2]
DOWNLOADS=Path('C:/Users/50176/Downloads')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def prepare():
    plan=load(O/'PREREGISTERED_HISTORY_CONTRACT.json');assert plan['fixed_history_s']==220
    for r in load(O/'INPUT_SHA256.json'):assert sha(O/r['path'])==r['sha256']
    for r in load(O/'NATIVE_PARITY.json'):assert r['all_floats_exact'] and r['RNG_endpoint_exact']
    for case in ['E3','A2']:
        for source in ['true','rival']:
            for pred in plan['prediction_streams']:
                short=load(O/'runs'/f'{case}_{source}_{pred["id"]}_native.json');long=load(O/'runs'/f'{case}_{source}_{pred["id"]}_long220.json')
                assert short['before']==long['before']
                assert short['history']['first_exit_rng']==long['history']['first_exit_rng']
                assert long['history']['actual_warmup_steps']==1100
    frame=rows(O/'AGE_AND_SPATIAL_REACH.csv');critical=[r for r in frame if r['source']=='true' and r['history']=='long220' and int(r['stop'])>=9]
    assert len(critical)==10 and all(float(r['center_hit'])==float(r['PID_window_hit'])==0 for r in critical)
    assert all(float(r['max_spread_equivalent_age_s'])>230 for r in critical)
    summary=rows(O/'SOURCE_PAIR_SUMMARY.csv');assert all(int(r['true_world_correct'])==0 for r in summary)
    cost=load(O/'EXECUTION_RECEIPT.json');assert cost['total_wall_s']<900 and cost['max_child_CPU_s']<120
    baseline=Path('D:/ZYC/A-gas/workspace/FROZEN_O24_1M2_SCREEN12_20261024/verify_frozen_baseline.py')
    checked=subprocess.run([sys.executable,'-X','utf8',str(baseline)],capture_output=True,encoding='utf8',timeout=60);assert checked.returncode==0
    put(O/'FROZEN_O24_GUARD.json',dict(status='PASS',stdout=checked.stdout,stderr=checked.stderr))
    parent=O/'parent_control';(parent/'event_control').mkdir(parents=True,exist_ok=True)
    shutil.copy2(OLD/'PHYSICAL_WINDOWS.csv',parent/'PHYSICAL_WINDOWS.csv')
    for source in ['true','rival']:
        for pred in plan['prediction_streams']:
            for extension in ['particles.bin','timeseries.csv']:
                name=f'{source}_{pred["id"]}.{extension}';shutil.copy2(OLD/'event_control'/name,parent/'event_control'/name)
    shutil.copytree(OLD/'build_source',O/'build_source',dirs_exist_ok=True)
    shutil.copy2(OLD/'event_control/kernel',O/'native_PID_kernel')
    shutil.copy2(OLD/'code/kernel.cpp',O/'native_PID_kernel.cpp')
    shutil.copy2(OLD/'native_runtime/libbsc.so',O/'libbsc.so')
    shutil.copy2(OLD/'native_runtime/OccupancyGrid3D.csv',O/'OccupancyGrid3D.csv')
    put(O/'READONLY_ENGINEERING_NOTES.json',dict(first_formal_campaign_attempt=1,failed_formal_forward_calls=0,retuned_parameters=False,compiler_warnings='Original VisibilityMap narrowing warnings retained; compilation returned0.',adhoc_diagnostic_parser_failure='A convenience print initially looked for exact geometric cell centers, but actual saved sensor positions are offset. StopIteration; no simulation was rerun. Final analysis uses frozen point_id, not inferred center equality.'))
    verdict=dict(primary='FIXED220_HISTORY_EXTENSION_DOES_NOT_RESCUE_E3',
        establishes=['Native warmup stops around18to20s for the true source; intervention actually reaches220s','Long intervention contains about240s-age particles, so old-state support was genuinely added','Both true-source predictions remain zero in center andPID event at stops9to13','All true physical worlds remain pair-rank2 with both operators and both prediction streams','Full-map native score still favors the locked rival by about884and1076times'],
        interpretation='Insufficient warmup alone does not explain the observed persistent response mismatch in these fixed conditions. Residual error concerns spatial transport/reach; local GMRF versus2D representation has not been independently separated.',
        does_not_establish=['all warmup strategies fail','wind alone is the unique cause','2D alone is the unique cause','full1132cell new posterior or ROS localization results','A2 full-domain nondegradation'],
        A2='Two-hypothesis normal guard changes toward true covering-cell center in both streams; not full-domain improvement or harm rate.',
        no_new_physical_worlds=True,no_ROS=True,frozen_baseline_unchanged=True)
    put(O/'SCIENTIFIC_VERDICT.json',verdict)
    report=f'''# E3 传播历史支撑最小干预：中文科学裁决

## 结论

**固定220秒预热未恢复E3真源响应，也未恢复锁定源对排名。**这次已实际控制预热终止，不能再把“本轮候选只有约40秒龄期，而真实观测依赖100–127秒气团”直接当成预热不足的因果证明。

现有证据将问题收紧为：**即使允许候选状态变老，局地GMRF驱动的二维输运仍未把足够气体带到关键测点附近，造成源条件响应错序。**究竟由局地风外推还是二维输运约束主导，仍需分别控制；本轮没有偷偷换真风或升级三维。

## 1. 干预事前如何固定

旧E3第8–13站真实浓度贡献的加权99%气团年龄为208.3秒。按事前唯一规则向上取20秒整倍数，预热固定220秒；不依结果再试150/180/300等时长。原生warmup步长0.2秒，故干预1100步；记录仍为200步×0.1秒。

两个固定E3源不变：(-4,-1.9)与(-2.375,-4.875)，源高仍0.7米。沿用上一轮两套Gaussian表及uniform初始化，场景、局地GMRF、二维运动、噪声0.5、源强质量转换、sigma/gamma、障碍LOS、0.1ppm阈值和观测位置均不变。

只在隔离工具中改变预热终止：原生第一个气团离域即停止；干预继续到220秒，离域气团照常移除，剩余气团正常继续更新。这个继续执行也补上原本退出分支之后未再执行的更新，不改变风场或移动规则。原生warmup/record分别0.2/0.1秒的数值语义保留；它不是统一步长的新物理求解器。

相同初态与首次离域前的RNG端点逐项完全一致。由于长历史额外消耗随机数，分叉之后不能宣称逐气团路径仍相同。这是共随机初始化、精确公共前缀的配对程序干预，不是全部后续路径锁定。

## 2. 资格与执行

先重放E3原call589/660与A2原call2662/2661：地图2112/1600个float32以及RNG终点均完全一致。新增被动记录器未改变原生短历史输出。四个E3短历史点预测又与上轮对应f32和RNG端点完全一致。

实际16次点源函数调用：E3两点×两流×短/长两种历史共8次；A2正常对照同样8次。另有4次历史叶技术重放。没有新增气体世界、ROS、算法训练或新的随机初始化。已有四个配对物理世界仅被重复评价，不增加独立样本数量。

## 3. 真源响应恢复了吗

| 指标 | 原生历史 | 固定220秒历史 |
|---|---:|---:|
| 真源预热时长，两流 | 20.4 / 17.8秒 | 220 / 220秒 |
| 记录期最大展宽等价龄期 | 40.4 / 37.8秒 | 239.7 / 240.1秒 |
| 第9–13站非零中心响应 | 一流0/5，另一流1/5 | 两流均0/5 |
| 第9–13站非零PID检出响应 | 一流0/5，另一流1/5 | 两流均0/5 |
| 两个真源物理实现×两预测流，锁定源对选对 | 0/4 | 0/4 |

第8站有局部改善，PID窗口检出率分别由0.02/0.06升到0.28/0.60，完整保存。它没有转化为源对排名翻转。不能把“某站有响应”当成整体定位恢复。

长历史真源轨迹中，约22%–29%的气团时间样本具有超过100秒的展宽等价龄期，说明干预确实产生了老气团，而不是名义220秒却全部早退。第11–13站所有记录时刻、所有真源气团中心距传感器的最小距离仍约1.50–1.62米。

## 4. 排名和评分

对同一批四个真实物理世界，逐站均衡的D=0.2兼容项保持不变。连续五窗不算五个独立物理实现；工作分数不冒称校准NLL或Bayes因子。两源假设的MAP只表示二选一排序。

中心事件和普通PID事件、全13站和第8–13站两个范围，真源世界在两预测流中全部仍排第二。整体4/8来自竞争源世界选对，不能包装成50%独立世界成功率或定位改进。

在旧E3原生观测地图上，用原生全图评分直接评价这两个点候选：错源优势由约1302倍变为884倍（流0），由约976倍变为1076倍（流1）。一流改善、一流恶化，均未翻转；不声称稳定证据增益。

没有为全部1132合法格生成长历史响应库，因此没有新的全域真源rank、MAP或Top-5%定位成绩。旧官方闭环MAP3.3899米、原Top-5%3.2476米、rank131–150保留，不替换成此次两源指标。

## 5. 是否只是LOS或Gaussian截断

完成干预后，对已保存轨迹另做只读宽松浓度上界：不扣遮挡、不截Gaussian尾部；此上界绝不进入评分或选点，正式PID算子一直保留原生LOS与3σ截断。

长历史的第9–13站，在两真源预测流中，这个上界仍全部低于0.1ppm。第9站最大约0.062/0.074ppm，第10站约0.0010/0.0063ppm，后3站更低。故在这些保存轨迹上，单修LOS或截断同样不足以救回。第8站是例外，已保留。

这进一步支持空间输运/驻留位置未被正确表示，而不是单纯读出门限或气团年龄不足。它仍不是所有随机路径必然不可达的证明，只有两个预测随机流。

## 6. A2正常反例

A2使用其自身保存的最终局地GMRF、地图、原生观测与RNG记录，未借用E3风。正常真源覆盖格中心与原最终MAP格中心相距0.25米，都是靠近真源的候选，不把另一点称为严重错源。

两点的真源覆盖格/竞争格原生分数比：流0由0.824升至2.050，流1由0.953升至1.552。该局部守护没有出现反向排斥真源，但它不等于完整1195格后验无损，更不能声称ROS误差改善。没有A2全域长历史预测，因此完整反退化资格仍未建立。

## 7. 现在能归因到哪里

1. **预热不足单独解释：本次干预不支持。**明显延长历史、实际生成老气团，仍没有修复目标响应和排序。不能继续无限加时长。
2. **局地GMRF误差：未单独检验。**可能把水平传播方向、速度和驻留区预测错；本轮保持它不变。
3. **二维输运限制：未单独检验。**可能遗漏越障、竖直交换及不同高度通道；本轮保持它不变。

因此直接失败环节是已明确的“候选输运空间响应错序”，不是主动规划复杂度不足。风和二维结构可能相互耦合，不能从本轮负结果强行给二者分配百分比，也不能宣布某一者唯一根因。

后续如果继续归因，只需针对风输入与传播维度分别做单因素对照；应另立有限合同。全场真风最多作为明确命名的诊断oracle，不能混入合法局地风算法成绩。本轮到此停止，没有自动启动这些对照。

## 8. 资源、交付与边界

编译、技术重放、16点源预测及4次PID读出的已记录总墙钟约{cost['total_wall_s']:.2f}秒，最大单命令CPU约{cost['max_child_CPU_s']:.2f}秒，均在900/120秒上限内。220秒是离线模型时间，不是实时ROS墙钟。正式调用均一次执行，不因成绩重试。

完整增量包含：预注册、输入SHA、精确重放、短/长响应、长历史气团轨迹、随机前缀验证、逐世界源对分数、A2局部反例、成本、源代码、全部日志、只读上界及复算QA。旧4个物理世界的逐原始查询帧仍在上一份O24_E3_CAUSAL_PAIR_EVIDENCE_20261025.zip（SHA303b217477c362af336f837ac6b6586a5f99bac7f29ca594bdf08cb9cfed03b6）中，不重新生成或覆盖。

科学定位：有针对性的普通模型因果诊断，不是主创新PASS、独立未知源定位验证或跨House泛化。冻结O24、旧E3及A2/B2历史证据均保持原身份。
'''
    (O/'中文科学裁决报告.md').write_text(report,encoding='utf8')
    (O/'FOR_PRO_交接说明.md').write_text('220秒历史干预已完成：确实出现约240秒龄期气团，但E3第9–13站两流的中心和PID事件仍全零，真源物理世界仍全部源对rank2，原生全图点候选错源优势仍约884/1076倍。故不要继续把40秒对100–127秒年龄差当预热不足的因果证明，也不要继续加长历史。先隔离局地GMRF空间风误差与二维输运通道；两者本轮未分开。没有新ROS、世界或神经训练。A2仅局部源对守护，不冒称全域无损。\n',encoding='utf8')
    code=O/'code';code.mkdir(exist_ok=True)
    for p in Path(__file__).parent.iterdir():
        if p.is_file():shutil.copy2(p,code/p.name)
    # Fresh copy verifies that no original absolute data directory is required.
    portable=O.parent/('E3_HISTORY_PORTABLE_QA_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    shutil.copytree(O,portable,ignore=shutil.ignore_patterns('__pycache__'))
    env=dict(os.environ,E3_HISTORY_OUTPUT=str(portable),E3_PAIR_OUTPUT=str(portable/'parent_control'),OPENBLAS_NUM_THREADS='1')
    for script in ['analyze.py','diagnostic_upper.py']:
        q=subprocess.run([sys.executable,'-X','utf8',str(portable/'code'/script)],env=env,capture_output=True,encoding='utf8',timeout=90);assert q.returncode==0,(script,q.stderr)
    compare=[]
    for p in sorted(O.glob('*.csv')):
        assert sha(p)==sha(portable/p.name),p.name
        compare.append(dict(path=p.name,sha256=sha(p)))
    assert sha(O/'RESULT_SUMMARY.json')==sha(portable/'RESULT_SUMMARY.json')
    put(O/'INDEPENDENT_QA.json',dict(status='PASS_PARITY_SHARED_PREFIX_AND_PORTABLE_RECOMPUTATION',tables_byte_exact=compare,result_summary_exact=True,portable_copy=str(portable),original_baseline_guard='PASS',all8short_long_pairs_same_initial_and_first_exit_RNG=True,new_physical_worlds=0,new_ROS=0))
    evidence=Path(__file__).parent/'evidence';evidence.mkdir(exist_ok=True)
    for p in O.iterdir():
        if p.is_file() and p.suffix in ['.json','.csv','.md'] and p.name!='OccupancyGrid3D.csv':shutil.copy2(p,evidence/p.name)
    print('PASS_HISTORY_REPORT_AND_PORTABLE_QA',len(compare),flush=True)

def archive():
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,encoding='utf8').strip();remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/codex/o24-e3-history-support-20261025'],cwd=REPO,encoding='utf8').split()[0];assert commit==remote
    put(O/'GITHUB_DELIVERY_RECEIPT.json',dict(commit=commit,url='https://github.com/kris-yun/uav-gsl-isj/commit/'+commit,remote_verified=True))
    files=sorted(p for p in O.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='PAYLOAD_SHA256.json')
    manifest=[dict(path=p.relative_to(O).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in files];put(O/'PAYLOAD_SHA256.json',manifest);files.append(O/'PAYLOAD_SHA256.json')
    assert sum(p.stat().st_size for p in files)<134217728
    dest=DOWNLOADS/'O24_E3_HISTORY220_INTERVENTION_20261025.zip';assert not dest.exists()
    with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,'E3_HISTORY_SUPPORT_20261025/'+p.relative_to(O).as_posix())
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        for r in manifest:assert hashlib.sha256(z.read('E3_HISTORY_SUPPORT_20261025/'+r['path'])).hexdigest()==r['sha256']
    digest=sha(dest);dest.with_suffix('.zip.sha256').write_text(digest+'  '+dest.name+'\n',encoding='ascii')
    receipt=dict(status='PASS_COMPLETE_PAYLOAD_READBACK_SHA256',zip=str(dest),zip_bytes=dest.stat().st_size,zip_sha256=digest,payload_files=len(manifest),uncompressed_bytes=sum(p.stat().st_size for p in files),commit=commit,new_worlds=0,new_ROS=0)
    put(dest.with_suffix('.zip.receipt.json'),receipt)
    shutil.copy2(O/'中文科学裁决报告.md',DOWNLOADS/'O24_E3_220秒历史干预_中文报告_20261025.md')
    shutil.copy2(O/'FOR_PRO_交接说明.md',DOWNLOADS/'O24_E3_220秒历史干预_给Pro说明_20261025.md')
    print(json.dumps(receipt,ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','archive']);args=parser.parse_args();prepare() if args.mode=='prepare' else archive()
