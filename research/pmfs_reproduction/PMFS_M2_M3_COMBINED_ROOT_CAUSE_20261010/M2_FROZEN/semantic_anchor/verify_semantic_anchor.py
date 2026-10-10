"""Independent read-only scalar verifier; no compilation or ROS invocation."""
import sys
sys.dont_write_bytecode=True
import argparse,csv,hashlib,json,math
from fractions import Fraction
from pathlib import Path

def verify(root):
    result=json.loads((root/'SEMANTIC_ANCHOR_RESULT.json').read_text(encoding='utf-8'))
    with (root/'vm_evidence/native/native_counts.csv').open(encoding='utf-8',newline='') as f:
        rows=list(csv.DictReader(f))
    table={(int(r['n']),int(r['total_hits']),r['ordering']):r for r in rows}
    assert len(table)==2*sum(n+1 for n in [5,10,20,50,100,200])==782
    assert all(result['execution_counters'][key]==0 for key in ['candidate_forward_calls','source_posterior_updates','ROS_nodes','GADEN_realizations'])
    reports=[]
    for summary in result['summary']:
        n=summary['n'];wrong=Fraction();raw_wrong=Fraction();ordering_disagreements=0
        for k in range(n+1):
            p=table[n,k,'hit_first'];reverse=table[n,k,'miss_first']
            st=float(p['source_score_true']);sw=float(p['source_score_wrong'])
            weight=Fraction(math.comb(n,k)*3**k*2**(n-k),5**n)
            wrong+=weight*(sw>st)
            raw_wrong+=weight*(2**k*4**(n-k)<3**k)
            ordering_disagreements+=(sw>st)!=(float(reverse['source_score_wrong'])>float(reverse['source_score_true']))
            measured=float(p['probability']);conf=float(p['confidence'])
            # float32 candidates 0.6f and 0.9f widened to double by native scoring.
            pred_t=1-.4*abs(measured-.6000000238418579)*conf
            pred_w=1-.4*abs(measured-.8999999761581421)*conf
            assert math.isclose(st,pred_t,rel_tol=0,abs_tol=3e-16)
            assert math.isclose(sw,pred_w,rel_tol=0,abs_tol=3e-16)
        assert abs(float(wrong)-summary['native_canonical_order_binomial_wrong_probability'])<1e-15
        assert abs(float(raw_wrong)-summary['raw_Bernoulli_exact_binomial_wrong_probability'])<1e-15
        assert ordering_disagreements==0
        reports.append(dict(n=n,native_wrong=float(wrong),raw_wrong=float(raw_wrong)))
    if (root/'SHA256.json').exists():
        manifest=json.loads((root/'SHA256.json').read_text(encoding='utf-8'))
        for entry in manifest:
            assert hashlib.sha256((root/entry['path']).read_bytes()).hexdigest()==entry['sha256'],entry['path']
    return dict(verdict='PASS_SOURCE_LEVEL_SEMANTIC_ANCHOR_RECOMPUTATION',native_count_rows=len(rows),n_results=reports,new_native_calls=0,new_forward_calls=0,new_ROS_nodes=0)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    print(json.dumps(verify(ap.parse_args().root),ensure_ascii=False,indent=2))
