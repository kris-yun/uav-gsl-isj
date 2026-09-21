"""Verify repository blob bytes against the committed dataset SHA256 manifest."""
import hashlib,json,subprocess,sys
ref=sys.argv[1] if len(sys.argv)>1 else 'HEAD'
prefix='evidence/mipo_probe_v1/'
def blob(path):return subprocess.check_output(['git','show',ref+':'+path])
checks=json.loads(blob(prefix+'SHA256SUMS.json'))
for path,expected in checks.items():
    assert hashlib.sha256(blob(prefix+path)).hexdigest()==expected,path
print('GIT_BLOB_SHA256_PASS',ref,len(checks))
