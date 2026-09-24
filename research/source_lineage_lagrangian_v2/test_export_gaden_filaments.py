#!/usr/bin/env python3
import importlib.util, struct, tempfile, zlib
from pathlib import Path
import numpy as np

P=Path(__file__).with_name("export_gaden_filaments.py")
s=importlib.util.spec_from_file_location("exp",P)
m=importlib.util.module_from_spec(s); s.loader.exec_module(m)

def modern(path):
    f=[(1.,2.,3.,.4),(4.,5.,6.,.7)]
    raw=struct.pack("<ii",4,0)+b"X"*40
    raw+=struct.pack("<Q",9)+b"filaments"+struct.pack("<Q",len(f))
    raw+=b"".join(struct.pack("<ffff",*x) for x in f)
    data=b"GADEN_RESULT\x00"+struct.pack("<B",1)+struct.pack("<Q",len(raw))+zlib.compress(raw)
    path.write_bytes(data)
    a,meta=m.parse_snapshot(path)
    assert np.allclose(a,np.asarray(f,np.float32))
    assert meta["major"]==4

def legacy(path,minor):
    raw=struct.pack("<ii",2,minor)+b"\x00"*92
    fmt="<idddd" if minor<=5 else "<iffff"
    f=[(0.,1.,2.,.2),(1.,2.,3.,.21),(2.,3.,4.,.22)]
    for i,x in enumerate(f): raw+=struct.pack(fmt,i,*x)
    path.write_bytes(zlib.compress(raw))
    a,meta=m.parse_snapshot(path)
    assert np.allclose(a,np.asarray(f,np.float32),atol=1e-6)
    assert meta["minor"]==minor

with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    modern(td/"iteration_1")
    legacy(td/"iteration_2",5)
    legacy(td/"iteration_3",6)
print("GADEN_FILAMENT_EXPORTER_SYNTHETIC_PASS")

steps,times=m.gaden_save_schedule(566,0.1,0.5)
assert len(steps)==566
assert steps[:7].tolist()==[0,6,11,16,22,28,34]
assert steps[-1]==2998
assert abs(times[-1]-299.80908203125)<1e-9
