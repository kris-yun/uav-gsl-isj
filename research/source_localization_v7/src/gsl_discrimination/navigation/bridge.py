"""JSON-lines process bridge for a qualified simulator or robot runtime.

The process that senses the world owns ground truth. This client sends only
an action index and resource budget. A ROS/GADEN-specific process is a local
integration dependency, not a capability claimed by this reference package.
"""
from __future__ import annotations
from pathlib import Path
import json,subprocess,selectors,time,os
from contextlib import nullcontext
import numpy as np
from ..data import SynchronousBlock,QualificationError
from ..channel import FiniteChannel,JointPosterior
from ..m1_opponent.raw_joint import load_observation_model
from ..m3_audit import CoveragePlanner,AuditLedger
from ..m2_boundary import BoundaryMemoryConfig,CausalBoundaryMemory,FormationGeometry,score_paired_formations,rank_by_maxmin,LocalWind
from ..ledger import RawObservationLedger
from ..evaluation.maps import export_source_map
from .crossings import CrossingDetector


class JsonLineBackend:
    def __init__(self,command,stderr_path,timeout_s=30):
        if not isinstance(command,list) or not command or not all(isinstance(x,str) for x in command):
            raise ValueError('bridge command must be a JSON argument array')
        self.error_log=Path(stderr_path).open('w')
        self.process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                         stderr=self.error_log,bufsize=0,shell=False)
        os.set_blocking(self.process.stdout.fileno(),False)
        self.timeout_s=timeout_s;self.sequence=0;self._buffer=b''

    def call(self,method,**arguments):
        self.sequence+=1
        request={'id':self.sequence,'method':method,**arguments}
        self.process.stdin.write((json.dumps(request)+'\n').encode());self.process.stdin.flush()
        deadline=time.monotonic()+self.timeout_s
        # Windows select() only accepts sockets, not subprocess pipe handles.
        # Keep the same whole-line deadline and byte budget on both platforms.
        with (nullcontext(None) if os.name=='nt' else selectors.DefaultSelector()) as sel:
            if sel is not None:sel.register(self.process.stdout,selectors.EVENT_READ)
            while b'\n' not in self._buffer:
                remaining=deadline-time.monotonic()
                if remaining<=0:raise TimeoutError('backend did not complete a JSONL response before the deadline')
                if sel is None:
                    import ctypes,msvcrt
                    available=ctypes.c_ulong()
                    handle=ctypes.c_void_p(msvcrt.get_osfhandle(self.process.stdout.fileno()))
                    ok=ctypes.windll.kernel32.PeekNamedPipe(handle,None,0,None,ctypes.byref(available),None)
                    if not ok:
                        raise RuntimeError(f'backend pipe closed with an incomplete response, returncode={self.process.poll()}')
                    if available.value==0:
                        time.sleep(min(.005,remaining));continue
                elif not sel.select(remaining):
                    raise TimeoutError('backend did not complete a JSONL response before the deadline')
                try:chunk=os.read(self.process.stdout.fileno(),65536)
                except BlockingIOError:continue
                if not chunk:raise RuntimeError(f'backend exited with an incomplete response, returncode={self.process.poll()}')
                self._buffer+=chunk
                if len(self._buffer)>8*1024**2:raise ValueError('backend response exceeds 8 MiB message budget')
        line,self._buffer=self._buffer.split(b'\n',1)
        response=json.loads(line)
        if response.get('id')!=self.sequence:raise ValueError('out-of-order bridge response')
        if response.get('error'):raise RuntimeError(response['error'])
        return response['result']

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:self.process.kill();self.process.wait(timeout=5)
        for f in (self.process.stdin,self.process.stdout,self.error_log):
            if f:f.close()


def _wind(sample):
    value=sample.get('local_wind')
    return None if value is None else LocalWind(np.asarray(value['velocity_xy']),float(value['time_s']))


def _check_action_geometry(block,action,channel):
    catalogue=channel.metadata.get('action_points_m')
    if catalogue is None:raise QualificationError('model does not pin action geometry')
    expected=np.asarray(catalogue[action],dtype=float)
    observed=np.asarray(block.positions_m)
    if expected.shape[-1]==2:observed=observed[...,:2]
    if observed.shape!=expected.shape or not np.allclose(observed,expected,rtol=0,atol=1e-6):
        raise QualificationError('actual paired readout geometry does not match chosen action')


