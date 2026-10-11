"""Stable read-only entrypoint for the parent package verifier."""
import sys
sys.dont_write_bytecode=True
import importlib.util
from pathlib import Path
_path=Path(__file__).resolve().with_name('verify_raw_receiver_queries.py')
_spec=importlib.util.spec_from_file_location('independent_raw_receiver_arithmetic',_path)
_impl=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_impl)

def verify(root):
    """root is the complete audit ZIP root; returns result dict, writes nothing."""
    result,_rows=_impl.verify(Path(root))
    return result

if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True)
    print(json.dumps(verify(p.parse_args().package),ensure_ascii=False,indent=2))
