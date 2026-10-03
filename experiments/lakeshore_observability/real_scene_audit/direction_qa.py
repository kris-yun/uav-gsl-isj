"""Post-analysis diagnostic; no alteration of the core UV-derived wind estimator."""
import pathlib,os,numpy as np,pandas as pd,xarray as xr
ROOT=pathlib.Path(__file__).resolve().parents[3]
OUT=ROOT/'evidence/wiscodisco_real_scene_feature_audit_20261003'
DATA=pathlib.Path(os.environ.get('WISCO_DATA_ROOT','C:/work/LAKESHORE_GSL_DATA_20261002/data_external'))
rows=[]
for p in sorted((DATA/'B_WiscoDISCO21_RAAVEN/raw').glob('*.nc')):
 with xr.open_dataset(p,decode_times=False) as d:
  angle=(270-np.rad2deg(np.arctan2(d.northward_wind.values,d.eastward_wind.values)))%360
  good=(d.wind_flag.values==0)&(np.hypot(d.eastward_wind.values,d.northward_wind.values)>=.5)
  diff=abs((angle-d.wind_direction.values+180)%360-180);q=diff[good]
  rows.append(dict(file=p.name,n_good=int(good.sum()),n_difference_gt1deg=int((q>1).sum()),fraction_gt1deg=float((q>1).mean()),median_difference_deg=float(np.nanmedian(q)),maximum_difference_deg=float(np.nanmax(q)),audit_direction_from_uv=True))
pd.DataFrame(rows).to_csv(OUT/'RAAVEN_UV_vs_published_direction_QA.csv',index=False)
