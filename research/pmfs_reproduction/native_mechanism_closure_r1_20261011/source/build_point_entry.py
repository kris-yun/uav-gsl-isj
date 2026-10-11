from common_n import *
src=(WORK/'native_entry.cpp').read_text()
src=src.replace('long double forward(const Utils::NQA::Node& node) {','long double forward(const Utils::NQA::Node& node,bool exact=false,Vector2 point={0,0}) {')
src=src.replace('SimulationSource src(&node,measuredHitProb.metadata);','SimulationSource src=exact?SimulationSource(point,measuredHitProb.metadata):SimulationSource(&node,measuredHitProb.metadata);')
src=src.replace('mode=="anchor_forward"','(mode=="anchor_forward"||mode=="point_forward")')
src=src.replace('auto score=sim->forward(node);','auto score=sim->forward(node,mode=="point_forward",mode=="point_forward"?Vector2(float(number(j,"point_x")),float(number(j,"point_y"))):Vector2(0,0));')
files={'code/native_point_entry.cpp':src.encode()};(CORE/'source/native_point_entry.cpp').write_text(src,encoding='utf-8')
code=r'''from pathlib import Path
import subprocess,time,shutil,hashlib,json
r4=Path('/home/zyc/pmfs_native_capture_r4_20261009');ctx=json.loads((r4/'BUILD_CONTEXT.json').read_text());ram=Path('/dev/shm/nmc_point');ram.mkdir()
objs=[Path('/home/zyc/pmfs_b4_m1_representation_20261010/Simulations_native.o'),Path('/home/zyc/pmfs_m2_semantic_anchor_20261010_build2/PMFSLib_frozen.o'),r4/'Math_accessors.o',r4/'NQAQuadtree.o']
cmds=[['/usr/bin/c++',*ctx['compileflags'],'-c',str(t/'code/native_point_entry.cpp'),'-o',str(ram/'point_entry.o')],['/usr/bin/c++','-fopenmp','-fsanitize=undefined','-Wl,--gc-sections',str(ram/'point_entry.o'),*[str(p) for p in objs],'-o',str(ram/'native_point_entry'),*ctx['link_tail']]]
rr=[]
for i,cmd in enumerate(cmds):
 start=time.time();p=subprocess.run(cmd,stdout=(t/f'point_build_{i}.stdout').open('w'),stderr=(t/f'point_build_{i}.stderr').open('w'),timeout=180)
 assert p.returncode==0,(t/f'point_build_{i}.stderr').read_text()[-3000:];rr.append(dict(command=cmd,wall_s=time.time()-start))
dest=Path(DATA)/'point_binary_preservation';dest.mkdir()
for p in ram.iterdir():shutil.copy2(p,dest/p.name)
print(json.dumps({'status':'PASS_NATIVE_POINT_MODE_LINK','builds':rr,'entry_SHA256':hashlib.sha256((ram/'native_point_entry').read_bytes()).hexdigest(),'kernel_objects_unchanged':True}))
'''.replace('DATA',repr(DATA))
r=json.loads(upload(files,code,'build_native_point_mode_thin_entry',240));dump(CORE/'POINT_ENTRY_PROVENANCE.json',r);print(json.dumps({'status':r['status'],'build_s':sum(x['wall_s'] for x in r['builds'])}))
