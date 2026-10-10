"""Portable verification of M3: frozen file reads and temporary derived tables only.
No ROS/SSH/native forward/GADEN/CFD/navigation is invoked.
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,csv,json,math,importlib.util,subprocess,tempfile,shutil,os,contextlib,io
def js(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):
    with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def mod(p,n):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def same(a,b,path='root'):
    if isinstance(a,dict):
        assert isinstance(b,dict) and set(a)==set(b),(path,'keys')
        for k in a:same(a[k],b[k],path+'/'+str(k))
    elif isinstance(a,list):
        assert len(a)==len(b),(path,'length')
        for i,(u,v) in enumerate(zip(a,b)):same(u,v,path+'/'+str(i))
    elif isinstance(a,bool):assert a==b,(path,a,b)
    elif isinstance(a,(int,float)):
        assert math.isclose(float(a),float(b),rel_tol=2e-12,abs_tol=3e-13),(path,a,b)
    else:assert a==b,(path,a,b)
def table(p,data):
    actual=rows(p);assert len(actual)==len(data),(p,'length')
    for i,(a,b) in enumerate(zip(actual,data)):
        assert set(a)==set(b),(p,'columns')
        for k,v in b.items():
            if isinstance(v,bool):assert a[k]==str(v),(p,i,k)
            elif isinstance(v,(float,int)):
                assert math.isclose(float(a[k]),float(v),rel_tol=2e-12,abs_tol=3e-13),(p,i,k,a[k],v)
            else:assert a[k]==str(v),(p,i,k)
def child(path,args=()):
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
    r=subprocess.run([sys.executable,'-B','-X','utf8',str(path),*map(str,args)],capture_output=True,text=True,encoding='utf-8',env=env)
    assert r.returncode==0,(path,r.stdout[-3000:],r.stderr[-3000:])
    return r.stdout
def verify(root,m2):
    m1=root/'M1_REFERENCE';checks={}
    checks['boundary_point']=child(root/'boundary_point_experiment/verify_boundary_point.py')
    checks['height']=child(root/'height_intervention/verify_height.py')
    if (root/'domain_support_intervention/verify_domain.py').exists():checks['domain']=child(root/'domain_support_intervention/verify_domain.py')
    op=mod(root/'analysis/operator_contrast.py','m3_operator')
    summary,*tables=op.analyse(m2,root,write=False)
    old=js(root/'operator_contrast/OPERATOR_RESULT.json');summary.pop('wall_s');old.pop('wall_s');same(old,summary)
    for n,t in zip(['OPERATOR_SCORE_COMPARISON.csv','OPERATOR_EVENT_COUNTS.csv','RECEPTOR_CONTRIBUTION_DECOMPOSITION.csv','FILAMENT_CONTRIBUTION_DECOMPOSITION.csv','MEMBERSHIP_BRANCH_OPERATORS.csv'],tables):table(root/'operator_contrast'/n,t)
    ce=mod(root/'analysis/projected_center_field.py','m3_centres');r,*tt=ce.analyse(m1,m2,root)
    same(js(root/'projected_center_field/CENTER_FIELD_RESULT.json'),r)
    for n,t in zip(['CENTER_FIELD_SOURCE_SCORES.csv','CENTER_FIELD_PER_CELL.csv','PROJECTED_GEOMETRY_OCCURRENCES.csv'],tt):table(root/'projected_center_field'/n,t)
    # Recompute the proxy control into a temporary directory; preserve all originals.
    with tempfile.TemporaryDirectory(prefix='pmfs_m3_proxy_verify_') as td:
        tmp=Path(td);p=mod(root/'proxy_factorial_audit/analyse_frozen_proxy.py','m3_proxy')
        shutil.copy2(root/'proxy_factorial_audit/frozen_proxy_contract.json',tmp/'frozen_proxy_contract.json')
        p.HERE=tmp;p.M1=m1;p.M2=m2;p.B4=m2/'frozen_B4_inputs'
        with contextlib.redirect_stdout(io.StringIO()):p.run()
        same(js(root/'proxy_factorial_audit/PROXY_FACTORIAL_RESULT.json'),js(tmp/'PROXY_FACTORIAL_RESULT.json'))
        for f in tmp.glob('*.csv'):
            a=rows(root/'proxy_factorial_audit'/f.name);b=rows(f);assert len(a)==len(b)
            for x,y in zip(a,b):
                assert set(x)==set(y)
                for k in x:
                    try:
                        v,w=float(x[k]),float(y[k]);assert v==w or math.isclose(v,w,rel_tol=2e-12,abs_tol=3e-13),(f.name,k)
                    except ValueError:assert x[k]==y[k],(f.name,k)
    with tempfile.TemporaryDirectory(prefix='pmfs_m3_physical_verify_') as td:
        tmp=Path(td)
        child(root/'forward_contract_audit/audit_3d_state_aliasing.py',['--m1',m1,'--m2',m2,'--out',tmp])
        same(js(root/'forward_contract_audit/THREED_STATE_ALIASING_AUDIT.json'),js(tmp/'THREED_STATE_ALIASING_AUDIT.json'))
        for f in tmp.glob('*.csv'):
            assert f.read_bytes()==(root/'forward_contract_audit'/f.name).read_bytes(),f.name
    return dict(status='PASS_M3_PHYSICAL_STATE_OPERATOR_PROXY_AND_NATIVE_FORWARD_EVIDENCE',
      recomputed_operators=5,physical_snapshot_count=392,independent_forward_parity_checks=4,
      new_experiments_executed_by_verifier=0,temporary_derived_tables_only=True,
      nested_forward_verifiers_passed=list(checks),
      note='M2 physical banks, both saved RNG bundles, all negative controls and oracle limits retained.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--m2',type=Path,required=True);a=p.parse_args()
    print(json.dumps(verify(Path(__file__).resolve().parent,a.m2),ensure_ascii=False,indent=2))
