#!/usr/bin/env python3
"""Real socket/compiled-C++ round trip + model-bank inference latency.
No gas targets read. c values below are test messages, NOT synthetic plumes.
"""
import json,sys,subprocess,time,socket,tempfile
from pathlib import Path
import numpy as np,torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from pmfs_brg.bank import TemplateBank
from pmfs_brg.model import load_checkpoint
from pmfs_brg.runtime import InferenceSession
import argparse

def main():
 p=argparse.ArgumentParser();p.add_argument('--bank',required=True);p.add_argument('--checkpoint',required=True);p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 torch.set_num_threads(1);model,meta=load_checkpoint(a.checkpoint);bank=TemplateBank.load(a.bank)
 ss=InferenceSession(model,meta,bank,True);ss.reset('timing',bank.fingerprint);xy=bank.xy[0];times=[]
 for i in range(40):
  t=time.perf_counter();r=ss.observe(dict(run_id='timing',event_id=i,time_s=float(i+1),x=float(xy[0]),y=float(xy[1]),z=.2,concentration_ppm=0. if i%2 else .1));times.append((time.perf_counter()-t)*1000)
 assert abs(sum(r['q'])-1)<1e-8
 with tempfile.TemporaryDirectory() as td:
  binary=Path(td)/'client';cp=subprocess.run(['c++','-std=c++17','-Wall','-Wextra','-O2',str(ROOT/'integration/client_smoke.cpp'),'-o',str(binary)],capture_output=True,text=True,check=True)
  with socket.socket() as probe:probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
  server=subprocess.Popen([sys.executable,str(ROOT/'tools/serve.py'),'--bank',a.bank,'--checkpoint',a.checkpoint,'--allow-warmstart','--tcp-port',str(port),'--log',str(out/'server_events.jsonl')],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
  try:
   for _ in range(100):
    try:
     with socket.create_connection(('127.0.0.1',port),timeout=.1):break
    except OSError:time.sleep(.05)
   result=subprocess.run([str(binary),str(port),bank.fingerprint,str(len(bank.ids)),str(bank.n),str(xy[0]),str(xy[1]),'.2','.1','1','0'],capture_output=True,text=True,timeout=10,check=True)
  finally:
   server.terminate();server.wait(timeout=10)
 report={'candidate_count':len(bank.ids),'map_cells':bank.n,'model_parameters':model.parameter_count,'bank_hash':bank.fingerprint,'latency_ms_median_excluding_first':float(np.median(times[1:])),'latency_ms_p95_excluding_first':float(np.quantile(times[1:],.95)),'bank_array_payload_bytes':sum(x.nbytes for x in [bank.p,bank.u,bank.xy,bank.cells]),'cpp_build_returncode':cp.returncode,'cpp_build_stderr':cp.stderr,'cpp_socket_result':result.stdout.strip(),'read_target_gas_arrays':False,'closed_loop_executed':False,'ros_workspace_compiled':False,'benchmark':'CPU single thread; complete Python event projection+network+variance+serialization-to-lists, excludes TCP latency/planner/forward'}
 (out/'interface_check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
