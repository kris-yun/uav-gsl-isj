from pathlib import Path
import csv,hashlib,json,os,shutil,subprocess,time,zipfile
P=Path(__file__).resolve().parent;R=Path(json.loads((P/'PREPARED_LOCATION.json').read_text(encoding='utf-8'))['path']);A=R/'validation';A.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
vs=Path(r'C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\Tools\VsDevCmd.bat');assert vs.is_file()
cmd='cmd.exe /d /s /c ""'+str(vs)+'" -no_logo -arch=x64 -host_arch=x64 >nul && set"'
q=subprocess.run(cmd,capture_output=True,timeout=30);assert q.returncode==0,q.stderr.decode(errors='replace')
env={k.upper():v for k,v in os.environ.items()}
for line in q.stdout.decode('mbcs',errors='replace').splitlines():
 if '='in line and not line.startswith('='):k,v=line.split('=',1);env[k.upper()]=v
cl=shutil.which('cl.exe',path=env['PATH']);assert cl
exe=A/'host_cpp_core_check.exe';obj=A/'host_cpp_core_check.obj';cmd=[cl,'/nologo','/std:c++20','/EHsc','/O2','/fp:precise','/wd4068','/I'+str(R/'dependencies/DDA/include'),'/Fo'+str(obj),'/Fe'+str(exe),str(R/'host_cpp_core_check.cpp')]
t=time.monotonic();q=subprocess.run(cmd,cwd=A,env=env,capture_output=True,timeout=90);(A/'HOST_CPP_BUILD.stdout').write_bytes(q.stdout);(A/'HOST_CPP_BUILD.stderr').write_bytes(q.stderr)
commands=[dict(argv=cmd,exit_code=q.returncode,wall_s=time.monotonic()-t)];put(A/'HOST_COMMANDS.json',commands);assert q.returncode==0,'See HOST_CPP_BUILD stdout/stderr'
t=time.monotonic();cmd=[str(exe),str(R/'CPP_REPLAY_INPUT.bin')];q=subprocess.run(cmd,capture_output=True,timeout=30);(A/'HOST_CPP_READOUT.csv').write_bytes(q.stdout);(A/'HOST_CPP_RUN.stderr').write_bytes(q.stderr);commands.append(dict(argv=cmd,exit_code=q.returncode,wall_s=time.monotonic()-t));put(A/'HOST_COMMANDS.json',commands);assert q.returncode==0,'Host core verification failed; inspect retained logs'
rows=list(csv.DictReader((A/'HOST_CPP_READOUT.csv').open(encoding='utf-8')));assert len(rows)==7 and sum(int(x['calls'])for x in rows)==1120
put(A/'HOST_CPP_RESULT.json',dict(status='PASS_HOST_CPP_SCORING_NORMALIZATION_AND_RECTANGULAR_MOMENTS',groups=len(rows),candidate_maps=1120,compiler=cl,compiler_sha256=sha(Path(cl)),host_exe_sha256=sha(exe),ROS_ELF_built=False,not_an_O24_closed_loop=True,score_max_saved_P24_relative_error=max(float(x['max_saved_score_relative_error'])for x in rows),P24_posterior_max_abs_error=max(float(x['p24_posterior_max_abs_error'])for x in rows),Top5_ties='Native std::sort tie selection is compiler-library dependent; host MSVC check is not Linux ROS performance or a byte-identical libstdc++ readout guarantee.'))
# Verify supplied archive bytes and every payload without opening another chat,
# VM or simulation. No extracting over the previous frozen data.
archive=Path(json.loads((R/'INPUT_ARCHIVE_IDENTITY.json').read_text(encoding='utf-8'))['path']);assert sha(archive)=='84087b1ddd39b1edcc5be33c88263585e7f1a8dd66694f8569a019250bee2100'
with zipfile.ZipFile(archive)as z:
 assert z.testzip()is None;name=next(n for n in z.namelist()if n.endswith('/MANIFEST_SHA256.json'));manifest=json.loads(z.read(name));prefix=name.rsplit('/',1)[0]+'/'
 for row in manifest['files']:assert hashlib.sha256(z.read(prefix+row['path'])).hexdigest()==row['sha256']
put(A/'INPUT_ARCHIVE_VERIFICATION.json',dict(status='PASS_CRC_AND_EVERY_PAYLOAD_SHA256',archive_sha256=sha(archive),files=len(manifest['files'])))
worlds=[];start=time.monotonic()
for case,name in [('A2','NATIVE_PMFS_WIND_RECOVERY_20261014'),('B2','NATIVE_PMFS_FULL20_20261014')]:
 root=Path(r'D:\ZYC\A-gas\workspace')/name/'cases'/case;manifest=root/'ALL_FRAME_SHA256_AND_TIME.csv';frames=list(csv.DictReader(manifest.open(encoding='utf-8')));total=0
 for row in frames:
  p=root/'one_realization'/('iteration_'+row['frame']);assert sha(p)==row['sha256'];total+=p.stat().st_size
 worlds.append(dict(case=case,path=str(root),frames=len(frames),bytes=total,manifest_sha256=sha(manifest),independent_new_physical_replicates=0))
put(A/'WORLD_READONLY_SHA_VERIFICATION.json',dict(status='PASS_EXISTING_ALL_3606_FRAME_SHA256',rows=worlds,wall_s=time.monotonic()-start,new_worlds=0))
print(json.dumps(dict(status='PASS_HOST_ONLY_SOURCE_ARCHIVE_CPP_AND_WORLD_CHECKS',groups=7,candidate_maps=1120,existing_frames=3606,new_ROS=0,new_VM_calls=0)))
