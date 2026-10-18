from pathlib import Path
import json,hashlib,re
E=Path(__file__).resolve().parent;BASE=E.parent
P=BASE/'FSR_S2_NATIVE_PMFS_SINGLE_V1_20261017/public_release_origin_D2/AUTHOR_20240918_FIX.patch'
OLD=BASE/'FSR_S2_PMFS_EQ6_INPUT_INVENTORY_20261017'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):
 with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2)
text=P.read_text();targets=re.findall(r'^diff --git a/(.*?) b/(.*?)$',text,re.M);assert len(targets)==1 and targets[0][0].endswith('/Math.cpp');hunks=re.findall(r'^@@.*@@.*$',text,re.M);assert len(hunks)==2
manifest=json.loads((OLD/'FILES_MANIFEST.json').read_text());assert all(sha(OLD/x['path'])==x['sha256'] for x in manifest['files'])
correction=dict(kind='APPENDED_EVIDENCE_LABEL_CORRECTION_NO_SOURCE_CHANGE',patch=dict(path=str(P),bytes=P.stat().st_size,sha256=sha(P),actual_diff_target_files=[x[0] for x in targets],actual_hunks=hunks),incorrect_prior_description='Whole author commit diff contains Grid2D/RNG/rotation changes',correct_description='Stored Math.cpp-only excerpt from author commit a8d5a764, containing RNG normalization and Gaussian rotation-sign hunks. It does not contain Grid2D diff and is not a complete commit patch.',affected_prior_artifacts=[str(OLD/'RECTANGULAR_GRID_SOURCE_ENTRIES.json'),str(OLD/'既有A2B2资产交接_zh.md'),str(OLD/'inventory_existing_inputs.py'),str(OLD/'finish_handoff.py')],original_artifacts_preserved=True,old_inventory_manifest_sha256=sha(OLD/'FILES_MANIFEST.json'),old_inventory_13_files_still_exact=True,scientific_tests_or_results_changed=False,September_grid_source_identity_remains='e00ae6a9329c405b68f6c2ad00f8a0aadbc7f97b2cc50457f20cdf55efb9ca3d; official Git blob9614081d712d4562f01e369acd841c433705f67b',full_S2_or_B2_additional_trace_started=False)
put(E/'PATCH_SCOPE_CORRECTION.json',correction)
(E/'交接补丁范围更正_zh.md').write_text('''# 交接更正：作者修复补丁是Math.cpp片段

此前既有A2/B2资产交接把AUTHOR_20240918_FIX.patch称作完整提交补丁，并称其中包含网格修改。这一描述不准确。

实际1730字节文件只有Math.cpp一个目标、两个hunk：Gaussian旋转符号和uniform随机数归一化。它带有作者a8d5a764提交标题，不等于收录该提交所有文件差异。不能从这个片段恢复Grid2D修改，也不能把它当成Eq6单行补丁。

September Grid2D.hpp原样文件的独立SHA/Git OID核验仍有效，Eq6单因素补丁和数值结果不受影响。旧13文件清单及源文件保留原样，本目录追加更正，不覆盖历史。本轮不继续新的B2支持域追查、不运行模拟或ROS。
''',encoding='utf-8',newline='\n')
put(E/'FILES_MANIFEST.json',dict(files=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in E.iterdir() if p.is_file()]))
print(json.dumps(dict(actual_targets=correction['patch']['actual_diff_target_files'],hunks=len(hunks),old_files_exact=True,no_scientific_result_change=True)))
