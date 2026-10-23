"""TRAIN full histories; DEV only the frozen pair and single/window."""
import csv,json,sys,time,tarfile,hashlib
import numpy as np
from protocol import *
from recover_assets import OCC,run_path
from extract_existing_worlds import points_for_probes
from gaden_executor.reader import NativeQuery,decode_frame

def get_timeline(data):
 rows=list(csv.DictReader(data.decode().splitlines(),delimiter='\t'))
 return rows,np.array([float(r['internal_simulation_time_s']) for r in rows])

def extract(stage):
 c=config();start=time.perf_counter();receipt=OUT/(stage.upper()+'_EXTRACTION.json')
 assert not receipt.exists()
 if stage=='dev':
  f=json.loads((OUT/'SELECTION_FREEZE.json').read_text());sel=f['selected']
  probes=sorted(set([sel['probe_L'],sel['probe_R'],sel['global_single']['probe_rank']]))
  extra=OUT/'UNKNOWN_SINGLE_CONTROL_FREEZE.json'
  if extra.exists():probes=sorted(set(probes+[json.loads(extra.read_text())['selected']['probe_rank']]))
  prototype=json.loads((OUT/'MODEL_FREEZE.json').read_text());assert prototype['selection_sha256']==sha(OUT/'SELECTION_FREEZE.json')
  keep=np.array(sel['window_indices']);repeats=(3,4)
 else:probes=list(range(1,31));keep=None;repeats=(1,2)
 points=points_for_probes([c['all_probe_pools'][i-1] for i in probes])
 query=NativeQuery(OCC,NATIVE/'native_query.dll');worlds=[];all_times=None
 scratch=OUT/'scratch/frame';scratch.parent.mkdir(exist_ok=True)
 for source in ('A','B','C'):
  for repeat in repeats:
   key=f'v7h3_{source}_r{repeat:02d}';is_old=source=='A'
   archive=None
   if is_old:
    old=f'ocb_r2_cfg00_r{repeat:02d}';root=run_path(old)
    lines=(root/'RECORD_TIMELINE.tsv').read_bytes();rows,times=get_timeline(lines)
    assert hashlib.sha256(lines).hexdigest()==c['expected_timeline_sha256']
    assets=json.loads((PROJECT/'results/native_20261023/assets'/(old+'.json')).read_text())
    hashes={x['name']:x['sha256'] for x in assets['files']}
   else:
    ar=json.loads((OUT/'archives'/(key+'.json')).read_text());p=OUT/ar['archive'];assert sha(p)==ar['sha256']
    archive=tarfile.open(p,'r:gz');members={x.name:x for x in archive.getmembers() if x.isfile()}
    assert all(Path(n).parts[0]==key and '..' not in Path(n).parts for n in members)
    read=lambda name:archive.extractfile(members[key+'/'+name]).read()
    manifest=json.loads(read('RUN_MANIFEST.json'));assert manifest['status']=='PASS_ORIGINAL_GENERATION'
    assert manifest['original_binary_sha256']==c['expected_identity']['binary_sha256']
    lines=read('RECORD_TIMELINE.tsv');assert hashlib.sha256(lines).hexdigest()==c['expected_timeline_sha256']
    rows,times=get_timeline(lines);hashes={x['name']:x['sha256'] for x in json.loads(read('FRAME_SHA256.json'))}
   idx=np.arange(len(times)) if keep is None else keep
   assert len(times)==1803 and np.diff(times).max()<=.61
   use_times=times[idx]
   if all_times is not None:assert np.array_equal(use_times,all_times)
   all_times=use_times
   if is_old and stage=='train':
    prior=PROJECT/'results/source_pair_observability_20261023'
    er=json.loads((prior/'TRAIN_EXTRACTION_RECEIPT.json').read_text())
    ref=next(w for w in er['worlds'] if w['run_id']==old);assert sha(prior/ref['file'])==ref['sha256']
    with np.load(prior/ref['file']) as z:values=z['values_ppm'];assert np.array_equal(z['times_s'],times)
   else:
    # Process gzip members in their physical archive order, not numeric frame
    # order; fill the original timestamp axis explicitly. Random gzip seeks
    # otherwise decompress the same archive hundreds of times.
    order=list(idx) if is_old else sorted(idx,key=lambda i:members[key+'/iteration_'+str(rows[int(i)]['record_index'])].offset)
    output=np.empty((len(idx),len(probes)),dtype=float);positions={int(i):j for j,i in enumerate(idx)}
    for i in order:
     name='iteration_'+str(rows[int(i)]['record_index'])
     data=(root/name).read_bytes() if is_old else read(name)
     assert hashlib.sha256(data).hexdigest()==hashes[name]
     scratch.write_bytes(data);frame=decode_frame(scratch)
     assert np.array_equal(np.array(frame['source_xyz'],dtype=np.float32),np.array(c['source_xyz_m'][c['source_ids'].index(source)],dtype=np.float32))
     assert frame['gas_type']==int(c['base_parameters']['gas_type'])
     output[positions[int(i)]]=query.query(frame,points).reshape(len(probes),4).mean(axis=1)
    values=output
   target=OUT/(stage+'_arrays')/(key+'.npz');target.parent.mkdir(exist_ok=True)
   if target.exists():
    with np.load(target) as prior:assert np.array_equal(values,prior['values_ppm']) and np.array_equal(use_times,prior['times_s'])
   np.savez_compressed(target,values_ppm=values,times_s=use_times,probe_ranks=np.array(probes))
   worlds.append({'run_id':key,'original_run':old if is_old else key,'source':source,'repeat':repeat,
   'master_seed':c['master_seeds'][repeat-1],'file':str(target.relative_to(OUT)),'sha256':sha(target),
   'frames_decoded_this_stage':0 if is_old and stage=='train' else len(idx),'reused_previous_full_TRAIN_extraction':bool(is_old and stage=='train')})
   if archive:archive.close()
   print('NATIVE_READOUT_COMPLETE',stage,key,len(values),len(probes),flush=True)
 if scratch.exists():scratch.unlink() # Only our single generated scratch frame.
 write(stage.upper()+'_EXTRACTION.json',{'stage':stage,'worlds':worlds,'source_ids':['A','B','C'],
 'times_s':all_times.tolist(),'probe_ranks':probes,'wall_s':time.perf_counter()-start,
 'DEV_response_decoded_before_selection':False,'native_query_sha256':sha(NATIVE/'native_query.dll'),
 'no_interpolation':True,'ideal_readout_not_hardware_PID':True})

if __name__=='__main__':
 assert sys.argv[1:] in (['train'],['dev']);extract(sys.argv[1])
