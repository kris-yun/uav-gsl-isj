"""Verify adapted east/north model against pinned publisher forward model."""
from pathlib import Path
import importlib.util,json,numpy as np,sys
sys.dont_write_bytecode=True
ROOT=Path(r'C:\work\SVALBARD_BOREHOLE_REAL_DATA_20261003')
P=ROOT/'raw/active/core/classes/observationmodel.py'
s=importlib.util.spec_from_file_location('publisher_model',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Config:
    Nagents=5;flux_min=0;flux_max=10000;Ngrid=201;hor_grid_cell_size=1;ver_grid_cell_size=1;Zmin=0
    def get(self,k):return {'observations/mirror':True,'observations/ld_conc':0,'observations/ld_windspeed':.38,'observations/ld_winddirection':1,'observations/BC_std_conc':.15,'observations/BC_std_windspeed':.83,'observations/BC_std_winddirection':98,'methods/observationmodel':3}[k]
mod=m.VergassolaConcentrationModel(Config())
r=np.random.default_rng(200103)
east=r.uniform(-50,50,5);north=r.uniform(-50,50,5);z=r.uniform(2,6,5)
U=.7;V=-1.1;speed=np.hypot(U,V);phi=(180+np.rad2deg(np.arctan2(U,V)))%360
states=np.zeros((8,7));states[0]=r.uniform(100,3000,7);states[1]=r.uniform(-20,20,7);states[2]=r.uniform(-20,20,7);states[4]=speed;states[5]=phi;states[6]=1;states[7]=2.09
agents=np.column_stack([-north,east,z]);a=mod._get_mu(agents,states)[:5]
dx=east[:,None]-states[2][None,:];dy=north[:,None]+states[1][None,:]
dist=np.sqrt(dx*dx+dy*dy+z[:,None]**2)
conv=8.314*273.95/(102000*16.04)*1e6/3600
b=2.09+2*conv*states[0][None,:]/(4*np.pi*dist)*np.exp(-dist*np.sqrt(1/286977600+speed**2/4)+(dx*U+dy*V)/2)
err=float(np.max(np.abs(a-b)));assert np.allclose(a,b,rtol=1e-12,atol=1e-12)
out=Path(r'C:\work\LAKESHORE_OBSERVABILITY_EXEC_20261003\evidence\public_data_first_20261003\van_hove\FORWARD_PARITY.json')
out.write_text(json.dumps(dict(pass_=True,max_abs_error_ppm=err,publisher_coordinates='x=-north,y=east',vector_consistent_phi='(180+atan2(U,V) in degrees)%360',publisher_preprocessor_phi='(180-atan2(U,V) in degrees)%360',n_comparisons=35),indent=2))
