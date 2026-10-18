from pathlib import Path
import argparse,csv,hashlib,json,math,os,shutil,subprocess,sys,zipfile
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description='Offline data replay only. Never starts ROS, a gas world, or AIMMD.');p.add_argument('--verify-only',action='store_true');p.add_argument('--out',type=Path);args=p.parse_args()
manifest=json.loads((R/'MANIFEST_SHA256.json').read_text(encoding='utf-8'));rows=manifest['files'];bad=[]
for row in rows:
 q=R/row['path']
 if not q.is_file()or hashlib.sha256(q.read_bytes()).hexdigest()!=row['sha256']:bad.append(row['path'])
assert not bad,bad
print(json.dumps(dict(status='PASS_ALL_PAYLOAD_SHA256',files=len(rows))))
if args.verify_only:raise SystemExit(0)
assert args.out is not None,'Use --out NEW_DIRECTORY to keep frozen results intact.'
out=args.out.resolve();assert not out.exists(),'Output directory must be new; frozen results are never overwritten.'
out.mkdir(parents=True)
for name in ['cases','analysis','source_runtime']:
 shutil.copytree(R/name,out/name)
for name in ['analyze.py','verify_readout_guest.py','native_readout_check.cpp']:shutil.copyfile(R/name,out/name)
prev=out/'_previous';prev.mkdir()
with zipfile.ZipFile(R/'previous_qualified_baseline.zip')as z:
 for item in z.infolist():
  target=(prev/item.filename).resolve();assert target.is_relative_to(prev.resolve())
  if item.is_dir():target.mkdir(parents=True,exist_ok=True)
  else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(item))
previous=prev/'PMFS_PAPER_FIRST_ROS_QUAL_20261017';assert previous.is_dir()
env=os.environ.copy();env['PMFS_AUDIT_PREVIOUS_ROOT']=str(previous)
commands=[]
for name in ['analyze.py','verify_readout_guest.py']:
 argv=[sys.executable,str(out/name)];q=subprocess.run(argv,env=env,capture_output=True,text=True);commands.append(dict(argv=argv,exit_code=q.returncode));(out/(name+'.stdout')).write_text(q.stdout,encoding='utf-8');(out/(name+'.stderr')).write_text(q.stderr,encoding='utf-8')
 assert q.returncode==0,(name,q.stderr)
# Inputs must match bytes. Recomputed floating reductions may differ by a few
# ulps between Windows BLAS and Linux BLAS; compare numbers at double precision.
checks=[]
for name in ['EPISODES.csv','SOURCE_UPDATES.csv','FIXED_HISTORY_FORMULA_CONTROLS.csv','EXACT_NATIVE_REPLAY_PARITY.csv','FORMULA_CONTROLS_NATIVE_CPP_READOUT.csv']:
 ap=R/'analysis'/name;bp=out/'analysis'/name;a=ap.read_bytes();b=bp.read_bytes();same=a==b
 aa=list(csv.DictReader(ap.open(encoding='utf-8',newline='')));bb=list(csv.DictReader(bp.open(encoding='utf-8',newline='')));assert len(aa)==len(bb),(name,'row count')
 differences=0;max_abs=0.
 for row,other in zip(aa,bb):
  assert row.keys()==other.keys()
  for key,x in row.items():
   y=other[key]
   if x==y:continue
   try:xx,yy=float(x),float(y)
   except ValueError:raise AssertionError((name,key,x,y))
   assert math.isclose(xx,yy,rel_tol=1e-12,abs_tol=1e-12),(name,key,x,y)
   differences+=1;max_abs=max(max_abs,abs(xx-yy))
 checks.append(dict(file=name,byte_equal=same,numerically_equivalent=True,float_fields_differing_in_last_bits=differences,max_abs_difference=max_abs,reference_sha256=hashlib.sha256(a).hexdigest(),replayed_sha256=hashlib.sha256(b).hexdigest()))
(out/'REPRODUCTION_RESULT.json').write_text(json.dumps(dict(status='PASS_OFFLINE_REPLAY_FIVE_TABLES_NUMERICALLY_EQUIVALENT',relative_tolerance=1e-12,absolute_tolerance=1e-12,commands=commands,checks=checks,new_ROS=0,new_forward_simulations=0,new_worlds=0,AIMMD=0),indent=2))
print(json.dumps(dict(status='PASS_OFFLINE_REPLAY_FIVE_TABLES_NUMERICALLY_EQUIVALENT',output=str(out),new_ROS=0,new_forward_simulations=0)))
