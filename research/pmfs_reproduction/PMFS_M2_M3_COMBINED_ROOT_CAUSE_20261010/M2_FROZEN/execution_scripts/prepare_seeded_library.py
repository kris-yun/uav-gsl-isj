"""Compile an isolated native GADEN copy with auditable RNG initial states only."""
from common import *
import hashlib
code=r'''
import hashlib,shlex,subprocess,os,time,signal,shutil
original=Path('/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/src/gaden_common/third_party/gaden_core')
build=Path('/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/build/gaden_common/third_party/gaden_core')
obj=build/'CMakeFiles/gaden.dir'
pristine=original/'include/gaden/internal/MathUtils.hpp'
text=pristine.read_text();(t/'pristine_MathUtils.hpp').write_bytes(pristine.read_bytes())
addition=r"""
    // M2 isolated initialization and audit only: native distributions and calls retained.
    struct M2RandomStream {
        std::mt19937 engine;
        std::normal_distribution<> normal{0,1};
        std::uniform_real_distribution<float> uniform{0.f,1.f};
        uint64_t draws=0;
        int stream;
        M2RandomStream(int s):stream(s) {
            const char* value=std::getenv(s==0?"M2_GAUSSIAN_SEED":"M2_UNIFORM_SEED");
            if(value)engine.seed(static_cast<uint32_t>(std::stoull(value)));
            if(const char* root=std::getenv("M2_RNG_TRACE")) {
                std::ofstream f(std::string(root)+".stream"+std::to_string(s)+".initial.txt");
                f<<engine<<"\nnormal="<<normal<<"\nuniform="<<uniform<<"\ndraws="<<draws<<"\n";
            }
        }
        ~M2RandomStream() {
            if(const char* root=std::getenv("M2_RNG_TRACE")) {
                std::ofstream f(std::string(root)+".stream"+std::to_string(stream)+".final.txt");
                f<<engine<<"\nnormal="<<normal<<"\nuniform="<<uniform<<"\ndraws="<<draws<<"\n";
            }
        }
    };
    inline M2RandomStream& M2Stream(int s) {
        if(s==0){static thread_local M2RandomStream x(0);return x;}
        static thread_local M2RandomStream x(1);return x;
    }
"""
text=text.replace('#include <random>','#include <random>\n#include <fstream>\n#include <cstdlib>\n#include <iomanip>')
text=text.replace('    // thread-safe',addition+'\n    // thread-safe',1)
old="""        static thread_local std::mt19937 engine;
        static thread_local std::normal_distribution<> dist{0, 1};
        return mean + dist(engine) * stdDev;"""
new="""        auto& random=M2Stream(0);random.draws++;
        return mean + random.normal(random.engine) * stdDev;"""
assert text.count(old)==1;text=text.replace(old,new)
old="""        static thread_local std::mt19937 engine;
        static thread_local std::uniform_real_distribution<float> distribution{0.0, 1.0};
        return min + distribution(engine) * (max - min);"""
new="""        auto& random=M2Stream(1);random.draws++;
        return min + random.uniform(random.engine) * (max - min);"""
assert text.count(old)==1;text=text.replace(old,new)
old="""            for (size_t i = 0; i < Size; i++)
                m_precalculatedTable[i] = GaussianRandom(0, 1);"""
new=old+"""
            if(const char* root=std::getenv("M2_RNG_TRACE")) {
                std::ofstream f(std::string(root)+".cache"+std::to_string(Size)+".f32",std::ios::binary);
                f.write(reinterpret_cast<const char*>(m_precalculatedTable.data()),sizeof(float)*Size);
                std::ofstream index(std::string(root)+".cache"+std::to_string(Size)+".index.txt");index<<m_index;
            }"""
assert text.count(old)==1;text=text.replace(old,new)
dest=t/'include/gaden/internal/MathUtils.hpp';dest.parent.mkdir(parents=True);dest.write_text(text)
flags={}
for line in (obj/'flags.make').read_text().splitlines():
 if line.startswith('CXX_') and ' = ' in line:
  k,v=line.split(' = ',1);flags[k]=shlex.split(v)
affected=[p for p in obj.rglob('*.o.d') if 'MathUtils.hpp' in p.read_text()]
commands=[];replacement={}
for dep in affected:
 relative=dep.relative_to(obj).as_posix()[:-2];source=original/relative[:-2]
 target=t/'objects'/relative;target.parent.mkdir(parents=True,exist_ok=True)
 replacement['CMakeFiles/gaden.dir/'+relative]=str(target)
 commands.append(['/usr/bin/c++',*flags['CXX_DEFINES'],'-I'+str(t/'include'),*flags['CXX_INCLUDES'],*flags['CXX_FLAGS'],'-c',str(source),'-o',str(target)])
link=shlex.split((obj/'link.txt').read_text())
for i,token in enumerate(link):
 if token in replacement:link[i]=replacement[token]
 elif token.endswith('.o') or token.endswith('.a') or token.endswith('.so'):
  if not token.startswith('/'):link[i]=str(build/token)
link[link.index('-o')+1]=str(t/'libgaden.so');commands.append(link)
(t/'RNG_LIBRARY_BUILD_COMMANDS.json').write_text(json.dumps(commands,indent=2))
start=time.monotonic();peak=0;exits=[]
with (t/'rng_library_build.log').open('w') as log:
 for command in commands:
  p=subprocess.Popen(command,stdout=log,stderr=log,start_new_session=True,cwd=build)
  while p.poll() is None:
   rss=0
   for entry in Path('/proc').iterdir():
    if not entry.name.isdigit():continue
    try:
     if os.getpgid(int(entry.name))!=p.pid:continue
     for line in (entry/'status').read_text().splitlines():
      if line.startswith('VmRSS:'):rss+=int(line.split()[1])*1024
    except (ProcessLookupError,PermissionError,FileNotFoundError):pass
   peak=max(peak,rss)
   if rss>1610612736 or time.monotonic()-start>300:
    os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=3);raise RuntimeError('isolated compile cap')
   time.sleep(.1)
  exits.append(p.returncode);assert p.returncode==0,(t/'rng_library_build.log').read_text()[-4000:]
result=dict(verdict='PASS_ISOLATED_NATIVE_RANDOM_INITIALIZATION_COPY_BUILT_NOT_GENERATED',
 compile_wall_s=time.monotonic()-start,maximum_RSS_bytes=peak,compiled_native_objects=len(affected),exit_codes=exits,
 original_header_SHA256=hashlib.sha256(pristine.read_bytes()).hexdigest(),patched_header_SHA256=hashlib.sha256(dest.read_bytes()).hexdigest(),
 library_SHA256=hashlib.sha256((t/'libgaden.so').read_bytes()).hexdigest(),new_GADEN_realizations=0)
(t/'RNG_LIBRARY_BUILD_RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
'''
files={'frozen_contract.json':(OUT/'frozen_contract.json').read_bytes()}
result=json.loads(upload(files,code,'PREPARE_RNG_LIBRARY',360))
(OUT/'RNG_LIBRARY_BUILD_RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
