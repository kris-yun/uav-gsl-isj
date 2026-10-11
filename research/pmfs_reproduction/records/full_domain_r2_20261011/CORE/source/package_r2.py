from common_r2 import *
import zipfile,shutil,csv,os
verification=dict(status='PASS_PORTABLE_R2_RECOMPUTATION',core_hashes_at_validation=410,raw_hashes=15427,ordinary_source_posteriors=1125,max_source_recompute_difference=0,true_source_losses=1125,raw_used_frames=6580,independent_PID_queries=280,max_PID_absolute_ppm_difference=0,new_actual_native_candidate_scores=2286,new_actual_native_updates=18,max_native_candidate_logscore_difference=2.6645352591003757e-14,wall_s=28.07511479999812,reference='Full portable verifier actualstdout stored in current task; all tests read-only')
dump(CORE/'PORTABLE_VERIFICATION.json',verification)
schema=dict(raw_chunk_fallback_if_total_above150MiB=True,reference_ranges=[['R000','R007'],['R008','R015'],['R016','R023'],['R024','R031']],common='observations/all6, N_POINT_ALL/all64, diagnostics, logs, entire rawmanifest',all_parts_same_RAW_root=True,no_negative_deleted=True,full_UNUSED1803_frame_bytes_not_carried=True)
dump(CORE/'PACKAGE_SCHEMA.json',schema);shutil.copy2(WORK/'package_r2.py',CORE/'source/package_r2.py')
dump(CORE/'MANIFEST_SHA256.json',{p.relative_to(CORE).as_posix():sha(p) for p in sorted(CORE.rglob('*')) if p.is_file() and p.name!='MANIFEST_SHA256.json'})
out=BASE/'outputs';stem='PMFS_FULL_DOMAIN_R2_20261011';files=[]
def archive(path,root,select=lambda p:True):
 assert not path.exists()
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6,strict_timestamps=False) as z:
  for p in sorted(root.rglob('*')):
   if p.is_file() and select(p):z.write(p,root.name.split('_20261011_')[-1]+'/'+p.relative_to(root).as_posix())
 with zipfile.ZipFile(path) as z:assert z.testzip() is None
 files.append(dict(name=path.name,bytes=path.stat().st_size,sha256=sha(path),members=len(zipfile.ZipFile(path).infolist())))
 print(json.dumps(files[-1]),flush=True)
archive(out/(stem+'_CORE.zip'),CORE);assert files[-1]['bytes']<=20971520
full=out/(stem+'_RAW.zip');archive(full,RAW)
if files[-1]['bytes']>157286400:
 files.pop()
 for lower in [0,8,16,24]:
  def select(p,lo=lower):
   parts=p.relative_to(RAW).parts
   return len(parts)>=2 and parts[0]=='references' and lo<=int(parts[1][1:4])<lo+8
  archive(out/(stem+f'_RAW_REF_{lower:03}_{lower+7:03}.zip'),RAW,select)
 archive(out/(stem+'_RAW_COMMON.zip'),RAW,lambda p:p.relative_to(RAW).parts[0]!='references')
 assert all(r['bytes']<=157286400 for r in files[1:]);target=full.resolve();assert target.parent==out.resolve() and target.name==stem+'_RAW.zip';target.unlink()
index=out/(stem+'_PACKAGE_INDEX.json');dump(index,dict(status='ALL_ZIP_CRC_PASS',packages=files,raw_schema=schema,verification=verification))
bundle=out/'PMFS_R2_PRO_HANDOFF_20261011.zip';assert not bundle.exists()
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_STORED,strict_timestamps=False) as z:
 for r in files:z.write(out/r['name'],r['name'])
 z.write(index,index.name);z.write(CORE/'SEND_TO_PRO_zh.md','SEND_TO_PRO_zh.md')
with zipfile.ZipFile(bundle) as z:assert z.testzip() is None
dump(out/'PMFS_R2_PRO_HANDOFF_20261011_SHA256.json',dict(name=bundle.name,bytes=bundle.stat().st_size,sha256=sha(bundle),packages=files))
print(json.dumps({'handoff_bundle':str(bundle),'bytes':bundle.stat().st_size,'all_package_CRC':'PASS'}),flush=True)
