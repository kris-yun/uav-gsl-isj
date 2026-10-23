from pathlib import Path
import ctypes as ct
import hashlib, struct, zlib
import numpy as np

class NativeFormatError(ValueError): pass

def decode_frame(path):
    """Version 3.0, point source, filament records; reject unknown encodings."""
    b=Path(path).read_bytes()
    if b[:13]!=b'GADEN_RESULT\0': raise NativeFormatError('modern GADEN header required')
    mode=b[13];n=struct.unpack_from('<Q',b,14)[0]
    if mode==1: raw=zlib.decompress(b[22:])
    elif mode==0: raw=b[22:]
    else: raise NativeFormatError('unsupported compression; no silent conversion')
    if len(raw)!=n: raise NativeFormatError('decompression size mismatch')
    off=0
    def take(fmt):
        nonlocal off
        value=struct.unpack_from('<'+fmt,raw,off);off+=struct.calcsize('<'+fmt);return value
    def string():
        nonlocal off
        length=take('Q')[0];v=raw[off:off+length].decode('ascii');off+=length;return v
    version=take('ii')
    if version!=(3,0): raise NativeFormatError('unqualified version '+str(version))
    dimensions=take('iii');origin=take('fff');maximum=take('fff');cell=take('f')[0]
    kind=string()
    if kind!='point': raise NativeFormatError('only historical point-source ABI qualified')
    source=take('fff');gas_type=take('i')[0]
    moles,air=take('ff');wind_index=take('i')[0]
    if string()!='filaments': raise NativeFormatError('not a filament archive')
    count=take('Q')[0]
    if len(raw)-off != count*16: raise NativeFormatError('unexpected filament ABI')
    fil=np.frombuffer(raw,dtype='<f4',count=count*4,offset=off).reshape(count,4).copy()
    if not np.isfinite(fil).all() or (len(fil) and np.any(fil[:,3]<=0)):
        raise NativeFormatError('invalid physical filament')
    return dict(version=version,dimensions=dimensions,origin=origin,maximum=maximum,cell=cell,
                source_xyz=source,gas_type=gas_type,moles=moles,air=air,
                wind_index=wind_index,filaments=fil)

class NativeQuery:
    def __init__(self,occupancy_path,library_path):
        lines=Path(occupancy_path).read_text().splitlines()
        self.dims=np.array(list(map(int,lines[2].split()[1:])),dtype=np.int32)
        self.origin=np.array(list(map(float,lines[0].split()[1:])),dtype=np.float32)
        self.cell=np.float32(lines[3].split()[1])
        a=np.array([[int(v) for v in s.split()] for s in lines[4:] if s!=';'],dtype=np.uint8)
        self.grid=np.ascontiguousarray(a.reshape(self.dims[2],self.dims[0],self.dims[1]).transpose(0,2,1).ravel())
        self.lib=ct.CDLL(str(Path(library_path).resolve()))
        f32=np.ctypeslib.ndpointer(dtype=np.float32,flags='C_CONTIGUOUS')
        i32=np.ctypeslib.ndpointer(dtype=np.int32,flags='C_CONTIGUOUS')
        u8=np.ctypeslib.ndpointer(dtype=np.uint8,flags='C_CONTIGUOUS')
        self.function=self.lib.query_many
        self.function.argtypes=[f32,ct.c_int,f32,ct.c_int,u8,i32,f32,ct.c_float,ct.c_float,ct.c_float,f32,u8]
        self.function.restype=ct.c_int

    def query(self,frame,points):
        p=np.ascontiguousarray(points,dtype=np.float32).reshape(-1,3)
        if not np.isfinite(p).all(): raise ValueError('nonfinite point')
        index=np.floor((p-self.origin)/self.cell).astype(int)
        if np.any(index<0) or np.any(index>=self.dims): raise ValueError('query outside actual map')
        if tuple(frame['dimensions'])!=tuple(self.dims) or not np.array_equal(frame['origin'],self.origin):
            raise NativeFormatError('archive environment differs from occupancy')
        out=np.zeros(len(p),dtype=np.float32);valid=np.zeros(len(p),dtype=np.uint8)
        code=self.function(frame['filaments'],len(frame['filaments']),p,len(p),self.grid,self.dims,
             self.origin,self.cell,frame['moles'],frame['air'],out,valid)
        if code or not valid.all() or not np.isfinite(out).all(): raise ValueError('invalid receiver is not a valid zero')
        return out

    def local_wind(self,path,points):
        b=Path(path).read_bytes()
        # WindSequence::WriteToFiles: two int32 version fields, then native
        # interleaved xyz float32; unlike result vectors, there is no count.
        version=struct.unpack_from('<ii',b)
        n=int(np.prod(self.dims))
        if version!=(3,0) or len(b)!=8+n*12:
            raise NativeFormatError('wind count/layout mismatch')
        v=np.frombuffer(b,dtype='<f4',offset=8).reshape(n,3)
        p=np.asarray(points,dtype=np.float32)
        index=np.floor((p-self.origin)/self.cell).astype(int)
        if np.any(index<0) or np.any(index>=self.dims): raise ValueError('wind point outside environment')
        i=index[:,0]+index[:,1]*self.dims[0]+index[:,2]*self.dims[0]*self.dims[1]
        return v[i].copy()

class NativeWorldExecutor:
    """Evaluator-owned archive; returns only executed past samples and local wind.

    No source label is returned. No interpolation, rewind, synthetic zero, saved
    target-state translation, CFD, new propagation or complete wind-field export.
    This class is a fixed-probe component, not a qualified M2 motion executor.
    """
    def __init__(self,root,query,timeline):
        self.root=Path(root);self.query=query;self.timeline=timeline;self.last=-float('inf')

    def observe(self,indices,points):
        points=np.asarray(points,dtype=np.float32)
        ts=np.array([float(self.timeline[i]['internal_simulation_time_s']) for i in indices])
        if len(ts)==0 or np.any(np.diff(ts)<=0) or ts[0]<=self.last:
            raise ValueError('cannot replay or rewind a consumed observation')
        values=[];winds=[]
        for i in indices:
            r=self.timeline[i];frame=decode_frame(self.root/('iteration_'+r['record_index']))
            if frame['wind_index']!=int(r['wind_index']): raise NativeFormatError('wind/physical clock mismatch')
            values.append(self.query.query(frame,points))
            winds.append(self.query.local_wind(self.root/'wind'/('wind_iteration_'+str(frame['wind_index'])),points))
        self.last=float(ts[-1])
        return {'times_s':ts,'values':np.array(values),'local_wind_mps':np.array(winds),
                'positions_m':points.copy(),'scope':'fixed probes in original passive native plume, no UAV dynamics'}
