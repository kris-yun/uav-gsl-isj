import json,subprocess,sys,hashlib
from pathlib import Path
task=Path(__file__).resolve().parent.parent
commands=json.loads((task/'build_commands.json').read_text())
with (task/'build.log').open('w') as log:
    for index,cmd in enumerate(commands):
        log.write('COMMAND '+str(index)+'\n');log.flush()
        p=subprocess.run(cmd,stdout=log,stderr=log)
        if p.returncode:
            (task/'BUILD_RESULT.json').write_text(json.dumps(dict(verdict='FAIL',command=index,exit=p.returncode)))
            sys.exit(p.returncode)
(task/'BUILD_RESULT.json').write_text(json.dumps(dict(verdict='PASS',executables={n:hashlib.sha256((task/n).read_bytes()).hexdigest() for n in ['pmfs_wind_probe','gmrf_wind_observed']})))
