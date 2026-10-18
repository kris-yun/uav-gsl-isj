from pathlib import Path
import csv,json,subprocess,time,sys
R=Path(__file__).resolve().parent;A=R/'analysis';A.mkdir(exist_ok=True);exe=R/'rng_stream_replay'
cmd=['g++','-std=c++20','-O2','-I'+str(R/'source_runtime/third_party/xxHash/include'),str(R/'rng_stream_replay.cpp'),'-o',str(exe)];q=subprocess.run(cmd,capture_output=True);(A/'RNG_STREAM_BUILD.log').write_bytes(q.stdout+q.stderr);assert q.returncode==0
allrows=[]
for F in sorted((R/'cases').iterdir()):
 rt=F/'runtime';p=rt/'native_rng_states.jsonl'
 if not p.exists()or not (F/'RUN_RESULT.json').exists():continue
 rows=[json.loads(line)for line in p.open()];maps=list(csv.DictReader((rt/'native_candidate_maps.csv').open()));assert len(rows)==len(maps)
 lines=[str(len(rows))]
 for row,mp in zip(rows,maps):
  assert row['call']==int(mp['call'])and row['update']==int(mp['update']);b=row['before'];a=row['after'];assert b['tid']==a['tid'];seed=b['seed']if b['ui']else a['seed'];state=b['state']if b['ui']else 65535
  cache=str(p)+'.cache.thread'+str(a['tid'])+'.f32';size=a['size']if a['ci']else 0
  vals=[b['ui'],seed,state,b['uc'],b['uh'],a['state'],a['uc'],a['uh'],b['ci'],b['index'],a['initial'],size,b['gc'],b['gh'],a['index'],a['gc'],a['gh'],b['nc'],b['nh'],a['nc'],a['nh']]
  lines.append(' '.join(map(str,vals))+' '+' '.join(json.dumps(x)for x in [cache,b['engine'],b['distribution'],a['engine'],a['distribution']]))
 inp=A/(F.name+'_RNG_INPUT.txt');inp.write_text('\n'.join(lines)+'\n');start=time.monotonic();q=subprocess.run([str(exe),str(inp)],capture_output=True);(A/(F.name+'_RNG_REPLAY.csv')).write_bytes(q.stdout);(A/(F.name+'_RNG_REPLAY.stderr')).write_bytes(q.stderr)
 assert q.returncode==0,('Recorded RNG replay failed',F.name,q.returncode)
 parsed=list(csv.DictReader(q.stdout.decode().splitlines()));assert len(parsed)==len(rows)
 result=dict(role=F.name,status='PASS_ALL_RECORDED_CANDIDATE_RANDOM_STREAMS',candidate_records=len(rows),threads=sorted(set(r['after']['tid']for r in rows)),uniform_draws=sum(int(x['uniform_draws'])for x in parsed),cached_gaussian_draws=sum(int(x['cache_draws'])for x in parsed),normal_table_draws=sum(int(x['normal_draws'])for x in parsed),wall_s=time.monotonic()-start,new_forward_simulations=0)
 allrows.append(result)
(A/'RNG_STREAM_REPLAY_RESULTS.json').write_text(json.dumps(dict(status='PASS_RECORDED_STREAM_REPLAY_NOT_FULL_TRAJECTORY_REPRODUCTION',rows=allrows),indent=2));print(json.dumps(allrows),flush=True)
