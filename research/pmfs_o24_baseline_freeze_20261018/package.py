from pathlib import Path
import hashlib,json,shutil,subprocess,zipfile
P=Path(__file__).resolve().parent;R=Path(json.loads((P/'PREPARED_LOCATION.json').read_text(encoding='utf-8'))['path']);W=R.parents[1];rel=R.relative_to(W).as_posix()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):
 q=subprocess.run(['git','-C',str(W),*a],capture_output=True);assert q.returncode==0,q.stderr.decode(errors='replace');return q.stdout
assert git('branch','--show-current').decode().strip()=='codex/pmfs-o24-baseline-freeze-20261018'
README='''# PMFS-O24阶段0冻结包

先读`阶段0裁决_zh.md`。O24源码/预期参数已冻结；尚未编译O24ROS程序、尚无O24实际成绩。P24历史不能当O24成绩。用户合同要求另行批准才能真实运行。

本轮仅Windows本机C++和文件读取；没有连接VM、启动ROS/CFD/AIMMD、气体世界或其他会话。完整RNG状态/seed预锁尚未满足，上游随机源码未改。

校验：`python verify_manifest.py`。

Linux纯C++离线复算（不需要ROS）：

```sh
g++ -std=c++20 -O2 -Idependencies/DDA/include host_cpp_core_check.cpp -o core_check
./core_check CPP_REPLAY_INPUT.bin
```

上面只重算7组/1120张已保存P24候选响应，没有生成新气体或新路径，不是O24闭环。程序同时检验原生公式、归一化、矩形方差修复与旧P24响应一致性。Top5%的并列排序可随MSVC/libstdc++略变，见验证说明。

`upstream_readonly`是185份已校验所选作者文件；`o24_port_gmrf_source`是新的源码候选，含线性Omega而无P24公式补丁。`PHASE1_QUALIFICATION_PLAN.json`仅为待批准草案，不含自动运行器；模板路径为NOT_BUILT。
'''
(R/'README.md').write_text(README,encoding='utf-8')
verify='''from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parent
m=json.loads((r/'MANIFEST_SHA256.json').read_text(encoding='utf-8'))
for a in m['files']:
 p=r/a['path'];assert p.is_file()and hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256'],a['path']
print(json.dumps(dict(status='PASS_ALL_PAYLOAD_SHA256',files=len(m['files']))))
'''
(R/'verify_manifest.py').write_text(verify,encoding='utf-8',newline='\n')
shutil.copyfile(P/'package.py',R/'package.py')
files=[p for p in sorted(R.rglob('*'))if p.is_file()and p.name!='MANIFEST_SHA256.json'and p.suffix not in ['.obj']and '__pycache__'not in p.parts]
manifest=dict(status='STAGE0_FROZEN_PAYLOAD',files=[dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=sha(p))for p in files])
(R/'MANIFEST_SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
dest=Path(r'C:\Users\50176\Downloads\PMFS_O24_官方源码身份冻结_阶段0只读预检_20261018.zip');assert not dest.exists()
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for p in files+[R/'MANIFEST_SHA256.json']:z.write(p,R.name+'/'+p.relative_to(R).as_posix())
with zipfile.ZipFile(dest)as z:
 assert z.testzip()is None
 for x in manifest['files']:assert hashlib.sha256(z.read(R.name+'/'+x['path'])).hexdigest()==x['sha256']
receipt=dict(status='PASS_ALL_PAYLOAD_HASH_AND_ZIP_CRC',path=str(dest),bytes=dest.stat().st_size,sha256=sha(dest),files=len(files),new_VM=0,new_ROS=0,new_worlds=0,AIMMD=0,scope='Stage0only; no O24 ROSperformance')
(P/'PACKAGE_RESULT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');dest.with_suffix('.verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
attrs=W/'.gitattributes';old=attrs.read_bytes()if attrs.exists()else b'';line=('/'+rel+'/** -text\n').encode();assert line not in old;attrs.write_bytes(old+(b'\n'if old and not old.endswith(b'\n')else b'')+line)
spec=P/'paths.nul';entries=manifest['files']+[dict(path='MANIFEST_SHA256.json')];spec.write_bytes(b''.join((rel+'/'+x['path']).encode('utf-8')+b'\0'for x in entries)+b'.gitattributes\0')
git('add','-f','--pathspec-from-file='+str(spec),'--pathspec-file-nul')
index={}
for v in git('ls-files','--stage','-z','--',rel).split(b'\0'):
 if v:meta,path=v.split(b'\t',1);index[path.decode('utf-8')]=meta.split()[1].decode()
assert len(index)==len(entries)
for x in entries:
 data=(R/x['path']).read_bytes();assert index[rel+'/'+x['path']]==hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
git('commit','-m','Freeze source-faithful PMFS O24 identities and host-only preflight gates')
commit=git('rev-parse','HEAD').decode().strip();status=git('status','--porcelain').decode();assert not status.strip(),status
(P/'COMMIT_RESULT.json').write_text(json.dumps(dict(status='COMMITTED_LOCAL_INDEPENDENT_BRANCH_NOT_PUSHED',branch='codex/pmfs-o24-baseline-freeze-20261018',commit=commit,path=str(R),files=len(entries)),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(**receipt,git_commit=commit),ensure_ascii=False))
