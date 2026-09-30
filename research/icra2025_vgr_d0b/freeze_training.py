"""Freeze a finite engineering budget before any trained target prediction."""
import ast,csv,hashlib,json,sys
from pathlib import Path
from audit_open49 import OUT,ROOT,CACHE,load,dump,sha
METHOD=Path(r'D:\ZYC\Topography-aware-Gas-Source')
UP=METHOD/'Topography-aware-Gas-Source-Localization-lfs'

def main():
    audit=load(OUT/'OPEN49_TRAINABILITY.json');assert audit['decision']=='OPEN49_TRAINABLE'
    prefixes=load(OUT/'PREFIX_MANIFEST.json');tr={p['case_id'] for p in prefixes if p['split']=='train'};va={p['case_id'] for p in prefixes if p['split']=='validation'}
    assert tr.isdisjoint(va)
    trseeds={(p['house'],p['physical_seed']) for p in prefixes if p['split']=='train'};vaseeds={(p['house'],p['physical_seed']) for p in prefixes if p['split']=='validation'};assert trseeds.isdisjoint(vaseeds)
    trsources={(p['house'],p['source_id']) for p in prefixes if p['split']=='train'};vasources={(p['house'],p['source_id']) for p in prefixes if p['split']=='validation'};assert trsources.isdisjoint(vasources)
    config=dict(initialization='random, no checkpoint warm start',seed=2026093019,
        architecture='exact upstream GSL_train.ipynb cell2 UNet(3,1)',loss='exact upstream CustomLoss(positive_weight=5)',
        optimizer='Adam',learning_rate=1e-5,weight_decay=.1,batch_size=8,
        scheduler=dict(name='ReduceLROnPlateau',mode='min',factor=.5,patience=5),
        max_epochs=20,early_stopping=None,checkpoint='lowest grouped-validation official loss; strict decrease; earliest tie',
        budget_rationale='One bounded target-domain engineering headroom test: 20 fixed epochs, same official loss/optimizer/LR/batch. Official notebook full run uses 100 epochs. No continuation or tuning after target.',
        precision='float32, no AMP',data_loader_workers=0,rotations=[0,90,180,270],normalization='none',
        deterministic=True,training_padding=-1,inference_padding=0,
        split='Historical entire-source train/dev split preserved; additional historical OPEN H02 trajectory assigned train; no prefix/rotation leakage',
        train_physical_runs=len(tr),validation_physical_runs=len(va),train_sources=sorted('/'.join(s) for s in trsources),validation_sources=sorted('/'.join(s) for s in vasources),
        train_prefixes=sum(p['split']=='train' for p in prefixes),validation_prefixes=sum(p['split']=='validation' for p in prefixes),
        train_augmented_samples=4*sum(p['split']=='train' for p in prefixes),validation_augmented_samples=4*sum(p['split']=='validation' for p in prefixes),
        input_manifest_sha256=sha(OUT/'PREFIX_MANIFEST.json'),audit_sha256=sha(OUT/'OPEN49_TRAINABILITY.json'),
        notebooks_sha256={n:sha(UP/'train'/n) for n in ['GSL_train.ipynb','GSLInference.ipynb','labeler.ipynb']},
        code_sha256={p.name:sha(p) for p in (ROOT/'research/icra2025_vgr_d0b').glob('*.py')},
        local_python=r'D:\Anaconda\envs\DL_5060_New\python.exe',checkpoint_directory=str(CACHE/'training'),
        target_case='ocb_r2_cfg00_r01',target_new_run_forbidden=True,confirmation=False,house03=False,
        engineering_gate=dict(promising_max_m=1.5,promising_min_improvement_fraction=.5,plausible_max_m=3.,zero_shot_mean_m=4.813847963183796,pmfs_reference_m=.8320478542107147),
        test_role='Previously observed OPEN development test, not untouched validation; training z=.2 vs current target z=.3 and original source location differ.')
    dump(OUT/'PRE_TARGET_TRAINING_FREEZE.json',config)
    print('PRE_TARGET_TRAINING_FREEZE',sha(OUT/'PRE_TARGET_TRAINING_FREEZE.json'));print('TRAIN',len(tr),'VAL',len(va),'PREFIXES',len(prefixes))
if __name__=='__main__':main()
