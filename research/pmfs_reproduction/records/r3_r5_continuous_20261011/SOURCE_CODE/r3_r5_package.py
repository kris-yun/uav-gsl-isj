"""Package compact complete posterior audit + chosen full predictive traces + raw bank."""
import csv,hashlib,json,pathlib,shutil,subprocess,sys,zipfile
import numpy as np
BASE=pathlib.Path(__file__).resolve().parents[1];OUT=BASE/'outputs/PMFS_R3_R5_CONTINUOUS_20261011';CORE=BASE/'outputs/PMFS_R3_R5_CONTINUOUS_20261011_CORE'
SAMPLE=['T00','T04','T18','T34'] # chosen by task design, not scores: dev/test & constant/dynamic
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    if CORE.exists():raise RuntimeError('Core already exists; no silent overwrite')
    CORE.mkdir();raw=OUT/'raw'
    for f in OUT.iterdir():
        if f.is_file() and not f.name.endswith('.stderr.log'):shutil.copy2(f,CORE/f.name)
    for name in ['authorization','literature']:
        shutil.copytree(OUT/name,CORE/name)
    parent=BASE/'outputs/PMFS_FULL_DOMAIN_R2_20261011_CORE';r3audit=CORE/'audit_R3';r3audit.mkdir()
    for name in ['SOURCE_CATALOG_AND_COVERAGE.json','SOURCE_CELL_TO_REGION.npy','FUTURE_PAIRED_SOURCE_METRICS.csv','FUTURE_READOUT_PAIRED_EFFECTS.csv','SOURCE_REPRESENTATIVE_AND_TOP5_TIE_DIAGNOSTIC.csv']:
        shutil.copy2(parent/name,r3audit/name)
    shutil.copy2(parent/'geometry/ATOMIC_SOURCE_CATALOG.csv',r3audit/'ATOMIC_SOURCE_CATALOG.csv')
    shutil.copy2(parent/'future_inference/FULL_SOURCE_POSTERIORS.npz',r3audit/'FULL_SOURCE_POSTERIORS.npz')
    shutil.copy2(parent/'evaluation_only/FUTURE_TRUTH.json',r3audit/'FUTURE_TRUTH.json')
    pred=np.load(parent/'future_inference_inputs/ALL_CANDIDATE_PREDICTIONS.npz');np.savez_compressed(r3audit/'PUBLIC_B_PPM_AND_EVENTS.npz',PUBLIC_B_PPM=pred['PUBLIC_B_PPM'],PUBLIC_B_EVENTS=pred['PUBLIC_B_EVENTS'])
    for oid in ['Z00','Z01','Z02','Z03','Z04','Z05']:
        shutil.copy2(parent/f'future_inference_inputs/observations/{oid}/EVENTS_50.csv',r3audit/f'{oid}_EVENTS_50.csv')
    scripts=CORE/'SOURCE_CODE';scripts.mkdir()
    for f in (BASE/'work').glob('r[34]*.py'):shutil.copy2(f,scripts/f.name)
    shutil.copy2(BASE/'work/r3_r5_verify.py',CORE/'verify_bundle.py')
    slim=CORE/'audit_slim';slim.mkdir();obs=CORE/'audit_observations';obs.mkdir();full=CORE/'audit_full';full.mkdir();ev=CORE/'audit_evaluation_only';ev.mkdir()
    registry=json.loads((OUT/'R4_PUBLIC_OBSERVATION_REGISTRY.json').read_text())
    for rec in registry:
        task=rec['task_id'];shutil.copy2(raw/f'observations/{task}.npz',obs/f'{task}.npz');t=np.load(raw/f'evaluation_only/{task}.npz')
        np.savez_compressed(ev/f'{task}.npz',**{k:t[k] for k in t.files if k!='gas_fields'})
    for f in sorted((raw/'inference').glob('*.npz')):
        a=np.load(f);np.savez_compressed(slim/f.name,**{k:a[k] for k in ['source_posterior','source_log_score','gas_prequential_log_evidence','wind_estimate','conditional_ESS']});shutil.copy2(f.with_suffix('.json'),slim/f.with_suffix('.json').name)
        if f.stem.split('__')[0] in SAMPLE:shutil.copy2(f,full/f.name)
    rawmanifest={str(f.relative_to(OUT)).replace('\\','/'):sha(f) for f in sorted(raw.rglob('*')) if f.is_file()}
    (CORE/'RAW_BANK_SHA256.json').write_text(json.dumps(rawmanifest,indent=2)+'\n',encoding='utf-8')
    (OUT/'RAW_BANK_SHA256.json').write_text(json.dumps(rawmanifest,indent=2)+'\n',encoding='utf-8')
    provenance={'core_slim':'Exact float64 subset from original NPZ, no lossy conversion','full_prediction_samples':SAMPLE,'sample_reason':'predefined constant/dynamic dev/held task IDs before inspecting results; not successful-case selection','raw_bank_root':str(raw.resolve()),'raw_members':len(rawmanifest),'raw_bytes':sum(f.stat().st_size for f in raw.rglob('*') if f.is_file()),'R2_parent_inputs':'Original CORE ZIP and hash list preserved outside this new core; no duplicate costly bank','verifier':'All 432 source endpoint rows; 16 full forecast/likelihood traces x50 events; full raw SHA manifest retained. Evaluator and verifier do not import inference/generator.'}
    (CORE/'PACKAGE_PROVENANCE.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (CORE/'REPRODUCE.md').write_text('''# 核验与复现\n\n优先读 PRO_FIRST_READ_zh.md、R3_MECHANISM_REPORT.md、R4_MECHANISM_GO_NOGO.md。\n\n独立审计：`python verify_bundle.py <解压后的CORE目录>`。依赖 Python、NumPy、SciPy；不需要ROS/GADEN、不启动物理或训练。核验全部包内SHA、全部432个源位置/概率端点、16份完整候选预测的800事件正确删失似然。剩余完整原始预测由RAW_BANK_SHA256.json索引，可选RAW压缩包包含。\n\n数值实验源码在SOURCE_CODE。原执行布局为 `<workspace>/work/r4_*.py` 和 `<workspace>/outputs/PMFS_R3_R5_CONTINUOUS_20261011/`。重新执行属于新计算，不能覆盖这份冻结记录；独立新目录准备原始授权与R4_PREREGISTRATION_REV1.json及sha、资格测试后运行 r4_campaign.py。全部参数不再自动搜索。原 r4_freeze.py 产生初版种子；操作合同为REV1，使用252个不重合RNG流。初版与碰撞修复证据均保留。\n\nR3依赖原冻结 R2 CORE；其路径和SHA见ALL_INPUT_SHA256.json。SOURCE_CODE/r3_readonly_executed.py是生成R3时实际执行版本；r3_readonly.py另外增加整份附件数值断言，未重运行物理数据。\n\n没有执行新原生PMFS导航、CFD/GADEN、GPU训练或真实湖岸验证；不得把数值B0/B1/B2命名或辅助Top5当官方原生指标。\n''',encoding='utf-8')
    manifest={str(f.relative_to(CORE)).replace('\\','/'):sha(f) for f in sorted(CORE.rglob('*')) if f.is_file()}
    (CORE/'MANIFEST_SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    result=subprocess.run([sys.executable,'-B','-X','utf8',str(CORE/'verify_bundle.py'),str(CORE)],capture_output=True,text=True,encoding='utf-8')
    (OUT/'INDEPENDENT_BUNDLE_VERIFY.stdout.log').write_text(result.stdout,encoding='utf-8');(OUT/'INDEPENDENT_BUNDLE_VERIFY.stderr.log').write_text(result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError(result.stderr)
    verification=json.loads(result.stdout);(OUT/'INDEPENDENT_VERIFICATION.json').write_text(json.dumps(verification,indent=2)+'\n',encoding='utf-8')
    # Verification receipt added with its own manifest entry; no self-hashing cycle.
    shutil.copy2(OUT/'INDEPENDENT_VERIFICATION.json',CORE/'INDEPENDENT_VERIFICATION.json');manifest['INDEPENDENT_VERIFICATION.json']=sha(CORE/'INDEPENDENT_VERIFICATION.json');(CORE/'MANIFEST_SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    archive=CORE.with_suffix('.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f in sorted(CORE.rglob('*')):
            if f.is_file():z.write(f,str(f.relative_to(CORE)))
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    if archive.stat().st_size>=30*2**20:raise RuntimeError('CORE >30MiB; preserve generated artifact, need split without dropping evidence')
    rawzip=BASE/'outputs/PMFS_R3_R5_CONTINUOUS_20261011_RAW.zip'
    with zipfile.ZipFile(rawzip,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for f in sorted(raw.rglob('*')):
            if f.is_file():z.write(f,str(f.relative_to(OUT)))
        z.write(OUT/'RAW_BANK_SHA256.json','RAW_BANK_SHA256.json')
    with zipfile.ZipFile(rawzip) as z:assert z.testzip() is None
    receipts={'CORE':{'path':str(archive.resolve()),'bytes':archive.stat().st_size,'sha256':sha(archive)},'RAW':{'path':str(rawzip.resolve()),'bytes':rawzip.stat().st_size,'sha256':sha(rawzip)},'independent_verification':verification}
    (OUT/'PACKAGE_RECEIPT.json').write_text(json.dumps(receipts,indent=2)+'\n',encoding='utf-8')
    for p in [archive,rawzip]:p.with_suffix('.zip.sha256').write_text(sha(p)+'  '+p.name+'\n',encoding='ascii')
    print(json.dumps(receipts,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
