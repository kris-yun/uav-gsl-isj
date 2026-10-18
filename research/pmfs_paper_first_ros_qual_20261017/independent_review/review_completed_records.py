from pathlib import Path
import csv,json,math,hashlib,re
from PIL import Image
E=Path(__file__).resolve().parent
P=E.parent.parent/'workspace/PMFS_PAPER_FIRST_ROS_QUAL_20261017'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):
 with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8-sig')))
put(E/'SCOPE.json',dict(scope='Independent read-only review of completed Sep18-derived A2/B2 ROS records. No process launch, ROS/VM connection, build, rerun, new physics or candidate support repair.',source_directory=str(P),not_full_paper_reproduction=True))
lock=read(P/'SOURCE_LOCK.json');sourcechecks=[]
for x in lock['files']:
 file=P/'official_exact'/x['path'];data=file.read_bytes();oid=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();assert oid==x['git_blob_oid'] and sha(file)==x['sha256'],x['path']
 sourcechecks.append(dict(path=x['path'],sha256=sha(file),git_blob_oid=oid,matches=True))
put(E/'OFFICIAL_SOURCE_FILES_POSTCHECK.json',dict(commit=lock['commit'],tree=lock['tree'],files=sourcechecks,all_match=True))
binary=P/'binaries/gsl_actionserver_node';build=read(P/'BUILD_RESULT.json');assert sha(binary)==build['binary_sha256']=='78ca758e1b79a8e2f9ebe0480cdbad6211baba512523ef664160c015aa1a5dec'
original=P/'official_exact/gsl_server/src/gsl_server/algorithms/PMFS/PMFS_utils.cpp';runtime=P/'source_runtime/src/gsl_server/algorithms/PMFS/PMFS_utils.cpp';before=original.read_text();after=runtime.read_text();old='for (int j = 0; j < gridMetadata.dimensions.x; j++)';new='for (int j = 0; j < gridMetadata.dimensions.y; j++)';assert before.count(old)==2 and before.replace(old,new)==after
rect=read(P/'RECTANGULAR_FIX_PRECOMMIT.json');assert sha(original)==rect['author_before_sha256'] and sha(runtime)==rect['runtime_after_sha256']
classification=read(P/'PATCH_CLASSIFICATION.json');rect_in_classification=any(x['path'].endswith('/PMFS_utils.cpp') for x in classification['patches'])
readout={int(x['group']):x for x in rows(P/'analysis/NATIVE_READOUT.csv')};n_group=0;episodes=[]
for role in ['PF24_A2_T02','PF24_B2_Q01']:
 case=P/'cases'/role;R=case/'runtime';meta=read(case/'CASE_META.json');truth=meta['source_xyz'][:2];nav=read(R/'NAVIGATION_MAP_METADATA.json');run=read(case/'RUN_RESULT.json');assert run['native_goal_count']==1 and run['result']=='NATIVE_ACTION_RETURNED'
 params=read(R/'resolved_GSL_parameters.json');typed={1:'bool_value',2:'integer_value',3:'double_value',4:'string_value'};actual={k:v[typed[v['type']]] for k,v in zip(params['names'],params['values']) if v['type'] in typed}
 required=dict(use_sim_time=False,useWindGroundTruth=False,sourceDiscriminationPower=1.,convergence_thr=1.,maxSearchTime=300.,stop_and_measure_time=.4,confidenceMeasurementWeight=1.,confidenceSigmaSpatial=1.,scale=25)
 assert all(k in actual and actual[k]==v for k,v in required.items()),role
 image_root=P/'official_exact/Environment_config/PMFS/scenarios'/meta['scenario'];cfg=(image_root/'_occupancy.yaml').read_text();image_name=re.search(r'^image:\s*(.*?)\s*$',cfg,re.M).group(1).strip('"\'');free=float(re.search(r'^free_thresh:\s*([^\n#]+)',cfg,re.M).group(1));occupied=float(re.search(r'^occupied_thresh:\s*([^\n#]+)',cfg,re.M).group(1));neg=int(re.search(r'^negate:\s*([^\n#]+)',cfg,re.M).group(1));resolution=float(re.search(r'^resolution:\s*([^\n#]+)',cfg,re.M).group(1))
 with Image.open(image_root/image_name) as image:
  grey=image.convert('L');w,h=grey.size;data=grey.tobytes();expected=bytearray()
  for y in reversed(range(h)):
   for val in data[y*w:(y+1)*w]:
    occ=val/255. if neg else (255-val)/255.;expected.append(100 if occ>occupied else 0 if occ<free else 255)
 actual_map=(R/'navigation_map.s8').read_bytes();assert bytes(expected)==actual_map and w==nav['width'] and h==nav['height'] and abs(resolution-nav['resolution'])<1e-8
 states={}
 for x in rows(R/'native_posterior_updates.csv'):states.setdefault(int(x['update']),[]).append(x)
 state_checks=[]
 for update,values in sorted(states.items()):
  probs=[float(x['source_probability']) for x in values];mass=math.fsum(probs);assert abs(mass-1)<1e-9
  alpha_err=max(abs(float(x['hit_confidence'])-(1-math.exp(-float(x['hit_omega'])**2))) for x in values);assert alpha_err<2e-14
  mx=math.fsum(p*float(x['x_m']) for p,x in zip(probs,values))/mass;my=math.fsum(p*float(x['y_m']) for p,x in zip(probs,values))/mass;var=math.fsum(p*((float(x['x_m'])-mx)**2+(float(x['y_m'])-my)**2) for p,x in zip(probs,values))/mass
  cellsize=float(values[0]['cell_size_m']);col=math.floor((truth[0]-nav['origin_x'])/cellsize);row=math.floor((truth[1]-nav['origin_y'])/cellsize);supported=any(int(x['row'])==row and int(x['col'])==col for x in values)
  nr=readout[n_group];n_group+=1;assert abs(var-float(nr['variance_m2']))<2e-5
  state_checks.append(dict(update=update,mass=mass,max_eq6_error=alpha_err,recomputed_mean=[mx,my],recomputed_variance=var,native_readout_variance=float(nr['variance_m2']),truth_source_cell=[col,row],truth_supported=supported,native_top5_xy=[float(nr['top5_x']),float(nr['top5_y'])]))
 words=(R/'native_results.csv').read_text().split();assert len(words)==6 and words[0]!='FAILED';error=float(words[3]);variance=float(words[5]);native_time=float(words[1]);last=state_checks[-1];independent_error=math.hypot(last['native_top5_xy'][0]-truth[0],last['native_top5_xy'][1]-truth[1]);assert abs(independent_error-error)<1e-5 and abs(last['recomputed_variance']-variance)<2e-5 and variance<1.
 consumed=[x for x in rows(R/'native_window_consumption.csv') if x['status']=='CONSUMED'];assert all(int(x['gas_count'])>0 and int(x['wind_count'])>0 for x in consumed)
 episodes.append(dict(role=role,case=meta['case'],truth_xy=truth,native_declared=True,declared_top5_error_logged_m=error,declared_top5_error_recomputed_from_native_coordinates_m=independent_error,native_search_system_clock_s=native_time,PMFS_use_sim_time=actual['use_sim_time'],basic_sim_clock_factor=read(R/'CLOCK_SENSOR_RATE_PREFLIGHT.json')['real_time_factor'],truth_supported=last['truth_supported'],consumed_windows=len(consumed),required_actual_ROS_parameters=required,official_PGM_map_bytes_equal=True,state_checks=state_checks,binary_sha256=sha(binary)))
