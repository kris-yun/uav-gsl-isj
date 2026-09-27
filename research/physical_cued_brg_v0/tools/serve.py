#!/usr/bin/env python3
"""Local sidecar. JSON-lines stdio or a simple line protocol on localhost TCP.
No ROS dependency, no shell execution, no arbitrary remotely supplied weights.
"""
import argparse,json,socket,sys,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import torch
from pmfs_brg.model import load_checkpoint
from pmfs_brg.bank import TemplateBank
from pmfs_brg.runtime import InferenceSession

def dispatch(req,session):
    op=req.pop('op',None)
    if op=='hello':
        return {'status':'HELLO','bank_id':session.bank.fingerprint,'source_ids':session.bank.ids,'source_cells':session.bank.cells.tolist(),'width':session.bank.nx,'height':session.bank.ny,'metadata':session.bank.meta,'model_metadata':session.metadata}
    if op=='reset':return session.reset(**req)
    if op=='observe':return session.observe(req)
    raise ValueError('unknown operation')

def text_reply(line,session):
    v=line.strip().split()
    if not v:raise ValueError('empty command')
    if v[0]=='HELLO' and len(v)==1:
        b=session.bank
        return f'HELLO {b.fingerprint} {len(b.ids)} {b.n} {b.nx} {b.ny} {b.dx:.17g} {b.ox:.17g} {b.oy:.17g}\n'
    if v[0]=='RESET' and len(v)==3:
        r=session.reset(v[1],v[2]);return f'RESET {r["bank_id"]}\n'
    if v[0]=='STEP' and len(v)==9:
        _,run,eid,t,x,y,z,c,bank=v
        if bank!=session.bank.fingerprint:raise ValueError('wrong bank')
        r=session.observe(dict(run_id=run,event_id=int(eid),time_s=float(t),x=float(x),y=float(y),z=float(z),concentration_ppm=float(c)))
        parts=[f'OK {eid} {bank} {len(r["q"])} {len(r["source_map"])}']
        for k in ['q','source_map','variance_of_hit_prob']:parts.append(' '.join(format(a,'.17g') for a in r[k]))
        return '\n'.join(parts)+'\n'
    raise ValueError('bad text command')

def main():
 p=argparse.ArgumentParser();p.add_argument('--checkpoint',required=True);p.add_argument('--bank',required=True);p.add_argument('--allow-warmstart',action='store_true');p.add_argument('--tcp-port',type=int);p.add_argument('--threads',type=int,default=1);p.add_argument('--log',required=True);a=p.parse_args()
 torch.set_num_threads(a.threads);model,meta=load_checkpoint(a.checkpoint);bank=TemplateBank.load(a.bank)
 session=InferenceSession(model,meta,bank,a.allow_warmstart)
 log=open(a.log,'a',buffering=1)
 def record(req,status):log.write(json.dumps({'request':req,'status':status},allow_nan=False)+'\n')
 if a.tcp_port is None:
  for line in sys.stdin:
   try:
    req=json.loads(line);copy=dict(req);ans=dispatch(req,session);record(copy,ans['status'])
   except Exception as exc:
    ans={'status':'ERROR','error':str(exc)};record({'raw':line.strip()},'ERROR')
   print(json.dumps(ans,allow_nan=False),flush=True)
 else:
  with socket.socket() as server:
   server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);server.bind(('127.0.0.1',a.tcp_port));server.listen(1)
   while True:
    conn,_=server.accept()
    with conn:
     conn.settimeout(30.)
     with conn.makefile('r',encoding='ascii') as stream:
      while True:
       line=stream.readline(4097)
       if not line:break
       try:
        if len(line)>4096 or not line.endswith('\n'):raise ValueError('oversized/incomplete message')
        answer=text_reply(line,session);record({'text':line.strip()},answer.split()[0])
       except Exception as exc:
        answer='ERROR '+str(exc).replace('\n',' ')+'\n';record({'text':line.strip()},'ERROR')
       conn.sendall(answer.encode('ascii'))
if __name__=='__main__':main()
