from common_n import *
import ast,base64,shutil
tree=ast.parse((WORK/'build_native_n.py').read_text())
code=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='code' for t in n.targets))
prefix="t=Path("+repr(REMOTE)+")\np=t/'code/native_entry.cpp'\n(t/'code/native_entry.FIRST_FAILED.cpp').write_bytes(p.read_bytes())\n(t/'build.FIRST_FAILED.log').write_bytes((t/'build.log').read_bytes())\np.write_bytes(base64.b64decode("+repr(base64.b64encode((WORK/'native_entry.cpp').read_bytes()).decode())+"))\n"
r=json.loads(run_remote('from pathlib import Path\nimport base64,json\n'+prefix+code,'BUILD_NATIVE_ENTRY_NAMESPACE_REPAIR',180))
dump(CORE/'ACTUAL_BINARY_PROVENANCE.json',r['result'])
for n,b in r['sourcefiles'].items():p=CORE/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(b))
shutil.copyfile(WORK/'native_entry.cpp',CORE/'source/native_entry.cpp')
rep=load(CORE/'TECHNICAL_REPAIRS.json');rep['repairs'].append(dict(kind='Isolated adapter compile namespace collision',attempts=1,change='Rename local State to ReplayState; explicit separate auto declarations; same calculations, frozen core untouched',scientific_calls_before_repair=0));dump(CORE/'TECHNICAL_REPAIRS.json',rep)
print(json.dumps({k:v for k,v in r['result'].items() if k not in ['actual_dynamic_dependencies_SHA256','LD_LIBRARY_PATH','linked_objects_SHA256']},indent=2))
