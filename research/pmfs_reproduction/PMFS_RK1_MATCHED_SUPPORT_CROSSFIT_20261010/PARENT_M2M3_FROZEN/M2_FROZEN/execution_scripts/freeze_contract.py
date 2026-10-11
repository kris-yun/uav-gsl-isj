from common import *
import hashlib,shutil
handoff=W/'handoff'
hashes=json.loads((handoff/'SHA256.json').read_text(encoding='utf-8'))
for name,digest in hashes.items():assert hashlib.sha256((handoff/name).read_bytes()).hexdigest()==digest
sources=[('C7',[-3.2,-3.3,-.5]),('K2',[-1.675,1.495,-.5])]
jobs=[]
for replicate in range(4):
    for candidate,xyz in sources:
        identity=f'PMFS-M2-20261010-v1/{candidate}/realization/{replicate}'
        seeds=[int.from_bytes(hashlib.sha256((identity+'/stream/'+str(stream)).encode()).digest()[:4],'little') for stream in range(2)]
        assert all(seed!=5489 for seed in seeds)
        jobs.append(dict(candidate_id=candidate,realization=replicate,role='reference' if replicate<2 else 'heldout',
                         source_xyz=xyz,seeds=seeds,seed_rule_identity=identity,smoke_first_pair=replicate==0))
contract=dict(anchor_commit='a41c611b25b276ad86d1baf887153f26bb153df7',
 user_authorization='2026-10-10 human request: 学习了解这个pro给你的全部知识思想,并进行实验,然后返回压缩包; bounded attached plan adopted, no additional approvals inferred beyond this experiment',
 work_scope='Native scalar semantics + eight independent source-conditioned B4 references and observation-process discrimination',
 maximum_new_GADEN_realizations=8,first_two_smoke_included_in_eight=True,maximum_generation_total_wall_s=900,
 maximum_single_process_RSS_bytes=1073741824,maximum_new_disk_bytes=2147483648,
 one_existing_VM_only=True,serial_generations=True,ROS_domain=88,CFD_generations=0,navigation_goals=0,training_runs=0,
 extra_2D_candidate_forwards=0,point_source_comparison_only_in_3D=True,
 jobs=jobs,reference_split=[0,1],heldout_split=[2,3],
 smoothing=dict(rule='Jeffreys beta-binomial marginal predictive',alpha=.5,beta=.5,
                p_formula='(positive reference realizations + 0.5)/(2 + 1)',estimated_probabilities=[1/6,.5,5/6]),
 primary_scores=['Bernoulli marginal composite log score over 50 actual block events','Mean Brier score over 50 actual block events'],
 independence_claim='Physical realization units only. No joint likelihood, calibrated posterior or sample-size=50/447 claim.',
 old_stops_unchanged=True,core_PMFS_unchanged=True,source_blind_scoring='Score code receives C7/K2 IDs only; truth-role mapping read after scores hashed',
 original_B4_all_positive_labels=True,original_B4_case_is_posthoc_mechanism_discovery=True,
 future_prototype_gate='No automatic prototype or independent task: preserve original qualification requirements and E3 successful control',
 no_posthoc_tuning=['seed','threshold','source location','smoothing','scores','split','reference count'],
 incomplete_cells='2D occupancy frequency and 3D PID are not interchangeable; do not invent conversion',
 receiver_schedule='To be frozen from exact consumer gas messages, raw CDR and actual service/clock frame lineage before querying or scoring',
 aligned_map_comparison='Mean squared difference between observed map and identical-PMFSLib predicted map, over free cells; descriptive dependent-map discrepancy, not independent-cell likelihood',
 unmatched_map_comparison='Measured cumulative map versus frequency of concentration>0.1 over the same 50 observation frames at every free 2D cell and actual sensor height; descriptive deliberately unmatched comparison',
 continuous_concentration='Archive separately as extra-information condition; no switch to new score after outcomes',
 RNG_change='Isolated copy only: two native mt19937 streams seeded before Gaussian cache construction; capture initial/final states and generated cache; no physics parameter change')
out=OUT/'frozen_contract.json';assert not out.exists();out.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
mapping=dict(C7='original_B4_true_source',K2='B4_posthoc_wrong_candidate')
(OUT/'TRUTH_ROLE_MAPPING_ANALYSIS_ONLY.json').write_text(json.dumps(mapping,indent=2)+'\n',encoding='utf-8')
shutil.copytree(handoff,OUT/'handoff_original')
shutil.copyfile(Path('C:/Users/50176/Downloads/下一轮Codex最小鉴别实验_待执行.md'),OUT/'USER_TASK_FILE.md')
shutil.copyfile(Path('D:/ZYC/UAV/.codex/attachments/6c262ad2-9db2-4217-8d5f-47e658580cba/已粘贴的文本.txt'),OUT/'USER_RESEARCH_REASONING.txt')
(OUT/'PRE_RUN_CONTRACT_SHA256.txt').write_text(hashlib.sha256(out.read_bytes()).hexdigest()+'  frozen_contract.json\n',encoding='ascii')
print(json.dumps({'frozen_contract_SHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'jobs':jobs},indent=2))
