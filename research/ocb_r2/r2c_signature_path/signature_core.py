"""Fixed sigkernel-equivalent PDE and explicit level-three Chen signatures."""
import numpy as np
from numba import njit
from functools import lru_cache


def path(binary):
    x = np.column_stack((np.arange(10)/9, binary.astype(float)/np.sqrt(30)))
    return np.vstack((np.zeros((1,31)), x))


def static_table(x, y):
    # Upstream RBFKernel(sigma=1): exp(-||x-y||^2 / sigma).
    return np.exp(-np.square(x[:,None,:]-y[None,:,:]).sum(axis=-1))


@njit(cache=True)
def solve(g):
    n, m = g.shape
    k = np.ones((2*n+1,2*m+1))
    for i in range(2*n):
        for j in range(2*m):
            d = g[i//2,j//2]/4
            d2 = d*d/12
            k[i+1,j+1] = (k[i+1,j]+k[i,j+1])*(1+.5*d+d2)-k[i,j]*(1-d2)
    return k[-1,-1]


def kernel(x,y):
    a = static_table(x,y)
    return float(solve(a[1:,1:]+a[:-1,:-1]-a[1:,:-1]-a[:-1,1:]))


@njit(cache=True)
def lookup_batch(table, choices_a, choices_b):
    result = np.empty(len(choices_a))
    for b in range(len(choices_a)):
        g = np.empty((10,10))
        for i in range(10):
            for j in range(10):
                a0,a1 = choices_a[b,i],choices_a[b,i+1]
                b0,b1 = choices_b[b,j],choices_b[b,j+1]
                g[i,j] = table[i+1,a1,j+1,b1]+table[i,a0,j,b0]-table[i+1,a1,j,b0]-table[i,a0,j+1,b1]
        result[b] = solve(g)
    return result


def choices(n, identifiers, channel):
    rng=np.random.default_rng(np.random.SeedSequence([2026093201,*identifiers,channel]))
    return np.column_stack((np.zeros(n,dtype=np.int64),rng.integers(0,3,size=(n,10),dtype=np.int64)))


def q_scores(ref,y,identifiers):
    """Three independent streams; prefixes give nested 2048 and 4096 audits."""
    rp=np.stack([path(r) for r in ref]).transpose(1,0,2)
    yp=path(y)[:,None,:]
    table=np.exp(-np.square(rp[:,:,None,None,:]-rp[None,None,:,:,:]).sum(axis=-1))
    ty=np.exp(-np.square(rp[:,:,None,None,:]-yp[None,None,:,:,:]).sum(axis=-1))
    c0,c1,c2=[choices(4096,identifiers,ch) for ch in (0,1,2)]
    selfk=lookup_batch(table,c1,c2)
    targetk=lookup_batch(ty,c0,np.zeros_like(c0))
    assert np.isfinite(selfk).all() and np.isfinite(targetk).all()
    return {b:dict(SIG_Q=float(selfk[:b].mean()-2*targetk[:b].mean()),
                   Q_self_mean=float(selfk[:b].mean()),Q_target_mean=float(targetk[:b].mean())) for b in (2048,4096)}


def raw_score(ref,y):
    xs=[path(r) for r in ref];yp=path(y)
    selfk=sum(kernel(xs[i],xs[j]) for i in range(3) for j in range(3) if i!=j)/6
    return selfk-2*sum(kernel(x,yp) for x in xs)/3


def chen(sig,v):
    a,b,c=sig
    vv=np.outer(v,v)
    return (a+v,b+np.outer(a,v)+vv/2,
            c+b[:,:,None]*v[None,None,:]+a[:,None,None]*vv[None,:,:]/2+vv[:,:,None]*v[None,None,:]/6)


def signature(x):
    d=x.shape[1]
    s=(np.zeros(d),np.zeros((d,d)),np.zeros((d,d,d)))
    for v in np.diff(x,axis=0):
        s=chen(s,v)
    return s


@lru_cache(maxsize=64)
def binary_signature(data):
    return signature(path(np.frombuffer(data,dtype=np.bool_).reshape(10,30)))


@lru_cache(maxsize=64)
def binary_q_signature(data):
    return q_expected_signature(np.frombuffer(data,dtype=np.bool_).reshape(3,10,30))


def q_expected_signature(ref):
    """Exact empirical product law, explicit tensors; conditional Chen recursion.

    The present snapshot is the only state needed to integrate the NEXT increment.
    This integrates Q exactly; it is not a dynamics or Markov assumption for RAW.
    """
    xp=np.stack([path(r) for r in ref])
    states=[signature(xp[i,:2]) for i in range(3)]
    for t in range(2,xp.shape[1]):
        nxt=[]
        for j in range(3):
            ss=[chen(states[i],xp[j,t]-xp[i,t-1]) for i in range(3)]
            nxt.append(tuple(sum(v[l] for v in ss)/3 for l in range(3)))
        states=nxt
    return tuple(sum(v[l] for v in states)/3 for l in range(3))


def anatomy_scores(ref,y):
    fs=[binary_signature(r.tobytes()) for r in ref];fy=binary_signature(y.tobytes());fq=binary_q_signature(ref.tobytes())
    raw=[];q=[]
    for level in range(3):
        raw.append(sum(float(np.sum(fs[i][level]*fs[j][level])) for i in range(3) for j in range(3) if i!=j)/6
                   -2*sum(float(np.sum(f[level]*fy[level])) for f in fs)/3)
        q.append(float(np.sum(fq[level]*fq[level]))-2*float(np.sum(fq[level]*fy[level])))
    return [float(sum(q[:l])-sum(raw[:l])) for l in (1,2,3)]
