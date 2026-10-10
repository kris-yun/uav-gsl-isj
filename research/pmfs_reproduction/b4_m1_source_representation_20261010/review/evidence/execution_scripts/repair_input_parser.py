"""Repair a pre-forward loader fault only; preserve old failure and native kernel."""
import sys
sys.dont_write_bytecode=True
import base64,hashlib,json
from pathlib import Path
from remote_local import run
W=Path(__file__).resolve().parent;R=W.parents[1];O=R/'outputs/PMFS_B4_M1_SOURCE_REPRESENTATION_20261010'
entry=(W/'m1_candidate_forward.cpp').read_bytes()
function=entry.decode().split('double checkedDouble',1)[1].split('class CandidateDiagnostic',1)[0]
probe='#include <map>\n#include <string>\n#include <stdexcept>\n#include <cmath>\n#include <cerrno>\n#include <cstdlib>\n#include <iostream>\nusing Row=std::map<std::string,std::string>;\ndouble checkedDouble'+function+'''
int main(){
 for(auto s:{"3.1908919011361254e-312","4.4673415696965513e-319"}) {
  bool failed=false;try{std::stod(s);}catch(const std::out_of_range&){failed=true;}
  if(!failed)return 2;
  std::cout<<s<<","<<std::hexfloat<<checkedDouble(Row{{"x",s}},"x")<<"\\n";
 }
 for(auto s:{"","nan","inf","1.2garbage"}) {
  bool rejected=false;try{checkedDouble(Row{{"x",s}},"x");}catch(const std::runtime_error&){rejected=true;}
  if(!rejected)return 3;
 }
}
'''
code='''from pathlib import Path
import base64,hashlib,json,os,signal,subprocess,time
t=Path('/home/zyc/pmfs_b4_m1_representation_20261010');r4=Path('/home/zyc/pmfs_native_capture_r4_20261009')
assert not (t/'forward_calls/anchor_T_coarse').exists()
ledger=json.loads((t/'forward_calls/EXECUTION_LEDGER.json').read_text());assert ledger['attempted_calls']==1 and ledger['completed_calls']==0
archive=t/'entry_before_subnormal_parser_fix';archive.mkdir()
old=(t/'m1_candidate_forward.cpp').read_bytes()
for name in ['m1_candidate_forward.cpp','m1_candidate_forward','BUILD_COMMANDS.json','BUILD_RESULT.json','build.log']:(t/name).rename(archive/name)
before=json.loads((archive/'BUILD_RESULT.json').read_text())
(t/'m1_candidate_forward.cpp').write_bytes(base64.b64decode(@@ENTRY@@))
(t/'numeric_parser_probe.cpp').write_bytes(base64.b64decode(@@PROBE@@))
context=json.loads((r4/'BUILD_CONTEXT.json').read_text())
commands=[['/usr/bin/c++','-std=c++20',str(t/'numeric_parser_probe.cpp'),'-o',str(t/'numeric_parser_probe')],
 ['/usr/bin/c++',*context['compileflags'],'-c',str(t/'m1_candidate_forward.cpp'),'-o',str(t/'m1_entry_fixed.o')],
 ['/usr/bin/c++','-fopenmp','-fsanitize=undefined','-Wl,--gc-sections',str(t/'m1_entry_fixed.o'),str(t/'Simulations_native.o'),
  *[str(r4/(n+'.o')) for n in ['Math_accessors','NQAQuadtree','PMFSLib']],'-o',str(t/'m1_candidate_forward'),*context['link_tail']]]
start=time.monotonic();peak=0;exitcodes=[]
with (t/'build.log').open('w') as log:
 for cmd in commands:
  p=subprocess.Popen(cmd,stdout=log,stderr=log,start_new_session=True)
  while p.poll() is None:
   rss=0
   for d in Path('/proc').iterdir():
    if not d.name.isdigit():continue
    try:
     if os.getpgid(int(d.name))!=p.pid:continue
     for line in (d/'status').read_text().splitlines():
      if line.startswith('VmRSS:'):rss+=int(line.split()[1])*1024
    except (ProcessLookupError,PermissionError,FileNotFoundError):pass
   peak=max(peak,rss)
   if before['cumulative_build_wall_seconds']+time.monotonic()-start>180 or rss>1610612736:
    os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=3);raise RuntimeError('compile resource cap')
   time.sleep(.1)
  exitcodes.append(p.returncode);assert p.returncode==0,(t/'build.log').read_text()
probe=subprocess.run([str(t/'numeric_parser_probe')],capture_output=True,text=True,check=True)
(t/'NUMERIC_PARSER_PROBE.stdout').write_text(probe.stdout)
result=dict(verdict='PASS_ISOLATED_SUBNORMAL_INPUT_PARSER_REPAIR_ZERO_FORWARD_CALLS',
 input_subnormal_examples=['3.1908919011361254e-312','4.4673415696965513e-319'],probe_stdout=probe.stdout,
 original_failure='std::stod range_error while loading input omega; before simulation construction and output creation',
 input_data_modified=False,native_kernel_modified=False,RNG_or_parameters_modified=False,
 original_entry_sha256=hashlib.sha256(old).hexdigest(),new_entry_sha256=hashlib.sha256((t/'m1_candidate_forward.cpp').read_bytes()).hexdigest(),
 original_executable_sha256=before['executable_sha256'],executable_sha256=hashlib.sha256((t/'m1_candidate_forward').read_bytes()).hexdigest(),
 build_wall_seconds=time.monotonic()-start,cumulative_build_wall_seconds=before['cumulative_build_wall_seconds']+time.monotonic()-start,
 maximum_RSS_bytes=max(peak,before['maximum_RSS_bytes']),exit_codes=exitcodes,
 failed_initialization_launches=1,actual_forward_calls_before_repair=0,budget_forward_calls_remain=6)
(t/'INPUT_PARSER_REPAIR.json').write_text(json.dumps(result,indent=2));(t/'BUILD_COMMANDS.json').write_text(json.dumps(commands,indent=2))
print(json.dumps(result,indent=2))
'''.replace('@@ENTRY@@',repr(base64.b64encode(entry).decode())).replace('@@PROBE@@',repr(base64.b64encode(probe.encode()).decode()))
compile(code,'parser_repair','exec')
result=json.loads(run(code,'SUBNORMAL_INPUT_PARSER_REPAIR',180))
for line in result['probe_stdout'].splitlines():
    decimal,hexadecimal=line.split(',');assert float(decimal).hex()==float.fromhex(hexadecimal).hex()
result['Python_double_bit_value_crosscheck']='PASS_EXACT'
(O/'INPUT_PARSER_REPAIR.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(W/'numeric_parser_probe.cpp').write_text(probe,encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