def run_bridge(model_directory,command,output,budget_s=300.):
    out=Path(output)
    if (out/'BRIDGE_RESULT.json').exists():raise ValueError('output is frozen')
    out.mkdir(parents=True,exist_ok=True)
    model=load_observation_model(model_directory);ch=model.channel
    post=JointPosterior(ch);audit=AuditLedger(ch);planner=CoveragePlanner()
    rawledger=RawObservationLedger(out/'raw_ledger');rng=np.random.default_rng(77331)
    bridge=JsonLineBackend(command,out/'backend.stderr.log');rows=[];elapsed=0.;realization_id=None
    try:
        context=bridge.call('describe')
        if context.get('schema')!='gsl-action-bridge-1':raise QualificationError('unsupported bridge protocol')
        if context.get('future_truth_available_to_policy',True):raise QualificationError('backend violates causal policy boundary')
        if context.get('action_names')!=ch.action_names:raise QualificationError('action catalogue mismatch')
        if not np.allclose(context['action_cost_upper_bounds_s'],ch.costs):raise QualificationError('cost contract mismatch')
        if context.get('safety_checked_before_execute') is not True:
            raise QualificationError('backend must check obstacle, separation and dynamics before execution')
        config=BoundaryMemoryConfig(**context['boundary_config'])
        memory=CausalBoundaryMemory(config);detector=CrossingDetector(config.min_pre_s,config.min_post_s)
        initial=context['initial_state'];position=np.asarray(initial['position_xy']);clock=float(initial['time_s'])
        memory.update(timestamp_s=clock,position_xy=position,heading_rad=initial['heading_rad'],local_wind=_wind(initial))
        detector.update(clock,bool(initial['gas_detected']))
        fp=Path(model_directory)/'formation_predictions.npz'
        if not fp.exists():raise QualificationError('calibrated M2 geometry file is required; do not invent source gradients')
        with np.load(fp) as z:
            centers=z['centers'];means=z['means'];grads=z['gradients']
            if 'joint_covariance' in z:
                covariance=z['joint_covariance'];covariance_source='frozen_training_geometry_file'
            elif context.get('scope')=='CONTROLLED_LEVEL1':
                covariance=np.asarray(context['calibrated_even_odd_covariance']);covariance_source='declared_level1_construction'
            else:raise QualificationError('native geometry requires TRAIN-frozen covariance, not backend state statistics')
        g=context['formation_geometry'];geometry=FormationGeometry(np.array(g['lower_xy']),np.array(g['upper_xy']),
              g['min_separation'],g['max_separation'],g['linearization_radius'])
        separations=g['separations'];orientations=g['orientations_rad']
        costs=ch.costs.reshape(len(centers),len(separations),len(orientations))
        while True:
            affordable=np.flatnonzero(ch.costs<=budget_s-elapsed+1e-9)
            if not len(affordable):break
            try:
                tube=memory.make_return_tube(timestamp_s=clock,current_position_xy=position,
                     length=g['tube_length'],base_radius=g['tube_base_radius'],
                     position_covariance=np.asarray(g['position_covariance']),
                     drift_variance_rate=g['drift_variance_rate'],sensor_delay_uncertainty_s=g['sensor_delay_uncertainty_s'])
            except ValueError:tube=None
            scored=score_paired_formations(center_xy=centers,source_means=means,source_gradients=grads,
                  joint_covariance=covariance,costs=costs,separations=separations,orientations_rad=orientations,
                  geometry=geometry,return_tube=tube)
            if len(scored.actions)!=ch.shape[0]:raise QualificationError('formation and likelihood action indices differ')
            frozen_points=ch.metadata.get('action_points_m')
            if frozen_points is None:raise QualificationError('frozen action geometry is missing')
            for i,action_geometry in enumerate(scored.actions):
                points=np.asarray(frozen_points[i])[...,:2]
                if points.shape!=(2,2) or not np.allclose(action_geometry.endpoints_xy,points,atol=1e-6,rtol=0):
                    raise QualificationError('formation action ordering differs from likelihood geometry')
            ranked=rank_by_maxmin(scored);mask=np.zeros(ch.shape[0],dtype=bool)
            mask[ranked[:max(1,ch.shape[0]//3)]]=True
            sub=FiniteChannel(ch.probabilities[affordable],ch.costs[affordable],ch.source_xy,
                 [ch.action_names[x] for x in affordable],ch.source_ids,ch.nuisance_prior,ch.metadata)
            incumbent=int(np.argmax(post.source));challenger=None
            if incumbent not in audit.compatible_now:
                candidates=[j for j in audit.compatible_now if j!=incumbent]
                if candidates:challenger=min(candidates,key=lambda j:(audit.log_e_values[j],j))
            plan=planner.plan(sub,post.predict()[affordable],post.source,len(rows),challenger=challenger,exploit_mask=mask[affordable])
            action=int(rng.choice(affordable,p=plan.probabilities));audit.prepare(action,model_version='frozen-bridge-model')
            observed=bridge.call('execute',action=action,remaining_budget_s=budget_s-elapsed)
            if observed.get('safety_passed') is not True:raise QualificationError('backend reports unsafe/incomplete action')
            cost=float(observed['cost_s'])
            if not np.isfinite(cost) or cost<=0 or cost>ch.costs[action]+1e-6:raise QualificationError('measured execution exceeds the predeclared finite cost bound')
            block=SynchronousBlock.load_npz(observed['block_path'])
            block.qualification.require('synchronous_spatial','physical_clock','native_samples_only')
            readout_contract=ch.metadata.get('observation_contract')
            if readout_contract is None and context.get('scope')=='CONTROLLED_LEVEL1':
                readout_contract={'units':'ppm','sensor_ids_order':['plus','minus']}
            if {'units':block.units,'sensor_ids_order':list(block.sensor_ids)}!=readout_contract:
                raise QualificationError('live readout units/sensor identity differs from calibration')
            _check_action_geometry(block,action,ch)
            if realization_id is None:realization_id=block.realization_id
            if block.realization_id!=realization_id:raise QualificationError('backend changed physical realization within episode')
            end_state=observed['end_state'];end_clock=float(end_state['time_s'])
            if not np.isfinite(end_clock) or not np.isclose(end_clock,clock+cost,rtol=0,atol=1e-3):
                raise QualificationError('end clock and measured action cost disagree')
            if block.times_s[0]<clock-1e-3 or block.times_s[-1]>end_clock+1e-3:
                raise QualificationError('readout is outside the executed physical interval')
            if context.get('scope')!='CONTROLLED_LEVEL1':
                block.qualification.require('source_occupancy_validated','native_active_closed_loop','sensor_response_calibrated')
            if model.contract.continuous:block.require_dynamic(with_wind=False)
            rawledger.append(block,action);symbol=int(model.encode(action,block.values,block.times_s))
            post.update(action,symbol,block.block_id);snapshot=audit.update(action,symbol,block.block_id)
            # Same causal stream can be supplied to competing planners. It is
            # not silently counted as independent posterior evidence here.
            rejected_memory=[]
            for sample in observed.get('motion_samples',[]):
                if not clock<float(sample['time_s'])<=end_clock+1e-3:
                    raise QualificationError('motion sample is not in the executed past interval')
                event=detector.update(float(sample['time_s']),bool(sample['gas_detected']))
                arguments=dict(timestamp_s=float(sample['time_s']),position_xy=sample['position_xy'],
                               heading_rad=float(sample['heading_rad']),local_wind=_wind(sample))
                try:memory.update(**arguments,event=event)
                except ValueError as exc:
                    if event is None:raise
                    rejected_memory.append(str(exc));memory.update(**arguments)
            state=end_state;position=np.asarray(state['position_xy']);clock=end_clock
            elapsed+=cost
            row={'step':len(rows),'action':action,'symbol':symbol,'elapsed_s':elapsed,'source_map':post.map_points(),
                 'posterior':post.source.tolist(),'audit_list':list(snapshot.compatible_now),'policy':plan.info,
                 'm2_status':scored.status,'audit_challenger':challenger,'backend_scope':context.get('scope'),
                 'covariance_source':covariance_source,
                 'rejected_boundary_events':rejected_memory}
            rows.append(row)
            with (out/'steps.jsonl').open('a') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
        result={'status':'BRIDGE_LOOP_COMPLETE','scope':context.get('scope'),'steps':len(rows),
                'elapsed_s':elapsed,'native_backend_certification':context.get('qualification_receipt'),
                'source_map':post.map_points(),'oracle_access':False,
                'risk_guarantee':'conditional/model-relative; read the native qualification receipt'}
        (out/'BRIDGE_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
        export_source_map(ch.source_xy,post.source,out/'source_probability_map.npz')
        return result
    finally:bridge.close()