review=dict(status='COMPLETED_RECORDS_RECHECKED_NOT_PAPER_REPRODUCTION_PASS',official_pinned_source_files_checked=len(sourcechecks),build_source_commit=lock['commit'],local_binary_SHA_matches=True,rectangular_fix_actual_two_y_loop_changes_verified=True,rectangular_fix_in_current_patch_classification=rect_in_classification,classification_note='If false, intermediate PATCH_CLASSIFICATION does not enumerate separately precommitted rectangular engineering repair; peer notified to reconcile final release table.',episodes=episodes,clock_definition='PMFS saveResults uses node->now()-startTime. Actual use_sim_time=false means PMFS search_s follows its system clock; separate basic_sim /clock factor5 and gas-file time mappings must not be conflated.',age_radius_reconstruction_added=False,formal_paper_statistical_reproduction_pass=False,new_experiments_in_this_review=0,records_only_no_current_VM_process_or_binary_inspection=True)
put(E/'INDEPENDENT_RECORD_REVIEW.json',review)
(E/'ROS两场记录独立复核_zh.md').write_text('''# Paper-first ROS两场记录只读复核

作者固定September源集、现存完整构建二进制和两场真实记录已核对；本聊天没有启动VM、编译或ROS。185个原样源文件的实际SHA/Git blob OID重新匹配，运行二进制副本SHA与构建回执一致。两处非方形y上界修复也已逐字确认，须作为工程补丁单列。

| 本次记录 | 原生已声明 | 声明Top5误差 | PMFS系统钟搜索时间 | 真源在候选域 |
|---|---|---:|---:|---|
| A2 T02 | 是 | 4.85474m | 33.5465s | 是 |
| B2 Q01 | 是 | 4.36641m | 14.4709s | 否 |

我从实际源更新CSV独立重算了三个状态的概率总质量、Eq6、完整均值/方差和真源候选支持，并用原生坐标读出重新计算声明误差；均与记录一致。实际ROS参数由服务返回原始typed values核对，官方PGM转换后的导航图字节也重新比较一致。

这证明了本次所记录的程序运行与部分接口链，不能证明原论文结果已复现。A2是可解释的单回合错误声明，不能凭低于1m²的内部分布方差称找到了真源；B2真源在该记录的候选域之外，不宜作方法性能比较。两次技术失败仍属历史失败，不能剔除后称零失败。

search_t的源码是node->now()-startTime，两个实际use_sim_time=false，因此是PMFS节点系统钟秒；另一路basic_sim /clock约5倍，以及气体文件物理时间应单列，不把33.5s误称论文原始物理搜索时长。

全论文精确身份/年龄覆盖限制仍披露，AIMMD及S2批次未恢复。最终补丁分类、B2支持链和时钟完整映射由研究2收尾；本复核不追加实验。
''',encoding='utf-8',newline='\n')
files=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in E.iterdir() if p.is_file()];put(E/'FILES_MANIFEST.json',dict(files=files));print(json.dumps(dict(status=review['status'],source_files=len(sourcechecks),episodes=[{k:x[k] for k in ['case','declared_top5_error_recomputed_from_native_coordinates_m','truth_supported']} for x in episodes],rect_in_classification=rect_in_classification),ensure_ascii=False))
