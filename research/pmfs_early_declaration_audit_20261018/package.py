from pathlib import Path
import hashlib,json,shutil,subprocess,zipfile
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
dest=Path(r'C:\Users\50176\Downloads\PMFS_提前错误声明_时钟与B2核清_四回合原始证据_20261018_复核版.zip')
assert not dest.exists(),'Never overwrite an earlier delivery'
guest_binary=R/'install/lib/gsl_server/gsl_actionserver_node';(R/'binaries').mkdir(exist_ok=True);shutil.copyfile(guest_binary,R/'binaries/gsl_actionserver_node')
readme='''# PMFS 提前错误声明审计

先读 `核查结论_zh.md`，结果为性能复现HOLD，AIMMD暂停。

保存四次真实ROS闭环、1,120次实际前向候选图、28组固定历史公式控制、原生C++读出、时钟与B2地图独立核验。所有负结果均保留。

仅校验：`python reproduce.py --verify-only`

离线复算：`python reproduce.py --out /tmp/pmfs_early_audit_replay_01`

离线复算需要Python+NumPy与Linux g++/C++20，自动在新输出目录解开所附旧基线；不会启动ROS、气体世界或AIMMD。五个核心结果表必须逐字节一致。原始完整ROS复跑仍需要本机已有世界与安装，包中没有所有世界帧，也不把这些帧当算法免费参考库。

`FORMULA_CONTROLS_NATIVE_CPP_READOUT.csv`是权威Top5/方差读出；NumPy控制表另留用于评分/概率核查。
'''
(R/'README.md').write_text(readme,encoding='utf-8')
exclude={'build','install','QA_REPLAY','PACKAGE_CONTENTS','__pycache__'}
files=[p for p in sorted(R.rglob('*'))if p.is_file()and not any(part in exclude for part in p.relative_to(R).parts)and p.name not in ['MANIFEST_SHA256.json','PACKAGE_RESULT.json']]
manifest=dict(status='FROZEN_DELIVERY_INPUTS',files=[dict(path=p.relative_to(R).as_posix(),size=p.stat().st_size,sha256=sha(p))for p in files])
(R/'MANIFEST_SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for p in files+[R/'MANIFEST_SHA256.json']:z.write(p,arcname=R.name+'/'+p.relative_to(R).as_posix())
with zipfile.ZipFile(dest)as z:
 assert z.testzip()is None
 for row in manifest['files']:assert hashlib.sha256(z.read(R.name+'/'+row['path'])).hexdigest()==row['sha256']
receipt=dict(status='PASS_ZIP_CRC_AND_ALL_PAYLOAD_SHA256',path=str(dest),size_bytes=dest.stat().st_size,sha256=sha(dest),payload_files=len(files),manifest_sha256=sha(R/'MANIFEST_SHA256.json'))
(R/'PACKAGE_RESULT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');dest.with_suffix('.verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False))
