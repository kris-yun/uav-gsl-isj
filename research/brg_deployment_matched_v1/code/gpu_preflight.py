"""Shape and device check only; does not train or evaluate a localization case."""
import sys,json,platform,hashlib
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'v0_execution_archive'))
from model import CandidateBRG,ModelConfig

def main():
    torch.manual_seed(2026092801)
    torch.set_num_threads(2)
    available=torch.cuda.is_available()
    device='cuda' if available else 'cpu'
    rows=[]
    for variant,hidden,rounds in [('gru',35,1),('brg',32,3),('ungated',32,3)]:
        model=CandidateBRG(ModelConfig(hidden=hidden,rounds=rounds,variant=variant,obs_dim=6,cue_dim=6)).to(device)
        with torch.inference_mode():
            o=torch.zeros(1,6,device=device);c=torch.zeros(1,630,6,device=device)
            z,h=model.step(o,c,model.initial(1,630))
        assert z.shape==(1,630) and h.shape==(1,630,hidden) and torch.isfinite(z).all()
        rows.append({'variant':variant,'hidden':hidden,'rounds':rounds,'obs_dim':6,'cue_dim':6,'parameters':model.parameter_count,'active_parameters':model.active_parameter_count,'output_shape':list(z.shape),'finite':True})
    result={'status':'DEVICE_AND_MODEL_INPUT_CHECK_ONLY','torch':str(torch.__version__),'python':platform.python_version(),'cuda_available':available,'cuda_version':torch.version.cuda,'device':device,'gpu':torch.cuda.get_device_name(0) if available else None,'gpu_total_bytes':torch.cuda.get_device_properties(0).total_memory if available else None,'models':rows,'trained_weights_created':0,'plumes_read':0,'model_source_sha256':hashlib.sha256((ROOT/'v0_execution_archive/model.py').read_bytes()).hexdigest()}
    (ROOT/'evidence/GPU_PREFLIGHT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
