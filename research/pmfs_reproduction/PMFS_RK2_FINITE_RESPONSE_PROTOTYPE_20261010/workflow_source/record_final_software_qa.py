"""Record repaired source QA; no scientific datasets or production fits."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import unittest,io,hashlib,json,time
import test_rk2_models
started=time.perf_counter()
stream=io.StringIO()
r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(test_rk2_models.SoftwareTests))
out=Path(__file__).resolve().parent/'final_reports'
record=dict(status='PASS' if r.wasSuccessful() else 'FAIL',cases=r.testsRun,failures=len(r.failures),errors=len(r.errors),wall_s=time.perf_counter()-started,
    model_source_SHA256=hashlib.sha256((out.parent/'rk2_models.py').read_bytes()).hexdigest(),test_source_SHA256=hashlib.sha256(Path(test_rk2_models.__file__).read_bytes()).hexdigest(),
    scientific_dataset_used=False,scientific_models_fitted=0,note='Analytic toy objective/router QA only; original pre-repair QA record preserved unchanged.')
(out/'FINAL_MODEL_SOFTWARE_QA.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
(out/'FINAL_MODEL_SOFTWARE_QA.stdout').write_text(stream.getvalue(),encoding='utf-8')
print(json.dumps(record,indent=2))
raise SystemExit(0 if r.wasSuccessful() else 1)
