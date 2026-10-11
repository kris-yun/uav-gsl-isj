from common_n import *
import zipfile,shutil,subprocess,csv,os
archive=BASE/'outputs/PMFS_NATIVE_MECHANISM_CLOSURE_R1_20261011_REVIEW.zip';assert not archive.exists()
review=WORK/'portable_zip_review';assert not review.exists() or not any(review.iterdir());review.mkdir(exist_ok=True)
readme='''# PMFS原生机制闭合R1审核包

先读CORE/00_READ_FIRST_FOR_PRO_zh.md，再读MECHANISM_CLOSURE_REPORT_zh.md。主原生结果以QUALIFIED_*为准，初始化修正前影子结果只作技术留档。所有反例和新6份端点都保留。

本包包含全部主要候选图、后验、查询数值、参数及原始快照样本；不包含完整气体银行，覆盖边界见RAW_COVERAGE_AND_REPLAY_LIMITS_zh.md。完整银行本地冻结并有逐帧SHA/time索引。

仅执行只读复核：python PMFS_NATIVE_MECHANISM_CLOSURE_R1_20261011_CORE/source/portable/verify_native_mechanism_bundle.py 解压根目录。需要NumPy。不启动ROS、GADEN或前向仿真。
'''
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,strict_timestamps=False) as z:
 z.writestr('README_zh.md',readme)
 for folder in [CORE,RAW]:
  for p in sorted(folder.rglob('*')):
   if p.is_file():z.write(p,folder.name+'/'+p.relative_to(folder).as_posix())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None;z.extractall(review)
check=review/CORE.name/'source/portable/verify_native_mechanism_bundle.py'
p=subprocess.run([sys.executable,'-B','-X','utf8',str(check),str(review)],capture_output=True,text=True,timeout=240)
(WORK/'zip_review.stdout').write_text(p.stdout,encoding='utf-8');(WORK/'zip_review.stderr').write_text(p.stderr,encoding='utf-8')
assert p.returncode==0,p.stderr
result=json.loads(p.stdout);assert result['status'].startswith('PASS')
result['ZIP_integrity']='PASS_ALL_MEMBERS_CRC';result['actual_run']='Freshly extracted directory; only packaged files and NumPy used; no VM/source producer imports'
dump(review/'PORTABLE_VERIFICATION_RESULT.json',result)
with zipfile.ZipFile(archive,'a',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.write(review/'PORTABLE_VERIFICATION_RESULT.json','PORTABLE_VERIFICATION_RESULT.json')
with zipfile.ZipFile(archive) as z:assert z.testzip() is None;members=len(z.infolist())
metadata=dict(status='PASS_EXTRACTED_PORTABLE_REVIEW',zip=archive.as_posix(),SHA256=sha(archive),bytes=archive.stat().st_size,members=members,verification=result,task_elapsed_s=time.time()-load(WORK/'ENTRY_TIME.json')['start_unix'])
dump(BASE/'outputs/PMFS_NATIVE_MECHANISM_CLOSURE_R1_20261011_REVIEW_SHA256.json',metadata)
(archive.with_suffix('.zip.sha256')).write_text(metadata['SHA256']+'  '+archive.name+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in metadata.items() if k!='verification'},ensure_ascii=False))
