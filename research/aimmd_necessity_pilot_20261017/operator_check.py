"""Exact finite-state counterexample; not a PMFS sampler benchmark."""
from pathlib import Path
import itertools,json,math
R=Path(__file__).resolve().parent
records=[];p1=.1;p2=.2;q=[.1,.3,.3,.3]
for k,(a,b) in enumerate(itertools.product([0,1],repeat=2)):
    target=(p1 if a else 1-p1)*(p2 if b else 1-p2);weight=target/q[k]
    records.append(dict(particle1=a,particle2=b,target_probability=target,proposal_probability=q[k],weight=weight,any_hit=int(a or b),sum_of_individual_hits=a+b))
correct=sum(x['proposal_probability']*x['weight']*x['any_hit'] for x in records)
wrong_sum=sum(x['proposal_probability']*x['weight']*x['sum_of_individual_hits'] for x in records)
result=dict(status='PASS_EXACT_JOINT_EVENT_IMPORTANCE_IDENTITY',target_any_hit_probability=1-(1-p1)*(1-p2),correct_weighted_joint_event=correct,wrong_weighted_hit_count=wrong_sum,wrong_weighted_individual_hit_fraction=wrong_sum/2,states=records,
 scope='Finite four-state mathematical operator check only; zero gas simulations; does not establish an implemented PMFS WE or AIMMD arm.')
assert math.isclose(correct,result['target_any_hit_probability'])
(R/'lineage/MULTIPARTICLE_OPERATOR_CHECK.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
