"""Package only new RK2 evidence; old RK1 is referenced by SHA, never copied."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,shutil,zipfile,time

BASE=Path(__file__).resolve().parents[2];WORK=Path(__file__).resolve().parent
RUN=BASE/'outputs/PMFS_RK2_FINITE_RESPONSE_PROTOTYPE_20261010_REPAIR1'
OUT=BASE/'outputs/PMFS_RK2_PROTOTYPE_REVIEW_BUNDLE_20261010'
start=time.perf_counter();assert not OUT.exists();OUT.mkdir()
def copyfile(src,dest):dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
def tree(src,dest):
    for p in src.rglob('*'):
        if p.is_file():copyfile(p,dest/p.relative_to(src))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):(OUT/n).write_text(v,encoding='utf-8')
tree(RUN,OUT/'RK2_NEW')
tree(BASE/'outputs/PMFS_RK2_FINITE_RESPONSE_PROTOTYPE_20261010',OUT/'FIRST_NUMERICAL_ATTEMPT_FROZEN')
tree(WORK/'pro_handoff',OUT/'PRO_RK1_REVIEW_FROZEN')
tree(WORK/'final_reports',OUT)
copyfile(Path('C:/Users/50176/Downloads/RK1_独立审核与有限原型任务书_210b94e.zip'),OUT/'PRO_RK1_ORIGINAL_HANDOFF.zip')
for name in ('independent_rk2_validation','independent_rk2_validation_full','independent_rk2_saved_only_validation','isolated_infer_process_validation','isolated_infer_process_validation_v2'):
    tree(WORK/name,OUT/'INDEPENDENT_REVIEW'/name)
for name in ('INDEPENDENT_RK2_NUMERICAL_REVIEW_zh.md','INFER_PROCESS_AUDIT_zh.md','FINAL_SCIENTIFIC_REPORT_REVIEW_zh.md','SAVED_ONLY_VERIFICATION_SCOPE_zh.md','PRO_ADDENDUM_INDEPENDENT_REVIEW_zh.md','PRO_ADDENDUM_INDEPENDENT_REVIEW.json','PRO_ADDENDUM_RECOMPUTED_BLOCK_DIRECTIONS.csv','PRO_ADDENDUM_RECOMPUTED_METRICS.csv'):
    copyfile(WORK/name,OUT/'INDEPENDENT_REVIEW'/name)
for name in ('B_PROSPECTIVE_GEOMETRY_ONLY_PLAN_zh.md','B_PROSPECTIVE_GEOMETRY_ONLY_PLAN.json','B_GEOMETRY_ELIGIBILITY_AUDIT.csv','design_b_geometry_only.py'):
    copyfile(WORK/name,OUT/'B_DESIGN_ONLY'/name)
for name in ('verify_rk2.py','verify_rk2_saved_only.py','audit_infer_process.py','recheck_pro_addendum.py'):
    copyfile(WORK/name,OUT/'verification'/name)
copyfile(WORK/'verify_bundle.py',OUT/'verify_bundle.py')
for name in ('prepare_rk2.py','freeze_rk2.py','prepare_one_numerical_repair.py','build_rk2_reports.py','package_rk2.py','record_final_software_qa.py','test_rk2_models.py','MODEL_SOFTWARE_QA.json','fresh_validate_rk2.py'):
    copyfile(WORK/name,OUT/'workflow_source'/name)
parent=BASE/'outputs/PMFS_RK1_PRO_REVIEW_BUNDLE_20261010'
parent_zip=BASE/'outputs/PMFS_RK1_PRO_REVIEW_BUNDLE_20261010_REVIEW.zip'
refs=dict(parent_commit='210b94e5de0ab7e906136fd0765c3639f10103b2',
    RK1_root_manifest_SHA256=sha(parent/'SHA256SUMS.json'),RK1_ZIP_SHA256=sha(parent_zip),RK1_ZIP_bytes=parent_zip.stat().st_size,
    RK1_ZIP_name=parent_zip.name,RK1_root_directory_name=parent.name,
    parent_local_path=str(parent),parent_repository_relative_path='research/pmfs_reproduction/PMFS_RK1_MATCHED_SUPPORT_CROSSFIT_20261010',
    repository='https://github.com/kris-yun/uav-gsl-isj',PRO_handoff_ZIP_SHA256=sha(OUT/'PRO_RK1_ORIGINAL_HANDOFF.zip'),
    old_evidence_copied_into_new_bundle=False,selected_parent_input_count=642,
    contract_reference_note='Frozen run uses original local parent path; verification accepts the user-supplied extracted old bundle path.')
assert refs['RK1_root_manifest_SHA256']=='b310b6c7d13112660ccd1bdd0cd4fbbb8f708ceb53e02bec4f03126d12575534'
assert refs['RK1_ZIP_SHA256']=='c56daec4117cedf2503c8467402e78a852cc3d0f3bdca753830838a91b78c979'
write('PARENT_REFERENCE.json',json.dumps(refs,ensure_ascii=False,indent=2)+'\n')
write('.gitattributes','* -text\n')
write('START_HERE_zh.md','''# RK2-A新增结果审核包

**开发门PASS，收益小；B没有执行。**

先读 `SEND_TO_PRO_zh.txt` 和 `RK2_FINITE_PROTOTYPE_REPORT_zh.md`。源NLL约改善1.10%/1.22%，Top1均4/4，O03相对U有退化；L恢复F的二值候选读出，没有超越完整物理。原始结果、失败和回退全部保留。

- `RK2_NEW/`：完整一次修复后运行、模型、实际候选预测、冻结标量观测、原始表/日志。
- `FIRST_NUMERICAL_ATTEMPT_FROZEN/`：测试前KKT停止的第一次运行及原始源码，未覆盖。
- `INDEPENDENT_REVIEW/`：独立矩阵与源评分复核、实际源盲进程审计及审计初始化失败记录。
- `B_DESIGN_ONLY/`：只读几何设计和12份待批方案，生成数0。
- `PRO_RK1_REVIEW_FROZEN/`：用户Pro本次任务书原件。
- `verification/`：独立只读数值验证器，不导入原型、不拟合或生成物理。
- `workflow_source/`：准备、冻结、唯一数值修复、报告与打包代码。

旧RK1原始物理库没有再次复制。父ZIP与根清单SHA见 `PARENT_REFERENCE.json`。本新包可以自包含复算最终代数/分数；原始输入血统重验仍需旧RK1包。

仅本包（Python3+NumPy，psutil可选；输出目录须不存在）：

```text
python -B verify_bundle.py --root . --out ../rk2_saved_check
```

加旧父包复算196缓存路由/矩阵/先验及642外部SHA：

```text
python -B verify_bundle.py --root . --parent <旧RK1包解压目录> --out ../rk2_full_check
```

验证只读包文件；跨平台表格按数值容差比较，字节SHA仍严格。上面入口检查记录的源盲进程证据，不重新执行隔离审计。可选实际独立推断重验（只推断已有标量输入，不调用物理或训练，Windows本地运行库依赖可能不同）：

```text
python -B verification/audit_infer_process.py --package RK2_NEW --out ../rk2_infer_check
```

不要运行 `RK2_NEW/source/run_rk2.py` 来审核现有结果；它会重新拟合，超出本次一次A范围。没有正式闭环新结果或新独立物理任务；本包不是发表用的主创新确认。
''')
files={p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*')) if p.is_file()}
write('SHA256SUMS.json',json.dumps(files,ensure_ascii=False,indent=2)+'\n')
z=OUT.with_name(OUT.name+'_REVIEW.zip');assert not z.exists()
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as f:
    for p in sorted(OUT.rglob('*')):
        if p.is_file():f.write(p,p.relative_to(OUT).as_posix())
with zipfile.ZipFile(z) as f:assert f.testzip() is None
record=dict(status='PASS_CREATED_NEW_ONLY_RK2_REVIEW_BUNDLE',path=str(OUT),ZIP_path=str(z),ZIP_SHA256=sha(z),ZIP_bytes=z.stat().st_size,
    root_manifest_SHA256=sha(OUT/'SHA256SUMS.json'),manifest_members=len(files),ZIP_members=len(files)+1,
    total_uncompressed_bytes=sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),packaging_wall_s=time.perf_counter()-start,
    parent_inputs_not_duplicated=True,model_fits=0,new_physics=0)
(BASE/'outputs/PMFS_RK2_PACKAGE_CREATION_RECORD.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,ensure_ascii=False,indent=2))
