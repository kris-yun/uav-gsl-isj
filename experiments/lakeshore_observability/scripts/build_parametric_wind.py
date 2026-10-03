"""Regular cell-centre wind CSV, with a divergence-free streamfunction front."""
import pathlib,json,argparse,numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=pathlib.Path(__file__).resolve().parents[3]; EXP=ROOT/'experiments/lakeshore_observability'; OUT=ROOT/'evidence/lakeshore_observability_r0_r2'
def build(name):
 assert json.loads((OUT/'R0_wisco_effect_summary.json').read_text())['decision']=='R0_GO'
 x=np.arange(-97.5,300,5); y=np.arange(-97.5,100,5); z=np.arange(-2.5,150,5)
 Z,Y,X=np.meshgrid(z,y,x,indexing='ij'); zz=np.maximum(Z,0)
 H=100.; dz=15.; dx=35.; top=150.; front=120.
 f=lambda a:.5*(1-np.tanh((a-H)/dz))
 integ=lambda a:.5*(a-dz*(np.log(np.cosh((a-H)/dz))-np.log(np.cosh(-H/dz))))
 mean=integ(top)/top; I=integ(zz)-zz*mean; g=f(zz)-mean
 s=.5*(1-np.tanh((X-front)/dx)); sp=-.5/dx/np.cosh((X-front)/dx)**2
 u=np.full_like(X,2.);w=np.zeros_like(X);amp=0.
 if name=='L1':u=.4+1.6*f(zz)
 if name in ['F1','F2']:
  target=.5 if name=='F1' else 1.;amp=target/float(np.max(-sp*I));u=.4+amp*s*g;w=-amp*sp*I
 v=np.zeros_like(X); dest=EXP/'generated_project/wind_simulations'/name;dest.mkdir(parents=True,exist_ok=True)
 pd.DataFrame({'U:0':u.ravel(),'U:1':v.ravel(),'U:2':w.ravel(),'Points:0':X.ravel(),'Points:1':Y.ravel(),'Points:2':Z.ravel()}).to_csv(dest/'wind_0.csv',index=False,float_format='%.9g')
 div=np.gradient(u,5,axis=2)+np.gradient(w,5,axis=0);interior=div[2:-2,2:-2,2:-2]
 qc={'environment':name,'cell_size_m':5,'dims':[80,40,31],'min':[-100,-100,-5],'max':[300,100,150],'w_max':float(w.max()),'w_min':float(w.min()),'max_abs_div_finite_difference':float(abs(interior).max()),'analytic_divergence':'exact zero above ground: u=.4+A*s(x)*Iprime(z), w=-A*sprime(x)*I(z)','amplitude':amp,'H_lake_m':H,'delta_z_m':dz,'delta_x_m':dx,'x_front_m':front,'top_w_m_s':0.,'u_quantiles':np.quantile(u,[0,.25,.5,.75,1]).tolist(),'w_quantiles':np.quantile(w,[0,.25,.5,.75,1]).tolist(),'parameter_basis':'Wisco POST22 paper layer ~100m; JGR Mg=.4 weak background and 2m/s background control. Ideal mechanism fields, not fitted transient weather.'}
 qc['pass']=bool(np.isfinite(u).all() and np.isfinite(w).all() and np.max(abs(interior))<.005 and w.min()>=-1e-8)
 (OUT/f'wind_{name}_QC.json').write_text(json.dumps(qc,indent=2))
 (EXP/'configs'/f'wind_{name}.yaml').write_text(json.dumps(qc,indent=2)) # JSON is valid YAML
 fig,axs=plt.subplots(1,5,figsize=(16,4),layout='constrained');j=len(y)//2
 axs[0].quiver(X[::2,j,::3],Z[::2,j,::3],u[::2,j,::3],w[::2,j,::3]);axs[0].set_title(name+' X-Z');axs[0].set_xlabel('x (m)');axs[0].set_ylabel('z (m)')
 for a,height in zip(axs[1:],[10,30,60,100]):
  k=np.argmin(abs(z-height));a.imshow(u[k],extent=[-100,300,-100,100],origin='lower',aspect='auto');a.set_title(f'u at cell z={z[k]} m');a.set_xlabel('x (m)')
 fig.savefig(OUT/f'wind_{name}_QC.png',dpi=130);plt.close(fig)
 assert qc['pass'],qc
 print(json.dumps(qc))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('environment',choices=['N0','L1','F1','F2']);build(a.parse_args().environment)
