from common_n import *
import re,shlex,difflib
original=(WORK/'C_NATIVE_SOURCE_REVIEW.stdout').read_text(encoding='utf-8')
original=original[original.index('#include "gaden/RunningSimulation.hpp"'):].rstrip()+'\n'
(WORK/'C_original/RunningSimulation.cpp').write_text(original,encoding='utf-8')
helper=r'''
#include <sstream>
#include <limits>
namespace gaden {
namespace NMC {
thread_local uint64_t released=0, removed=0, navBlocks=0, physicalBlocks=0, noiseCalls=0;
bool flag(const char* name){const char* v=std::getenv(name);return v && std::string(v)=="1";}
const bool restrictNav=flag("NMC_RESTRICT_NAV"),fixHeight=flag("NMC_FIX_HEIGHT");
Vector3i navIndex(Vector3 p){return {int(std::floor((p.x-float(-7.55))/.25f)),int(std::floor((p.y-float(-7.88))/.25f)),0};}
const std::vector<bool>& nav(){
 static const std::vector<bool> m=[](){
  std::vector<bool> a(34*45,false);const char* path=std::getenv("NMC_NAV_PATH");
  if(!path)throw std::runtime_error("NMC nav path missing");std::ifstream f(path);if(!f)throw std::runtime_error("NMC nav missing");
  std::string line;std::getline(f,line);int n=0;
  while(std::getline(f,line)){std::stringstream s(line);std::string x;int col=0,i=-1,free=-1;
   while(std::getline(s,x,',')){if(col==0)i=std::stoi(x);if(col==3)free=std::stoi(x);col++;}
   if(i!=n||free<0)throw std::runtime_error("NMC nav order");a.at(i)=free==1;n++;
  }
  if(n!=34*45||std::count(a.begin(),a.end(),true)!=447)throw std::runtime_error("NMC nav size");return a;
 }();return m;
}
bool navFree(Vector3 p){auto i=navIndex(p);return i.x>=0&&i.x<34&&i.y>=0&&i.y<45&&nav().at(i.x+i.y*34);}
}
}
'''
src=original.replace('namespace gaden\n{',helper+'\nnamespace gaden\n{',1)
src=src.replace('        AddFilaments();\n        MoveFilaments();','''        NMC::released=0;NMC::removed=0;NMC::navBlocks=0;NMC::physicalBlocks=0;NMC::noiseCalls=0;
        AddFilaments();
        MoveFilaments();
        if(const char* p=std::getenv("NMC_STATE_TRACE")) {
          static thread_local std::ofstream tr(p);static thread_local bool header=false;
          if(!header){tr<<"iteration,time_before_increment_s,released,removed,alive,z_min,z_max,nav_blocks,physical_blocks,gaussian_cache_calls,gaussian_index,wind_index\\n";header=true;}
          float lo=std::numeric_limits<float>::infinity(),hi=-lo;
          for(auto& f:*activeFilaments){lo=std::min(lo,f.position.z);hi=std::max(hi,f.position.z);}
          tr<<std::setprecision(17)<<currentIteration<<','<<currentTime<<','<<NMC::released<<','<<NMC::removed<<','<<activeFilaments->size()<<','<<lo<<','<<hi<<','<<NMC::navBlocks<<','<<NMC::physicalBlocks<<','<<NMC::noiseCalls<<','<<gaussian.nmc_index()<<','<<config->windSequence.GetCurrentIndex()<<'\\n';
        }''')
src=src.replace('            activeFilaments->emplace_back(position, parameters.filamentInitialSigma);','            activeFilaments->emplace_back(position, parameters.filamentInitialSigma);NMC::released++;')
needle='            newPosition.z += gaussian.nextValue(0, parameters.filamentNoise_std) * parameters.deltaTime;'
assert src.count(needle)==1
src=src.replace(needle,needle+'\n            NMC::noiseCalls+=3;\n            if(NMC::fixHeight)newPosition.z=filament.position.z;')
src=src.replace('                isActive[i] = false;', '                {isActive[i] = false;NMC::removed++;}')
src=src.replace('if (startCell == endCell)','if (startCell == endCell && (!NMC::restrictNav || NMC::navIndex(filament.position)==NMC::navIndex(end)))')
src=src.replace('            if (cellState == Environment::CellState::Obstacle || cellState == Environment::CellState::OutOfBounds)', '''            bool physicalBlock=cellState == Environment::CellState::Obstacle || cellState == Environment::CellState::OutOfBounds;
            bool navBlock=NMC::restrictNav && !NMC::navFree(filament.position);
            if (physicalBlock || navBlock)''')
