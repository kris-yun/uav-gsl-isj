"""Future B proposal only. Geometry/config input; no gas snapshot or response read."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import csv,json,hashlib,math,importlib.util
import numpy as np
from scipy.ndimage import distance_transform_edt,label

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
PARENT=BASE/'outputs/PMFS_RK1_PRO_REVIEW_BUNDLE_20261010'
M2=PARENT/'PARENT_M2M3_FROZEN/M2_FROZEN'
M3=PARENT/'PARENT_M2M3_FROZEN/M3_NEW'
OLD_COMMIT='210b94e5de0ab7e906136fd0765c3639f10103b2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def scalar_params(path):
    out={}
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.startswith('    ') or ':' not in line:continue
        key,value=line.strip().split(':',1);out[key]=value.strip()
    return out
def choose(points,count,tag):
    assert len(points)>=count
    points=sorted(points,key=lambda p:(p['grid_i'],p['grid_j']))
    integer=int(hashlib.sha256(tag.encode('utf-8')).hexdigest(),16)
    first=integer%len(points);chosen=[points[first]]
    while len(chosen)<count:
        remaining=[p for p in points if p not in chosen]
        def dist(p):return min((p['xyz_m'][0]-s['xyz_m'][0])**2+(p['xyz_m'][1]-s['xyz_m'][1])**2 for s in chosen)
        p=min(remaining,key=lambda p:(-dist(p),p['grid_i'],p['grid_j']))
        chosen.append(p)
    return chosen,dict(tag=tag,full_SHA256=hashlib.sha256(tag.encode()).hexdigest(),initial_hash_mod_index=first,eligible_count=len(points),sort='grid_i, then grid_j ascending',subsequent_rule='maximum minimum squared XY distance; tie grid_i,grid_j ascending')

def main():
    p2=M2/'event_map_anchor/vm_evidence/snapshot/occupancy.csv'
    p3=M2/'frozen_B4_inputs/derived_B4/OccupancyGrid3D.csv'
    metadata=M3/'M1_REFERENCE/snapshot/metadata.json'
    rawpath=PARENT/'RK0_NEW/source/verify_raw_receiver_queries.py'
    params=[M2/f'native_reference_evidence/realizations/{b}/PARAMETERS.yaml' for b in ['C7_0','K2_0']]
    wind=M2/'frozen_B4_inputs/derived_B4/wind/wind_iteration_10'
    geometryfiles=[p2,p3,metadata,rawpath,*params,wind]
    assert all(p.is_file() for p in geometryfiles)
    inp={p.relative_to(PARENT).as_posix():sha(p) for p in geometryfiles}
    old=json.loads((PARENT/'SHA256SUMS.json').read_text(encoding='utf-8'))
    for key,h in inp.items():assert old[key]==h,key
    spec=importlib.util.spec_from_file_location('geometry_only_occupancy_parser',rawpath)
    raw=importlib.util.module_from_spec(spec);spec.loader.exec_module(raw)
    occ=raw.occupancy(p3) # Geometry only; snapshot()/query()/LOS never called.
    free=occ['data']==0;distance=distance_transform_edt(np.pad(free,1,constant_values=False))[1:-1,1:-1,1:-1]*float(occ['cell_size'])
    def status(point):
        point=np.asarray(point,dtype=np.float32)
        ix=np.asarray((point-occ['minimum'])/occ['cell_size'],dtype=np.int64)
        if (ix<0).any() or (ix>=occ['dimensions']).any():return dict(legal=False,state=3,indices=ix.tolist(),clearance_lower_bound_m=0.)
        x,y,z=map(int,ix);state=int(occ['data'][z,x,y])
        centre=occ['minimum'].astype(float)+(ix+.5)*float(occ['cell_size'])
        bound=max(0.,float(distance[z,x,y])-math.sqrt(3)*float(occ['cell_size'])/2-float(np.linalg.norm(point.astype(float)-centre)))
        return dict(legal=state==0,state=state,indices=[x,y,z],clearance_lower_bound_m=bound)
    with p2.open(encoding='utf-8',newline='') as f:rr=list(csv.DictReader(f))
    first=rr[0];w,h=int(first['grid_width']),int(first['grid_height']);cell=float(first['cell_size']);origin=[float(first['origin_x']),float(first['origin_y'])]
    assert len(rr)==w*h and sorted(int(r['cell_index']) for r in rr)==list(range(w*h))
    meta=json.loads(metadata.read_text());assert [meta['width'],meta['height']]==[w,h] and meta['cell_size']==cell
    assert [meta['origin_x'],meta['origin_y']]==origin
    mask=np.zeros((h,w),dtype=bool)
    for row in rr:
        index=int(row['cell_index']);mask[index//w,index%w]=row['occupancy']=='Free'
    assert int(mask.sum())==meta['free_cells']
    components,ncomponents=label(mask)
    oldparams=[scalar_params(p) for p in params]
    oldsources=[[float(p['source_position_'+a]) for a in ['x','y','z']] for p in oldparams]
    excluded={(math.floor((s[0]-origin[0])/cell),math.floor((s[1]-origin[1])/cell)) for s in oldsources}
    sourcepoints=[];receiverpoints=[];allrows=[]
    for j,i in zip(*np.nonzero(mask)):
        xy=[origin[0]+(int(i)+.5)*cell,origin[1]+(int(j)+.5)*cell]
        sr=status([*xy,-.5]);rc=status([*xy,-.2])
        common=dict(grid_i=int(i),grid_j=int(j),cell_index=int(j)*w+int(i),component=int(components[j,i]))
        sourceok=sr['legal'] and (int(i),int(j)) not in excluded
        receiverok=rc['legal'] and rc['clearance_lower_bound_m']>=.20
        if sourceok:sourcepoints.append(dict(**common,xyz_m=[*xy,-.5],occupancy3D_indices=sr['indices'],clearance_lower_bound_m=sr['clearance_lower_bound_m']))
        if receiverok:receiverpoints.append(dict(**common,xyz_m=[*xy,-.2],occupancy3D_indices=rc['indices'],clearance_lower_bound_m=rc['clearance_lower_bound_m']))
        allrows.append(dict(**common,source_eligible=sourceok,receiver_base_eligible=receiverok,source_clearance_m=sr['clearance_lower_bound_m'],receiver_clearance_m=rc['clearance_lower_bound_m']))
    source_tag='RK2-B-SOURCE-GEOMETRY-V1|'+OLD_COMMIT
    sources,source_rule=choose(sourcepoints,3,source_tag)
    assert len({p['component'] for p in sources})==1,'Future proposal needs common original 2D connected support'
    component=sources[0]['component']
    receiverpoints=[p for p in receiverpoints if p['component']==component and all(math.dist(p['xyz_m'][:2],s['xyz_m'][:2])>=1. for s in sources)]
    receivers,receiver_rule=choose(receiverpoints,10,'RK2-B-RECEIVER-GEOMETRY-V1|'+OLD_COMMIT)
    for i,s in enumerate(sources):s['future_candidate_id']=f'candidate_B_{i:03d}'
    for i,r in enumerate(receivers):
        r['stop_id']=i;r['physical_query_times_s']=[320.+20.*i+.5*k for k in range(5)]
        r['distances_to_all_candidate_sources_m']=[math.dist(r['xyz_m'][:2],s['xyz_m'][:2]) for s in sources]
    seeds=[]
    for source in sources:
        for role in ['reference','heldout']:
            for replicate in range(2):
                tag=f"RK2-B-RNG-V1|{OLD_COMMIT}|{source['future_candidate_id']}|{role}|{replicate}"
                seed=int.from_bytes(hashlib.sha256(tag.encode()).digest()[:4],'little')
                seeds.append(dict(candidate_id=source['future_candidate_id'],role=role,replicate=replicate,proposed_uint32_seed=seed,tag=tag))
    assert len({s['proposed_uint32_seed'] for s in seeds})==12
    keep=['sim_time','time_step','num_filaments_sec','variable_rate','filament_stop_steps','ppm_filament_center','filament_initial_std','filament_growth_gamma','filament_noise_std','gas_type','temperature','pressure','concentration_unit_choice','wind_time_step','allow_looping','results_time_step','results_min_time']
    assert {k:oldparams[0][k] for k in keep}=={k:oldparams[1][k] for k in keep}
    result=dict(status='GEOMETRY_ONLY_FUTURE_B_PROPOSAL_NOT_APPROVED_NOT_EXECUTED',parent_commit=OLD_COMMIT,parent_manifest_SHA256=sha(PARENT/'SHA256SUMS.json'),input_SHA256=inp,
      consumed_input_types=['3D occupancy','native pruned 2D occupancy','native grid metadata','gas scalar configuration','native geometry parser','wind asset hash only'],
      gas_snapshots_or_concentrations_read_for_selection=False,phi_or_new_prediction_calls=0,CFD_GADEN_ROS_VM_execution=0,
      native_2D_support=dict(width=w,height=h,cell_size_m=cell,origin_m=origin,free_cells=int(mask.sum()),connected_components=ncomponents),
      occupancy3D=dict(dimensions=occ['dimensions'].tolist(),minimum_m=occ['minimum'].astype(float).tolist(),maximum_m=occ['maximum'].astype(float).tolist(),cell_size_m=float(occ['cell_size'])),
      exclusion=dict(old_source_xyz_m=oldsources,old_source_support_cells=sorted([list(p) for p in excluded]),rule='exclude whole old coarse support cells, not merely exact floating-point old coordinates'),
      legality_rule=dict(source_z_m=-.5,source_centre_must_be_3D_free=True,full_3sigma_ball_clearance_is_not_a_native_point_release_requirement=True,receiver_z_m=-.2,receiver_clearance_lower_bound_m=.20,receiver_minimum_distance_to_each_candidate_XY_m=1.,sphere_clearance='EDT nearest nonfree voxel-centre distance minus voxel half-diagonal and point-to-own-voxel-centre offset; outside padded blocked'),
      source_selection=source_rule,receiver_selection=receiver_rule,sources=sources,receivers=receivers,
      fixed_observation_window=dict(start_physical_s=320.,maximum_elapsed_physical_s=300.,last_planned_query_physical_s=502.,queries=50,virtual_point_receivers_only=True,ROS_query_nodes_or_navigation_goals=0),
      unchanged_gas_config={k:oldparams[0][k] for k in keep},wind_rule='same fixed wind_iteration_10 asset; physical query traces must prove index10, not infer from filename',
      proposed_rng_initial_states=seeds,
      reference_realizations=6,heldout_realizations=6,total_proposed_realizations=12,
      model_adaptation='same frozen U_query/S_query/L construction rules on six new references, equal realization weights; 30 scheduled rows per receiver, not the old-code literal20',
      future_main_endpoint=dict(source_NLL_mean_over_six_whole_heldout='at least10percent improvement vs each ordinary baseline',Top1_errors='no increase; ties are abstain errors',per_realization_NLL_worsening_limit_nat=.2,endpoint_status='PROPOSED_FOR_FUTURE_APPROVAL_NOT_AN_A_RULE',resource_parity='same actual total storage and local readout budget'),
      budget_proposal=dict(GADEN_realizations=12,new_CFD=0,new_navigation=0,generation_single_thread=True,reuse_existing_qualified_binary_no_compilation=True,total_gas_generation_wall_ceiling_s=900,per_generator_RSS_ceiling_bytes=1073741824,new_disk_reservation_bytes=3221225472,method_construction_and_predictions_wall_ceiling_s=600,reference_native_response_arithmetic='6 reference realizations x 50 frames x 10 frozen poses',reference_native_anchor_first='first reference count toward12; validate only time/hash/finite/native operator, not task performance'),
      missing_before_execution=['fresh user approval for this B contract and all12 realizations','A method-value gate must independently permit requesting B; this proposal does not override A STOP','existing generator binary/hash/runtime inventory and exact semantic RNG seed binding','final release-boundary/outlet and wind coverage validation at three selected sources','exact physical saved-time trace clock mapping; selected frame by saved physical time, not frame-name/0.5 arithmetic','receiver response cache and scalar observations; none generated now','new task information separation and loss/endpoint/model-capacity freeze before first new output','separate model-shape assertion update from20 to30 training rows/pose before new output; no loss/ridge/tree-rule change'],
      limits=['one new three-source classification task, not full447-free-cell localization','same geometry and static wind; not independent geometry or lake generalization','geometry safety margin is a conservative virtual receiver point-domain filter, not validated UAV dynamics or navigable flight trajectory','fixed virtual sensor queries across10 poses; no ROS query nodes, Nav2 path, transit concentration or robot closed loop','no source/receiver reselection on low signal, poor separability, or unfavorable method outcome','technical failure stops without replacement favorable seed; futureB not automatically started'])
    dump(HERE/'B_PROSPECTIVE_GEOMETRY_ONLY_PLAN.json',result)
    with (HERE/'B_GEOMETRY_ELIGIBILITY_AUDIT.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(allrows[0]));writer.writeheader();writer.writerows(allrows)
    source_lines='\n'.join(f"| {s['future_candidate_id']} | ({s['xyz_m'][0]:.6f}, {s['xyz_m'][1]:.6f}, -0.5) | ({s['grid_i']},{s['grid_j']}) | {s['cell_index']} | {s['occupancy3D_indices']} | {s['clearance_lower_bound_m']:.4f} |" for s in sources)
    receiver_lines='\n'.join(f"| {r['stop_id']} | ({r['xyz_m'][0]:.6f}, {r['xyz_m'][1]:.6f}, -0.2) | ({r['grid_i']},{r['grid_j']}) | {r['physical_query_times_s'][0]:.1f}–{r['physical_query_times_s'][-1]:.1f} | {min(r['distances_to_all_candidate_sources_m']):.3f} |" for r in receivers)
    text=f'''# B：一个未来新任务的几何方案（未批准、未执行）

只完成 geometry/config 静态设计。未读气体浓度或 phi 来选点、未拟合模型、未产生气体；不放行 B，不能越过 A 的方法价值门。父起点为 `{OLD_COMMIT}`。

## 合法支持与固定选择

找到原生已裁剪二维候选支持：34×45、0.25m、原点(-7.55,-7.88)，447自由格。与M1原生metadata一致；3D占据为87×114×33、0.1m，输入哈希全部与原RK1父manifest一致。

源高度固定-0.5m，受体高度固定-0.2m。源中心必须是原生3D自由格；受体另按0.20m保守清距过滤。完整初始3sigma球均自由不是原生point-source释放要求，高斯核跨壁由LOS处理，因此不把这个额外条件作为源排除门。原先尝试的0.30m整球条件在静态几何上排除全部点，已经在任何新气体出现前取消并记录，而未改变源强/sigma或旧数据。清距来自体素几何，不来自浓度。排除原C7/K2真实坐标所属整个二维粗格。先按(i,j)排序，以固定tag SHA256模合法点数选首点，再选至已选点最小XY距离最大的点，平局按(i,j)。十受体在同一原生连通域按独立tag、相同最远点覆盖法选择；距全部三候选至少1m，角色对称，不依赖测试真源。

这是基于已审计官方环境的新派生任务，不是作者原样场景。保守清距筛选的合法源点数为{len(sourcepoints)}，完成全候选1m排除后的合法受体点数为{len(receiverpoints)}。没有检查信号强弱后换点。

| 候选 | XYZ/m | 2D(i,j) | 原生cell_index | 3D(i,j,k) | 清距下界/m |
|---|---|---|---:|---|---:|
{source_lines}

## 固定受体计划

每处5次查询，间隔0.5s。第一处物理时刻320s，其后每20s切换一处；每个实现全部使用同一50块计划，末块为502s，位于固定300s观测窗(320–620s)内。帧必须按实际保存的物理时钟查找，不能用文件编号×0.5推断。这里只定义虚拟点传感器查询，不运行ROS查询节点或导航goal，未模拟无人机移动/路径，不声称具有已验证的真实飞行安全性。未来气体生成若批准，仍需沿用已有合格GADEN进程环境；本轮没有启动该环境。

| stop | XYZ/m | 2D(i,j) | 查询物理时段/s | 到最近候选的XY距离/m |
|---:|---|---|---|---:|
{receiver_lines}

## 数据与方法冻结建议

仍用7丝团/s、gas_type=13、初始sigma10cm、growth_gamma15、noise_std0.02、temperature298、pressure1、原有释放与单位规则，固定第10帧风资产；真实wind索引/时钟在实际生成时另验。每源2参考+2留出，共12份，JSON给出12个互不相同的预定uint32 seed；目前只是待批seed绑定方案，不已创建realization。

共享字典仅用6份参考按同冻结规则构造，六份留出只开放真实标量气体读数/许可受体计划。三模型相同信息、查询损失、正则化及支持回退。未来每受体30条训练查询，需要在数据出现前把A代码的固定20行断言参数化为30；这是样本布局适配，不得趁机改loss、lambda、树容量/切分规则。分类评分沿用每份参考先阈值再事件频率、共同mean logscore、温度1，不使用测试粒子/尾项。

未来B主门建议：六份完整留出等权源NLL相对U_query、S_query分别至少降低10%，Top1错误不增加（并列按弃权错误），任何一份NLL恶化不超过0.2nat，且同总存储/推理预算。10%与0.2是需要批准的实用阈值，不是本轮A规则或物理定律。源Top1天花板、无气体检出或无可辨识信号均如实报告，不改主端点、不换计划、不补有利种子。

## 待批准预算与缺项

最多12份生成，沿用现有合格生成器，不新编译、不计算CFD、不跑导航。建议生成总墙钟900s、单个生成器RSS≤1GiB，预留3GiB磁盘；参考响应复算与单一方法构造再单列600s/1GiB。旧M2八份生成用28.1s、完整工作数据约675.7MB，仅作参考，不能保证新源成本。3GiB来自1000s、7丝团/s、0.5s保存的全存活粒子体积上界及元数据余量。

生成第一份时只验输入合同、保存时钟、有限数、原生读出锚点，计入12份；不得先看性能再决定是否继续/换源。技术失败按合同停止，不能补有利seed。

尚缺新用户批准、A门通过、现有生成二进制/随机绑定/资源验收、三源释放边界与风覆盖验收、完整物理时间日志和新参考/观测数据。没有任何生成或方法性能已取得。A不合格则当前B方案仅留档，不执行。

可重算的静态选择脚本为 `design_b_geometry_only.py`，候选/受体及所有输入SHA详见同名JSON和 `B_GEOMETRY_ELIGIBILITY_AUDIT.csv`。该脚本不调用snapshot、query、LOS或任何生成程序。
'''
    (HERE/'B_PROSPECTIVE_GEOMETRY_ONLY_PLAN_zh.md').write_text(text,encoding='utf-8')
    print(json.dumps(dict(status=result['status'],source_eligible=len(sourcepoints),receiver_eligible=len(receiverpoints),sources=[p['xyz_m'] for p in sources],receivers=len(receivers)),ensure_ascii=False))

if __name__=='__main__':main()
