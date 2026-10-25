"""Verify and package the completed oracle wind intervention without new runs."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,shutil,struct,subprocess,sys,zipfile
import numpy as np
from analyze import O,H,P,load,put,rows

REPO=Path(__file__).resolve().parents[2];DOWNLOADS=Path('C:/Users/50176/Downloads')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def prepare():
    plan=load(O/'PREREGISTERED_WIND_CONTRACT.json');cost=load(O/'EXECUTION_RECEIPT.json');assert cost['status'].startswith('PASS_')
    for r in load(O/'INPUT_SHA256.json'):assert sha(O/r['path'])==r['sha256']
    scene=load(O/'inputs/E3_scene.json');oracle=load(O/'E3_ORACLE_scene.json');assert all(scene[k]==oracle[k] for k in scene if k!='wind_xy') and set(scene)==set(oracle)
    raw=(O/'inputs/wind_iteration_0').read_bytes();assert sha(O/'inputs/wind_iteration_0')==plan['wind']['sha256'];data=np.frombuffer(raw,dtype='<f4',offset=8).reshape(-1,3)
    for r in rows(O/'REFERENCE_WIND_SAMPLING.csv'):
        index=int(r['voxel_i'])+110*(int(r['voxel_j'])+120*int(r['voxel_k']));expected=np.array([float(r[k]) for k in ['reference_u','reference_v','reference_w']],np.float32);assert np.array_equal(expected,data[index])
    score_errors=[]
    for source in ['true','rival']:
        for pred in plan['prediction_streams']:
            control=O/'runs'/f'control_{source}_{pred["id"]}';prior=H/'runs'/f'E3_{source}_{pred["id"]}_long220';actual=load(control.with_suffix('.json'));expected=load(prior.with_suffix('.json'))
            assert actual['after']==expected['after'] and sha(control.with_suffix('.f32'))==sha(prior.with_suffix('.f32'))
            assert sha(Path(str(control)+'.particles.bin'))==sha(Path(str(prior)+'.particles.bin'))
            altered=load((O/'runs'/f'oracle_{source}_{pred["id"]}').with_suffix('.json'));assert actual['before']==altered['before'] and altered['history']['actual_warmup_steps']==1100
            for wind,prefix in [('GMRF',control),('oracle',O/'runs'/f'oracle_{source}_{pred["id"]}')]:
                freq=np.fromfile(prefix.with_suffix('.f32'),dtype='<f4').astype(float);valid=np.array(scene['occupancy'])==0;logodds=np.array(scene['logodds']);measured=1-1/(1+np.exp(logodds));confidence=np.array(scene['confidence']);factors=1-.2*np.abs(measured[valid]-freq[valid])*confidence[valid];score=float(np.prod(factors));recorded=load(prefix.with_suffix('.json'))['score'];error=abs(score-recorded)/recorded;assert error<1e-10;score_errors.append(error)
    assert cost['total_wall_s']<900 and cost['max_child_CPU_s']<120
    response=rows(O/'STATION_RESPONSE_COMPARISON.csv');z=[r for r in response if r['source']=='true' and r['wind']=='horizontal_oracle'];assert all(float(r['PID_window_frequency'])==1 for r in z if int(r['stop']) in [8,9]);assert all(float(r['PID_window_frequency'])==0 for r in z if int(r['stop']) in [10,11,12,13]);assert all(int(r['correct_true_world_by_prediction'])==0 for r in rows(O/'SOURCE_PAIR_SUMMARY.csv'))
    for stop in range(8,14):
        index=scene['stops'][stop-1]['cell'];flat=index[0]+scene['nx']*index[1];assert int(rows(O/'REFERENCE_WIND_SAMPLING.csv')[flat]['native3D_cell_state'])==0
    frozen=Path('D:/ZYC/A-gas/workspace/FROZEN_O24_1M2_SCREEN12_20261024/verify_frozen_baseline.py');r=subprocess.run([sys.executable,'-X','utf8',str(frozen)],capture_output=True,encoding='utf8',timeout=60);assert r.returncode==0;put(O/'FROZEN_O24_GUARD.json',dict(status='PASS',stdout=r.stdout,stderr=r.stderr))
    pair=O/'parent_pair';pair.mkdir(exist_ok=True);shutil.copy2(P/'PHYSICAL_WINDOWS.csv',pair/'PHYSICAL_WINDOWS.csv')
    hist=O/'parent_history/runs';hist.mkdir(exist_ok=True,parents=True)
    for source in ['true','rival']:
        for pred in plan['prediction_streams']:
            name=f'E3_{source}_{pred["id"]}_long220.timeseries.csv';shutil.copy2(H/'runs'/name,hist/name)
    shutil.copytree(P/'build_source',O/'build_source',dirs_exist_ok=True);shutil.copy2(H/'history_observer.cpp',O/'history_observer.cpp');shutil.copy2(P/'native_runtime/libbsc.so',O/'libbsc.so');shutil.copy2(P/'code/kernel.cpp',O/'PID_kernel.cpp')
    for p in Path(__file__).parent.iterdir():
        if p.is_file():(O/'code').mkdir(exist_ok=True);shutil.copy2(p,O/'code'/p.name)
    verdict=dict(primary='HORIZONTAL_WIND_ORACLE_PARTIAL_RESPONSE_RESCUE_NO_SOURCE_PAIR_RESCUE',
        positive='At source_height0.7m reference horizontal slice, both true-source prediction streams restore PID hits at stops8and9.',
        negative='At stops10to13 both streams still have zeroPID hit frequency; all true physical worlds remain pair-rank2.',
        native_full_observation_map_wrong_advantage=dict(GMRF=[884.1401927886525,1075.7353928348418],horizontal_oracle=[1022.0859502034046,1576.5440466341881]),
        causal_scope='Replacing only this predefined horizontal wind input has a conditional effect on response but is insufficient to restore source ranking; not evidence that wind never matters or2D alone is uniquely causal.',
        remaining=['coarse horizontal projection and unresolved height-dependent flow','2D transport and obstacle representation','native candidate transport/physical-readout structural approximations'],
        geometry='36of1132PMFS-free coarse centers are nonfree in3D at0.7m; both source centers and critical8to13centers are free. Original mask retained.',
        oracle_permission='full-world reference wind is offline diagnostic privilege, not deployment input',
        full1132cell_new_posterior=False,new_worlds=0,new_ROS=0,C_arm_started=False,parameters_retuned=False)
    put(O/'SCIENTIFIC_VERDICT.json',verdict)
    text=f'''# E3 水平参考风单因素诊断：中文科学裁决

## 结论

**参考水平风恢复了部分真源响应，但没有恢复锁定源对排序。**局地风输入对响应有影响；“只把GMRF改成这个准确采样的水平切片就能解决”不成立。结合上一轮，单独延长预热和本轮单独换水平风，都没有救回E3。尚不能因此把全部残差归于二维运动维数。

## 1. 本轮只改变什么

两源仍为(-4,-1.9,0.7)及(-2.375,-4.875,0.7)，两条预测随机初始化/缓存均沿用。原生二维运动、掩膜、噪声0.5、固定220秒预热、记录200×0.1秒、D=0.2、PID质量/展宽/LOS与0.1ppm阈值全部保持。模型ELF未重新编译，SHA仍为e547d792336e594f12a88405b99f1e2001a0f4c7cf1a5f7bc814f200f79eeacd。

唯一改变为scene.wind_xy。使用旧E3实际加载的单个原生风文件，SHA135690ce4679f43bb02d7d40fe39b338a250f2aa94cf3e71d0f2dbf8bbe4705a。调用原生Environment坐标变换与WindSequence读数，在全部44×48个PMFS粗格中心、共同候选高度z=0.7米查询原生体素风，取u/v；没有插值、平均、平滑、缩放、择优换层或只改真源附近。

这只是“原生细体素在粗格中心的水平切片参考”，不是精确连续二维流，也不包含沿真实三维路径随高度变化的风。w分量只审计，从未送入二维预测器。完整风场只用于明示的离线oracle诊断，不能混入局地风部署算法成绩。

所有初始RNG状态相同。换风后气团存活、运动及随机数消耗会改变，所以不是后续所有路径逐气团相同。未增加或择优挑选随机种子。

## 2. 资格是否可靠

原生C++导出与独立Python对二进制float32风数组的2112个查询逐项完全一致，轴顺序、索引、尺寸110×120×30、0.1米物理网格和版本3.0核对通过。除wind_xy外，两个scene的其他全部字段完全相同。

先把四个220秒GMRF点候选原样重放：f32地图、RNG终点及完整气团轨迹文件SHA与上轮完全一致，再执行四个oracle点预测。所有预热确实1100步、220秒。原生全观测图评分由独立NumPy重算，最大相对误差{max(score_errors):.3g}。

原二维1132个自由粗格中，36个粗格中心在z=0.7米的实际3D地图不是自由空间；两源中心及第8–13站中心均自由。未挖格、改掩膜或填充这些位置的参考风。36处不一致会限制“二维模型完全物理正确”的资格，但不是坐标索引读错，也不能据此直接声称它们就是错源唯一原因。

两类风在这些自由粗格的水平向量RMS差约0.293m/s；GMRF水平RMS约0.225m/s，参考约0.358m/s，参考竖直分量RMS约0.114m/s。全局差异不是因果贡献百分比，也不是只有传感器位置的风估计误差。

## 3. 关键测点发生了什么

下表是同一200步预测读出中的PID窗口检出频率，两条预测流分别报告；不是实际物理世界成功率。

| 真源测点 | GMRF、220秒 | 水平参考风、220秒 |
|---|---:|---:|
| 第8站 | 0.28 / 0.60 | 1.00 / 1.00 |
| 第9站 | 0 / 0 | 1.00 / 1.00 |
| 第10站 | 0 / 0 | 0 / 0 |
| 第11–13站 | 均为0 | 仍均为0 |

第9站参考风下平均浓度约0.148/0.204ppm，恢复了正检出；但气团中心占格频率仍是0，再次说明中心事件与PID事件有差异。第10站平均约0.0166/0.0311ppm，**不是浓度精确零，而是低于检出阈值**。第11–13站正式读出的浓度仍全零。

正结果和负结果同时保留，没有根据第9站改善更改源、阈值、风层或评分。参考风替换有局部作用，但未弥补更远站位的响应缺失。

## 4. 源对排名是否恢复

没有。对已有四个真实物理世界、两条预测流，采用同一站位均衡兼容评分，连续五窗不当成五个独立世界。中心与PID两读出、全13站与第8–13站两个范围，两个真源物理实现×两预测流均仍偏好竞争源，即0/4真源组合反超；四个独立物理世界没有因重复评价变成八个。

PID事件的真源相对证据有局部改善。例如true_r0全13站，真源减错源log兼容差由-1.269/-1.195改善到两流均-0.893，但没有跨过0。此分数不是正规化观测密度或校准Bayes因子。

保留原生整个观测地图评分时，锁定错源相对真源的优势如下：

| 预测流 | GMRF、220秒 | 水平参考风、220秒 |
|---|---:|---:|
| r0 | 884倍 | 1022倍 |
| r1 | 1076倍 | 1577倍 |

因此实测站位的响应改善并未转换为原生全观测图评分改善；空间证据扩展仍可能放大残差。不能用某一站恢复直接宣布定位成功。

本轮只有固定两源点候选；没有重算完整1132源格的后验、MAP或Top-5%，没有新的ROS误差。旧E3、A2正常参考、B2源域诊断及其身份保留；本轮没有对A2替换oracle风，不能声称完成新算子的全域反退化验证。

## 5. 残差可以归于二维吗

现在有两个明确的“单因素修复不充分”结果：220秒历史干预未修复；本轮在220秒历史上改用水平参考风也未修复。可以停止单独增大预热和反复调水平风输入来救同一案例。

但二维输运是重要竞争解释，尚非被唯一识别的原因。当前还保留粗格恒定风、固定高度切片、二维障碍/移动规则以及附加普通浓度读出等近似。实际3D风随高度变化、w分量以及质量相关漂移未进入本轮二维路径。即使水平切片在格中心读对了，也不代表完整源—传感器输运路径已经正确。

只读几何诊断还发现，oracle轨迹中平均约236–267个真源气团中心在0.7米3D图中非自由，约占气团时间样本的6.6%–9.5%；竞争源约16.6%–18.1%。这些是二维路径在真实高度上的一致性风险，逐流数据全部报告。没有按3D真值偷偷过滤、绕障或挖图来救结果。仅凭这些计数也不能证明消除它们就能恢复定位。

因此最准确归因是：**风输入误差对部分站位有作用，但当前二维空间输运表示与物理响应之间仍存在未消除的残差。**本轮不能断言“GMRF无关”或“二维是唯一根因”。下一项若要归因传播维度，需要在同一参考资料、释放/扩散、时钟及读出下设计单独控制，避免把更换物理引擎、噪声、几何和维度混为一个处理。本轮没有自动启动C。

## 6. 资源与交付

4次GMRF精确技术复算、4次新oracle点前向及其PID读出均一次执行。记录编译及运行总墙钟约{cost['total_wall_s']:.2f}秒，最大单命令CPU约{cost['max_child_CPU_s']:.2f}秒，低于900/120秒上限。220秒为模型时间；本轮是原生函数离线计算，不是实时ROS。

没有新气体世界、ROS、神经训练、改参数、换源或新种子。冻结O24的1153文件校验通过。原四个物理世界的完整气团帧仍见上一配对物理ZIP；本包保存本轮全部候选轨迹、原始PID读出、输入风文件、原生采样表、控制重放、成本、源码、独立QA及逐文件SHA。
'''
    (O/'中文科学裁决报告.md').write_text(text,encoding='utf8')
    (O/'FOR_PRO_交接说明.md').write_text('本轮只换水平风：全44×48粗格中心、固定z=0.7、原生E3风文件u/v，其他字段与ELF完全不变。恢复了真源第8/9站PID检出，第10–13站仍未检出；所有真源世界源对仍排第二，原生全观测图错源优势约1022/1577倍。不能说GMRF无关，也不能因失败就说二维唯一主因。固定层/粗格风与3D空间表示仍未分开：36个二维自由粗格中心在真实高度非自由，目标与源中心本身自由。未改图、过滤轨迹、训练或启动C/ROS。完整源码、负例和费用已推送独立分支。\n',encoding='utf8')
    # Copy after composing the final files; source versions become archive inputs.
    for p in Path(__file__).parent.iterdir():
        if p.is_file():shutil.copy2(p,O/'code'/p.name)
    portable=O.parent/('E3_ORACLE_PORTABLE_QA_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));shutil.copytree(O,portable,ignore=shutil.ignore_patterns('__pycache__'))
    env=dict(os.environ,E3_ORACLE_OUTPUT=str(portable),E3_HISTORY_OUTPUT=str(portable/'parent_history'),E3_PAIR_OUTPUT=str(portable/'parent_pair'),OPENBLAS_NUM_THREADS='1')
    r=subprocess.run([sys.executable,'-X','utf8',str(portable/'code/analyze.py')],env=env,capture_output=True,encoding='utf8',timeout=90);assert r.returncode==0,r.stderr
    compared=[]
    for p in O.glob('*.csv'):
        assert sha(p)==sha(portable/p.name),p.name
        compared.append(dict(path=p.name,sha256=sha(p)))
    assert sha(O/'RESULT_SUMMARY.json')==sha(portable/'RESULT_SUMMARY.json')
    put(O/'INDEPENDENT_QA.json',dict(status='PASS_ORACLE_DECODER_SAME_CONTROL_SCORE_AND_PORTABLE_ANALYSIS',independent_wind_queries_exact=2112,GMRF_controls_map_RNG_and_all_particle_bytes_exact=4,max_native_score_relative_error=max(score_errors),tables_byte_exact=compared,result_summary_byte_exact=True,portable_directory=str(portable),new_worlds=0,new_ROS=0,only_wind_input_changed=True))
    evidence=Path(__file__).parent/'evidence';evidence.mkdir(exist_ok=True)
    for p in O.iterdir():
        if p.is_file() and p.suffix in ['.json','.csv','.md'] and p.name not in ['OccupancyGrid3D.csv','E3_ORACLE_scene.json'] and p.stat().st_size<2000000:shutil.copy2(p,evidence/p.name)
    print('PASS_WIND_ORACLE_REPORT_AND_PORTABLE_QA',len(compared),flush=True)

def archive():
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,encoding='utf8').strip();remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/codex/o24-e3-wind-oracle-20261025'],cwd=REPO,encoding='utf8').split()[0];assert commit==remote
    put(O/'GITHUB_DELIVERY_RECEIPT.json',dict(commit=commit,branch='codex/o24-e3-wind-oracle-20261025',url='https://github.com/kris-yun/uav-gsl-isj/commit/'+commit,remote_verified=True))
    files=sorted(p for p in O.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='PAYLOAD_SHA256.json');manifest=[dict(path=p.relative_to(O).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in files];put(O/'PAYLOAD_SHA256.json',manifest);files.append(O/'PAYLOAD_SHA256.json');size=sum(p.stat().st_size for p in files);assert size<134217728
    dest=DOWNLOADS/'O24_E3_HORIZONTAL_WIND_ORACLE_20261025.zip';assert not dest.exists()
    with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,'E3_HORIZONTAL_WIND_ORACLE_20261025/'+p.relative_to(O).as_posix())
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        for r in manifest:assert hashlib.sha256(z.read('E3_HORIZONTAL_WIND_ORACLE_20261025/'+r['path'])).hexdigest()==r['sha256']
    digest=sha(dest);dest.with_suffix('.zip.sha256').write_text(digest+'  '+dest.name+'\n',encoding='ascii');receipt=dict(status='PASS_FULL_PAYLOAD_SHA256_READBACK',zip=str(dest),zip_bytes=dest.stat().st_size,zip_sha256=digest,uncompressed_bytes=size,payload_files=len(manifest),commit=commit,oracle_only_not_deployable=True,new_worlds=0,new_ROS=0);put(dest.with_suffix('.zip.receipt.json'),receipt)
    shutil.copy2(O/'中文科学裁决报告.md',DOWNLOADS/'O24_E3_水平参考风诊断_中文报告_20261025.md');shutil.copy2(O/'FOR_PRO_交接说明.md',DOWNLOADS/'O24_E3_水平参考风诊断_给Pro说明_20261025.md');print(json.dumps(receipt,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','archive']);a=p.parse_args();prepare() if a.mode=='prepare' else archive()
