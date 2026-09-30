"""Single existing OPEN development target. No simulator or target-based selection."""
import sys,time
from pathlib import Path
import numpy as np
import torch
from train_exact_unet import exact_definitions
from audit_open49 import OUT,CACHE,load,dump,sha
from prepare_open49 import METHOD
from official_three_channel import location
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    c=load(OUT/'PRE_TARGET_TRAINING_FREEZE.json');trained=load(OUT/'TRAINING_RESULT.json');assert trained['freeze_sha256']==sha(OUT/'PRE_TARGET_TRAINING_FREEZE.json')
    assert trained['epochs']==c['max_epochs'] and sha(trained['checkpoint_path'])==trained['checkpoint_sha256']
    UNet,Loss,astsha=exact_definitions();assert astsha==trained['network_loss_ast_sha256']
    torch.set_num_threads(2);torch.use_deterministic_algorithms(True);torch.backends.cudnn.benchmark=False;torch.backends.cudnn.deterministic=True;torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    model=UNet(3,1).cuda();model.load_state_dict(torch.load(trained['checkpoint_path'],map_location='cpu',weights_only=True),strict=True);model.eval()
    base=Path(r'C:\GADEN_OCB_R2_ARCHIVE\d0_lite_20260930');p=base/'results/unet_three_channel_input.npy'
    if not p.exists():
        candidates=list(base.rglob('unet_three_channel_input.npy'));assert len(candidates)==1;p=candidates[0]
    receipt=load(base/'ocb_r2_cfg00_r01/on/map_receipt.json');x=np.load(p,allow_pickle=False);assert x.shape==(3,279,279)
    tensor=torch.from_numpy(x).unsqueeze(0).cuda();torch.cuda.synchronize();start=time.perf_counter()
    with torch.inference_mode():y=model(tensor).cpu().numpy()[0,0]
    torch.cuda.synchronize();latency=time.perf_counter()-start
    with torch.inference_mode():repeated=model(tensor).cpu().numpy()[0,0]
    assert y.tobytes()==repeated.tobytes()
    loc=location(y,receipt['resolution'],{k:receipt['origin'][k] for k in ['x','y']},receipt['height'],receipt['width'])
    truth=[-.6,1.95];error=float(np.linalg.norm(np.array(loc['centroid_xy'])-truth));improvement=1-error/c['engineering_gate']['zero_shot_mean_m']
    decision='D0B_VGR_TRAINED_DL_PROMISING' if error<=1.5 and improvement>=.5 else 'D0B_VGR_TRAINED_DL_PLAUSIBLE' if 1.5<error<=3 else 'D0B_VGR_TRAINED_DL_NO_GO'
    np.save(OUT/'TRAINED_LIKELIHOOD_MAP.npy',y,allow_pickle=False)
    h,w=receipt['height'],receipt['width'];occ=np.array(receipt['data']).reshape(h,w)
    pi,pj=np.unravel_index(np.argmax(y[:h,:w]),(h,w))
    result=dict(decision=decision,case_id=c['target_case'],truth_xy=truth,**loc,localization_error_m=error,zero_shot_mean_error_m=4.813847963183796,
        zero_shot_best_error_m=4.307897450632183,zero_shot_improvement_fraction=improvement,pmfs_error_m=.8320478542107147,
        pmfs_estimate_xy=[-1.4079720973968506,2.148707628250122],inference_s=latency,deterministic_repeat_byte_equal=True,
        best_epoch=trained['best_epoch'],epochs=trained['epochs'],checkpoint_sha256=trained['checkpoint_sha256'],input_sha256=sha(p),map_receipt_sha256=sha(base/'ocb_r2_cfg00_r01/on/map_receipt.json'),
        likelihood_sha256=sha(OUT/'TRAINED_LIKELIHOOD_MAP.npy'),peak_in_obstacle=bool(occ[pi,pj]>0),wall_mass_fraction=float(y[:h,:w][occ>0].sum()/y[:h,:w].sum()),
        result_scope='One known OPEN development case after a fixed 20-epoch supervised budget. Not an untouched test or a statistical PMFS superiority claim.',
        new_simulations=0,new_pmfs_closed_loops=0,confirmation_read=False,house03_read=False,
        route_status='TARGET_DOMAIN_TRAINED_BASELINE_NO_HEADROOM' if decision.endswith('NO_GO') else 'STOP_FOR_HUMAN_REVIEW')
    dump(OUT/'D0B_RESULT.json',result)
    fig,axes=plt.subplots(1,3,figsize=(13,4));res=receipt['resolution'];origin=receipt['origin'];ext=[origin['x'],origin['x']+w*res,origin['y'],origin['y']+h*res]
    for ax,img,title in zip(axes,[occ,x[2,:h,:w],y[:h,:w]],['VGR occupancy','Same observed encounters','Trained U-Net likelihood']):
        ax.imshow(img,origin='lower',extent=ext);ax.scatter(*truth,c='red',marker='*',s=80,label='Truth (evaluation only)');ax.set_title(title);ax.set_aspect('equal')
    axes[-1].scatter(*loc['centroid_xy'],c='cyan',marker='x',s=70,label='Official centroid');axes[-1].scatter(-1.4079720973968506,2.148707628250122,c='lime',marker='+',s=70,label='PMFS');axes[-1].legend(fontsize=7)
    fig.tight_layout();fig.savefig(OUT/'D0B_COMPARISON.png',dpi=160);plt.close(fig)
    print(result)
if __name__=='__main__':main()