src=src.replace('                Vector3 normal = previousCell - currentCell;', '''                Vector3 normal = previousCell - currentCell;
                if(physicalBlock)NMC::physicalBlocks++;
                else {NMC::navBlocks++;normal=Vector3(NMC::navIndex(previous)-NMC::navIndex(filament.position));}
                if(normal==Vector3(0,0,0))throw std::runtime_error("NMC zero collision normal");''')
header=(WORK/'C_original/MathUtils.hpp').read_text()
header=header.replace('    private:\n        uint16_t m_index;', '        uint16_t nmc_index() const{return m_index;}\n    private:\n        uint16_t m_index;')
assert 'nmc_index' in header
files={'C_source/RunningSimulation.cpp':src.encode(),'C_include/gaden/internal/MathUtils.hpp':header.encode()}
(CORE/'source/C').mkdir(parents=True,exist_ok=True)
(CORE/'source/C/RunningSimulation.cpp').write_text(src,encoding='utf-8')
(CORE/'source/C/RunningSimulation.original.cpp').write_text(original,encoding='utf-8')
(CORE/'source/C/MathUtils.hpp').write_text(header,encoding='utf-8')
(CORE/'source/C/intervention.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),src.splitlines(True),fromfile='original',tofile='NMC')),encoding='utf-8')
flags=(WORK/'C_original/flags.make').read_text()
args=[]
for key in ['CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS']:
 args+=shlex.split(next(x.split(' = ',1)[1] for x in flags.splitlines() if x.startswith(key+' = ')))
args=[x for x in args if x!='-g']
command=['/usr/bin/c++','-I'+REMOTE+'/C_include',*args,'-g0','-c',REMOTE+'/C_source/RunningSimulation.cpp','-o','/dev/shm/nmc_C/RunningSimulation.o']
link=load(WORK/'C_original/RNG_LIBRARY_LINK_COMMAND.json')
link=[x.replace('/home/zyc/pmfs_m2_process_observation_20261010/objects/src/RunningSimulation.cpp.o','/dev/shm/nmc_C/RunningSimulation.o') for x in link]
link[link.index('-o')+1]='/dev/shm/nmc_C/libgaden.so'
code='''from pathlib import Path
import os,subprocess,time,json,hashlib,shutil
ram=Path('/dev/shm/nmc_C');ram.mkdir(exist_ok=False)
commands=COMMANDS;report=[]
for i,cmd in enumerate(commands):
 start=time.time();p=subprocess.run(cmd,stdout=(t/f'C_build_{i}.stdout').open('w'),stderr=(t/f'C_build_{i}.stderr').open('w'),timeout=180)
 report.append({'command':cmd,'exitcode':p.returncode,'wall_s':time.time()-start})
 if p.returncode:print((t/f'C_build_{i}.stderr').read_text()[-3500:]);raise SystemExit(1)
keep=Path(DATA)/'C_binary_preservation';keep.mkdir()
for f in ram.iterdir():shutil.copy2(f,keep/f.name)
report={'status':'COMPILE_PASS_NOT_PHYSICAL_QUALIFICATION','builds':report,'library_SHA256':hashlib.sha256((ram/'libgaden.so').read_bytes()).hexdigest()}
(t/'C_BUILD.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
'''.replace('COMMANDS',repr([command,link])).replace('DATA',repr(DATA))
r=json.loads(upload(files,code,'C_controlled_library_build',240));dump(CORE/'C_BUILD.json',r);print(json.dumps({'status':r['status'],'compile_s':sum(x['wall_s'] for x in r['builds'])}))
