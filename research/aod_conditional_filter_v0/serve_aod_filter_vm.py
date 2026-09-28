#!/usr/bin/env python3
"""Causal, non-neural AOD filter sidecar for the existing PMFS planner protocol."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import socket
import sys

import numpy as np

from bank import TemplateBank
from episode_io import align_publications, predict_sensor
from gain_innovation_bank import GainInnovationBank

V0=Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927')
sys.path.insert(0,str(V0))
from tools.serve import text_reply


def rows(path):
    with Path(path).open(newline='') as f:
        return list(csv.DictReader(f))


class AODSession:
    def __init__(self,bank,cfg,blocks,samples,sensor,trace,arrays):
        if cfg['status']!='AOD_FILTER_TRAIN_ONLY_PARAMETERS_FROZEN':
            raise ValueError('unfrozen OPEN training calibration')
        self.bank=bank;self.metadata={'non_neural':True,'calibration':'train40_moments'}
        self.cfg=cfg;self.blocks=Path(blocks);self.samples=Path(samples)
        self.sensor=Path(sensor);self.trace=Path(trace);self.arrays=Path(arrays)
        self.arrays.mkdir(parents=True,exist_ok=False)
        self.run_id=None

    def reset(self,run_id,expected_bank,prior=None):
        if not run_id or expected_bank!=self.bank.fingerprint:
            raise ValueError('run/bank mismatch')
        if prior is not None:raise ValueError('only fixed uniform prior admitted')
        self.run_id=run_id;self.last_event=-1;self.last_time=0.;self.last_digest=None;self.last_response=None
        self.model=GainInnovationBank(np.ones(len(self.bank.ids))/len(self.bank.ids),
                 gain_mean=self.cfg['gain_mean'],gain_variance=self.cfg['gain_variance'],
                 discrepancy_variance=self.cfg['discrepancy_variance'],
                 correlation_time_s=self.cfg['correlation_time_s'],
                 measurement_variance=self.cfg['measurement_variance'],
                 positive_gain=self.cfg['positive_gain'])
        return {'status':'RESET','bank_id':self.bank.fingerprint,
                'sources':len(self.bank.ids),'map_cells':self.bank.n}

    def observe(self,event):
        expected={'run_id','event_id','time_s','x','y','z','concentration_ppm'}
        if set(event)!=expected or event['run_id']!=self.run_id:
            raise ValueError('event schema or run identity')
        eid=event['event_id'];t=float(event['time_s']);xy=np.array([event['x'],event['y']],float)
        y=float(event['concentration_ppm'])
        if not isinstance(eid,int) or eid<0 or eid>127 or not np.isfinite([t,*xy,y]).all() or y<0:
            raise ValueError('event domain')
        digest=hashlib.sha256(json.dumps(event,sort_keys=True).encode()).hexdigest()
        if eid==self.last_event:
            if digest!=self.last_digest:raise ValueError('duplicate event changed')
            return self.last_response
        if eid!=self.last_event+1 or t<=self.last_time:
            raise ValueError('noncausal event order')
        if abs(float(event['z'])-float(self.bank.meta['height_m']))>1e-4:
            raise ValueError('bank/sensor height')
        blocks=[b for b in rows(self.blocks) if int(b['measurement_cycle_id'])==eid+1]
        ss=sorted([s for s in rows(self.samples) if int(s['measurement_cycle_id'])==eid+1],
                  key=lambda r:int(r['sample_index']))
        if len(blocks)!=1 or len(ss)!=10:raise RuntimeError('current event not flushed')
        block=blocks[0]
        bxy=np.array([float(block['pose_x']),float(block['pose_y'])])
        if np.linalg.norm(xy-bxy)>.01 or abs(y-float(block['gas_value_used_by_algorithm']))>2e-5+5e-6*max(1.,y):
            raise RuntimeError('STEP/block mismatch')
        sensor=rows(self.sensor)
        ids=align_publications(ss,sensor,float(block['sim_time_start']),
                               float(block['sim_time_end']),xy)
        response=predict_sensor(self.bank,sensor,int(ids.max()))
        m=response[ids].mean(axis=0)
        update=self.model.update(eid,t-self.last_time,y,m)
        q=update.source_probability
        src,var=self.bank.planner_maps(q)
        top=int(np.argmax(q))
        self.last_event=eid;self.last_time=t;self.last_digest=digest
        record={'event_id':eid,'time_s':t,'xy':xy.tolist(),'observed_ppm':y,
                'sample_publication_ids':ids.tolist(),'top_source_id':self.bank.ids[top],
                'top_probability':float(q[top]),'source_probability_sum':float(q.sum()),
                'gain_mean_top':float(self.model.mu[top,0]),
                'discrepancy_mean_top':float(self.model.mu[top,1]),
                'innovation_top':float(y-update.gaussian_envelope_prediction[top]),
                'innovation_variance_top':float(update.gaussian_envelope_innovation_variance[top])}
        with self.trace.open('a') as f:f.write(json.dumps(record,allow_nan=False)+'\n')
        np.savez_compressed(self.arrays/f'event_{eid:03d}.npz',
                            template=m,predicted_mean=update.gaussian_envelope_prediction,
                            predicted_variance=update.gaussian_envelope_innovation_variance,
                            predictive_log_likelihood=update.predictive_log_likelihood,
                            q=q,gain_state=self.model.mu[:,0],discrepancy_state=self.model.mu[:,1],
                            gain_variance=self.model.P[:,0,0],discrepancy_variance=self.model.P[:,1,1])
        self.last_response={'status':'OK','run_id':self.run_id,'event_id':eid,
                            'bank_id':self.bank.fingerprint,'q':q.tolist(),
                            'source_map':src.tolist(),'variance_of_hit_prob':var.tolist()}
        return self.last_response


def main():
    ap=argparse.ArgumentParser()
    for name in ('bank','calibration','measurement-blocks','measurement-samples',
                 'sensor-trace','trace','arrays','log'):
        ap.add_argument('--'+name,required=True)
    ap.add_argument('--tcp-port',required=True,type=int)
    a=ap.parse_args()
    bank=TemplateBank.load(a.bank)
    cfg=json.loads(Path(a.calibration).read_text())
    s=AODSession(bank,cfg,a.measurement_blocks,a.measurement_samples,a.sensor_trace,a.trace,a.arrays)
    with Path(a.log).open('a',buffering=1) as log,socket.socket() as server:
        server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        server.bind(('127.0.0.1',a.tcp_port));server.listen(1)
        while True:
            conn,_=server.accept()
            with conn:
                conn.settimeout(30)
                with conn.makefile('r',encoding='ascii') as stream:
                    for line in stream:
                        try:
                            if len(line)>4096 or not line.endswith('\n'):raise ValueError('invalid request')
                            answer=text_reply(line,s);status=answer.split()[0]
                        except Exception as exc:
                            status='ERROR';answer='ERROR '+str(exc).replace('\n',' ')+'\n'
                        log.write(json.dumps({'text':line.strip(),'status':status})+'\n')
                        conn.sendall(answer.encode('ascii'))

if __name__=='__main__':main()
