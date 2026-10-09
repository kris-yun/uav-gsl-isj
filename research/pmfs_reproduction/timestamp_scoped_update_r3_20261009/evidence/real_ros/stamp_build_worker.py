from pathlib import Path
import subprocess,json,hashlib,sys
t=Path(__file__).resolve().parent
with (t/'stamp_build.log').open('w') as log:
 for i,cmd in enumerate(json.loads((t/'stamp_build_commands.json').read_text())):
  p=subprocess.run(cmd,stdout=log,stderr=log)
  if p.returncode:(t/'STAMP_BUILD_RESULT.json').write_text(json.dumps(dict(verdict='FAIL',step=i)));sys.exit(p.returncode)
(t/'STAMP_BUILD_RESULT.json').write_text(json.dumps(dict(verdict='PASS',ELF_SHA256={n:hashlib.sha256((t/n).read_bytes()).hexdigest() for n in ['pmfs_original','pmfs_stamped']})))
