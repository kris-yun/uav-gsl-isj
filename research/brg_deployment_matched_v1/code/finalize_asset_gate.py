"""Document the observed data stop without substituting sparse snapshots."""
from pathlib import Path
import collections,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    audit=json.loads((E/'VERIFIED_ASSET_AUDIT.json').read_text())
    records=audit['records']
    if len(records)!=288 or not audit['all_recorded_hashes_match']:
        raise RuntimeError('asset count/hash audit failed')
    if any(r['shape'][0]!=10 or r['raw_frame_count'] for r in records):
        raise RuntimeError('asset state changed; redo inventory before deciding')
    sources={}
    for r in records:
        key=(r['house'],r['source_id'])
        s=sources.setdefault(key,{'house':r['house'],'source_id':r['source_id'],'xyz':r['source_xyz'],'snapshot_plumes':0,'winds':set(),'continuous_plumes_in_checked_bank':0})
        s['snapshot_plumes']+=1;s['winds'].add(r['wind'])
    source_rows=[{**s,'winds':sorted(s['winds'])} for s in sources.values()]
    c0_sources=sorted({c['manifest']['source_xyz_m'] for c in audit['c0_manifest_inventory']})
    status={'status':'BRG_V1_HOLD_INSUFFICIENT_CONTINUOUS_OPEN_ASSETS','classification':'DATA_EXECUTION_HOLD_NOT_ALGORITHM_RESULT','branch':'codex/brg-deployment-matched-v1-20260928','base_commit':'cb4c9af6a2dce0e852946df07c607cca4660e3ac','original_zip_sha256':'948379c7056067dc8a1d6742d21256480ed4c5e73d4d07f358dbf3dd41156453','installed_scope':'plan, shared timing/loss/split utilities, tests, GPU entry provenance; not a ROS-integrated trained V1','provided_tests':17,'local_tests_passed':17,'snapshot_plumes_verified':len(records),'historical_cube_hash_matches':288,'physical_source_count':len(source_rows),'continuous_plumes_in_checked_288_bank':0,'legacy_c0_continuous_runs':len(audit['c0_manifest_inventory']),'legacy_c0_physical_sources':len(c0_sources),'legacy_c0_sources_xyz':c0_sources,'minimum_eval_sources_required':4,'source_split_frozen':False,'training_epochs_executed':0,'new_weights_created':0,'new_plumes':0,'closed_loop_runs_executed':0,'required_closed_loop_runs':32,'house03_used_for_training_or_selection':False,'v0_modified':False,'ros_runtime_replaced':False,'asset_audit_sha256':sha(E/'VERIFIED_ASSET_AUDIT.json'),'source_inventory':source_rows,'next_required_input':'original continuous OPEN H01/H02 simulator frames or equivalent lawful deployment sensor histories with physical source/seed/timebase provenance; enough disjoint train/dev plus four evaluation sources','prohibited_substitutions':['sparse-frame interpolation','new plumes without separate authorization','House03 or sealed development substitution','nearest-source relabeling','reusing V0 weights as V1 weights']}
    (ROOT/'STATUS.json').write_text(json.dumps(status,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    lines=['# BRG V1 安装与连续资产准入审计','',
      '**状态：数据执行 HOLD；没有产生新的算法失败结果。**','',
      '新包及其共享时间、损失、划分工具已导入独立分支，V0 不变。实际 full-support GPU 训练入口和运行配置已经归档。新包是实施方案，不是可直接替换的 ROS 二进制或权重；此次未将 V1 接入运行中的 ROS。','',
      '## 核验结果','',
      '- 精确核验原 E2 OPEN 72、JTD E1 36、JTD E2 180，共 288 条 plume；全部与历史 cube SHA256 一致。',
      '- H01 96 条保存 10×87×114；H02 192 条保存 10×83×119。它们是完整空间场的十个时刻，不是完整时间连续场。',
      '- 上述 288 条涵盖 H01/H02 各六个物理源，但对应目录的连续 iteration 文件为 0；生成代码中有提取十帧后清理 realization 的记录。',
      '- R0 的 288 条和 D1R 的 2688 条亦只保留十帧空间场，不能充当部署匹配的高频过程。',
      '- C0.5 仍保留八组 566 帧记录，但只有两个 House02 物理源；不同 wind、seed 不增加独立源数。其时间基准尚未认证为 V1 的 300 s 覆盖。即使后续认证，两源也不足四个留出评测源，更不能同时留出训练、验证源。',
      '- canonical House01 历史源高度为 0.40/−0.30 m，House02 另一 family 为 −0.10 m，且并非当前精确合法候选标签。没有把历史源改标为最近候选，也没有自动打开其它 wind/House。','',
      '## 执行边界','',
      '停止依据是用户提供的 CODEX_NEXT_ACTION 第2项及 README 第4/7节：无合法连续资产或不足四个源留出时如实报告，不造 plume，不插值，不用 H03 补位。',
      '因此本次训练为 0 epoch，新权重为 0，32 次闭环尚未启动。17 项局部测试通过只验证工具语义，不代表 VGR 集成通过或 BRG 定位改善。','',
      '## 可继续的具体输入','',
      '需恢复既有 OPEN H01/H02 源/seed 对应的完整连续 simulator 输出，或同传感器/窗口合同下、含原始采样时钟及位置的合法日志。先有非空训练、验证源组，再有四个互不泄漏的评测源，每个评测源两条 realization。按相邻源成组时，两个评测 pair 之外仍需独立训练与验证 pair。',
      '目前缺的是这些连续输入，不是候选模板；596/630 的银行继续复用，不需重建。若原始输入已不存在，生成补充 plume 是新的授权决定，此版本不会自行执行。','',
      '根分区可用 '+str(audit['disk']['/']['free'])+' bytes，共享盘可用 '+str(audit['disk']['/mnt/hgfs/workspace']['free'])+' bytes；未清理历史数据。',
      '', '完整逐条路径、形状、历史 SHA256、metadata、保留帧计数及生成源码片段见 VERIFIED_ASSET_AUDIT.json。']
    (E/'ASSET_GATE_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(json.dumps({k:status[k] for k in ('status','snapshot_plumes_verified','physical_source_count','legacy_c0_physical_sources','training_epochs_executed','closed_loop_runs_executed')},indent=2))
if __name__=='__main__':main()
