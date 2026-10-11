from common_r2 import *
import csv,shutil,math
src=(R1/'source/native_cold_entry.cpp').read_text()
needle='}else if(mode=="map"||mode=="history"){'
assert src.count(needle)==1
insert=r'''}else if(mode=="point_all"){
  auto jobs=csv(payload);std::ofstream index(out/"INDEX.csv");index<<"id,output\n";
  for(auto& j:jobs){rng(in);auto d=out/j.at("id");fs::create_directories(d);R4Audit::initialize(d/"forward");
   auto state=csv(in/"rng.csv").at(0);bool ready=!state.count("ready")||integer(state,"ready");R4Audit::cache_ready=ready;R4Audit::last_index=ready?r4_gaussian_index():0;
   Utils::NQA::Node node(nullptr,{integer(j,"origin_i"),integer(j,"origin_j")},{1,1},sim->quadtree->map);
   sim->forward(node,true,Vector2(float(number(j,"point_x")),float(number(j,"point_y"))));R4Audit::finish(s.post);index<<j.at("id")<<','<<d.string()<<'\n';index.flush();
  }
 }else if(mode=="posterior_metrics"){
  std::ofstream f(out/"METRICS.csv");f<<std::setprecision(17)<<"id,mean_x,mean_y,top5_x,top5_y,variance\n";
  for(auto& j:csv(payload)){
   std::ifstream b(j.at("path"),std::ios::binary);b.read((char*)s.post.data(),s.post.size()*sizeof(double));if(!b)throw std::runtime_error("posterior missing");
   auto g=Grid2D<double>(s.post,s.occ,s.m);auto mu=Utils::ExpectedValue(g,1);auto t5=Utils::ExpectedValue(g,.05);auto v=Utils::Variance(g);f<<j.at("id")<<','<<mu.x<<','<<mu.y<<','<<t5.x<<','<<t5.y<<','<<v<<'\n';
  }
 }else if(mode=="map"||mode=="history"){'''
src=src.replace(needle,insert)
(CORE/'source').mkdir(exist_ok=True);(CORE/'source/native_batch_entry.cpp').write_text(src,encoding='utf-8')
files={'native_batch_entry.cpp':src.encode()}
code=r'''from pathlib import Path
import subprocess,time,hashlib,json,shutil
r4=Path('/home/zyc/pmfs_native_capture_r4_20261009');ctx=json.loads((r4/'BUILD_CONTEXT.json').read_text());ram=Path('/dev/shm/pmfs_r2/native_build');ram.mkdir()
objs=[Path('/home/zyc/pmfs_b4_m1_representation_20261010/Simulations_native.o'),Path('/home/zyc/pmfs_m2_semantic_anchor_20261010_build2/PMFSLib_frozen.o'),r4/'Math_accessors.o',r4/'NQAQuadtree.o']
cmds=[['/usr/bin/c++',*ctx['compileflags'],'-c',str(t/'native_batch_entry.cpp'),'-o',str(ram/'batch.o')],['/usr/bin/c++','-fopenmp','-fsanitize=undefined','-Wl,--gc-sections',str(ram/'batch.o'),*[str(p) for p in objs],'-o',str(ram/'native_batch_entry'),*ctx['link_tail']]]
records=[]
for i,cmd in enumerate(cmds):
 st=time.monotonic();p=subprocess.run(cmd,stdout=(t/f'native_build_{i}.stdout').open('w'),stderr=(t/f'native_build_{i}.stderr').open('w'),timeout=180);assert p.returncode==0,(t/f'native_build_{i}.stderr').read_text()[-2500:];records.append(dict(command=cmd,wall_s=time.monotonic()-st))
permanent=Path(DATA)/'binary_preservation';permanent.mkdir()
for p in ram.iterdir():shutil.copy2(p,permanent/p.name)
print(json.dumps({'status':'COMPILE_PASS_NOT_NUMERICAL_QUALIFICATION','binary_SHA256':hashlib.sha256((ram/'native_batch_entry').read_bytes()).hexdigest(),'unchanged_core_objects':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in objs},'build_records':records}))
'''.replace('DATA',repr(DATA))
r=json.loads(upload(files,code,'build_r2_native_batch_thin_entry',240));dump(CORE/'NATIVE_BATCH_PROVENANCE.json',r);print(json.dumps({'status':r['status'],'wall_s':sum(x['wall_s'] for x in r['build_records'])}))
