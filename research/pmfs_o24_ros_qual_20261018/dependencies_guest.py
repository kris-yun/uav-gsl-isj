from pathlib import Path
import datetime,hashlib,json,psutil,re,subprocess
R=Path('/mnt/hgfs/workspace/PMFS_O24_ROS_QUAL_20261018');plan=json.loads((R/'PRECOMMIT.json').read_text());domains={str(x['domain'])for x in plan['roles']}
expected=[('/home/zyc/ros2_ws/pmfs_o24_port_gmrf_20261018/gsl_actionserver_node',json.loads((R/'BUILD_RESULT.json').read_text())['binary_sha256']),('/home/zyc/ros2_ws/pmfs_official_repro_audit_20261016/install_paper_gmrf_tfqualified_2024/lib/gmrf_wind_mapping/gmrf_wind_mapping_node','6882e2e60440c5d5cb600eed454d160ded227fbbc8ed3c55a7fcf9572ad4efe2'),('/home/zyc/ros2_ws/pmfs_official_repro_audit_20261016/public_clock_player','ca8989091885fe920957e977bf7efac382633c9b4862dc968e5ca4cfbed9d80c')]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
rows=[];libs={};live=[]
for p in psutil.process_iter(['pid','cmdline','exe']):
 try:
  if p.environ().get('ROS_DOMAIN_ID')in domains and p.info['exe']:
   exe=Path(p.info['exe']);live.append(dict(pid=p.pid,exe=str(exe),sha256=sha(exe),domain=p.environ().get('ROS_DOMAIN_ID'),command=p.info['cmdline']))
 except(psutil.NoSuchProcess,psutil.AccessDenied,FileNotFoundError):pass
for path,h in expected:
 assert sha(path)==h
 q=subprocess.run(['ldd',path],capture_output=True,text=True);rows.append(dict(path=path,sha256=h,ldd_exit_code=q.returncode,ldd_output=q.stdout+q.stderr))
 for name in re.findall(r'(?:=>\s+)?(/[^\s()]+)',q.stdout):
  p=Path(name)
  if p.is_file():libs[str(p.resolve())]=sha(p)
(R/'DEPENDENCY_LIVE_MANIFEST.json').write_text(json.dumps(dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='PASS_EXPECTED_ROOT_BINARIES_AND_RESOLVED_LIBRARIES_HASHED',roots=rows,libraries=libs,live_owned_processes=live,live_scope='Only current O24 domains inspected; historical episodes use same frozen launch and binary set. No replay determinism across system-library changes claimed.'),indent=2));print(json.dumps(dict(status='PASS',root_binaries=len(rows),resolved_libraries=len(libs),live_owned_processes=len(live))))
