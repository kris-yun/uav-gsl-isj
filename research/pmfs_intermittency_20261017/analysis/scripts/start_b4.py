from pathlib import Path
import zipfile,subprocess,sys,time,json
R=Path(__file__).resolve().parents[1];W=R.parent
p=W/'B4_NATIVE_AUDIT_20261017'/'B4原生实查_间歇接触机制与逐格重放_20261017.zip'
extract=R/'b4_input';extract.mkdir(exist_ok=False)
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None
 z.extractall(extract)
source=extract/'B4_NATIVE_AUDIT_20261017';start=time.time()
q=subprocess.run([sys.executable,str(source/'reproduce_native_audit.py'),'--out',str(R/'results'/'b4_recomputed')],capture_output=True,text=True)
(R/'logs'/'b4.stdout').write_text(q.stdout);(R/'logs'/'b4.stderr').write_text(q.stderr)
(R/'logs'/'b4_execution.json').write_text(json.dumps(dict(command=q.args,returncode=q.returncode,elapsed_s=time.time()-start),indent=2))
print(q.returncode,q.stdout[-1000:]);sys.exit(q.returncode)
