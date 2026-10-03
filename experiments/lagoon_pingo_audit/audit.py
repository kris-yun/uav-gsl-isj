"""Stage A, source-evidence inventory, and track geometry without invented wind/shore labels."""
import sys,json,re,hashlib
from pathlib import Path
ROOT=Path(r'C:\work\LAGOON_PINGO_REAL_DATA_20261003');sys.path.insert(0,str(ROOT/'tools/python_deps'))
import numpy as np,pandas as pd,xarray as xr,openpyxl
from pyproj import Transformer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
def safe(x):
 if isinstance(x,dict):return {k:safe(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [safe(v) for v in x]
 if isinstance(x,np.ndarray):return safe(x.tolist())
 if isinstance(x,np.generic):return safe(x.item())
 if isinstance(x,bytes):return x.decode('utf8','replace')
 return x
def write(n,x):(ROOT/'audit'/n).write_text(json.dumps(safe(x),indent=2,allow_nan=False)+'\n',encoding='utf8')
def episodes(t,mask):
 idx=np.flatnonzero(mask)
 if not len(idx):return 0.,0
 delta=np.median(np.diff(t))
 lengths=np.split(idx,np.flatnonzero(np.diff(idx)>1)+1)
 return sum(float(t[g[-1]]-t[g[0]]+delta) for g in lengths),len(lengths)
def rate(t,mask):
 v=t[mask];delta=np.diff(v);delta=delta[delta>0]
 return (float(np.median(delta)),float(1/np.median(delta)),float(delta.max())) if len(delta) else (None,None,None)
def main():
 ds=xr.open_dataset(ROOT/'raw/svalbard_merged.nc',engine='h5netcdf')
 t=ds.tfs.values.astype('timedelta64[ns]').astype('int64')/1e9;assert np.all(np.diff(t)>0)
 schema={'dimensions':dict(ds.sizes),'attrs':safe(dict(ds.attrs)),'variables':{k:{'dims':list(v.dims),'shape':list(v.shape),'dtype':str(v.dtype),'attrs':safe(dict(v.attrs))} for k,v in ds.variables.items()}}
 write('DATA_SCHEMA.json',schema)
 dictionary=[];miss=[]
 for k,v in ds.variables.items():
  dictionary.append({'variable':k,'dimensions':'|'.join(v.dims),'dtype':str(v.dtype),'units_attribute':str(v.attrs.get('units','')),'attrs_json':json.dumps(safe(dict(v.attrs)),ensure_ascii=False)})
  a=v.values
  if np.issubdtype(a.dtype,np.number):finite=np.isfinite(a)
  elif np.issubdtype(a.dtype,np.datetime64) or np.issubdtype(a.dtype,np.timedelta64):finite=~pd.isna(a)
  else:finite=~pd.isna(a)
  miss.append({'variable':k,'axis':'all_rectangle','index':-1,'total_slots':a.size,'present':int(finite.sum()),'missing_fraction':float(1-finite.mean())})
  if a.ndim==2:
   for f in range(a.shape[0]):miss.append({'variable':k,'axis':v.dims[0],'index':f,'total_slots':a.shape[1],'present':int(finite[f].sum()),'missing_fraction':float(1-finite[f].mean())})
 pd.DataFrame(dictionary).to_csv(ROOT/'audit/VARIABLE_DICTIONARY.csv',index=False);pd.DataFrame(miss).to_csv(ROOT/'audit/MISSINGNESS.csv',index=False)
 transformer=Transformer.from_crs('EPSG:4326','EPSG:32633',always_xy=True)
 flight=[];rates=[];tracks=[];sync=[];pair=[]
 ch4=ds['CH4 (ppm)'].values;wind=np.stack([ds[x].values for x in ['U','V','W']],2);corr=np.stack([ds[x].values for x in ['ucorr','vcorr','wcorr']],2)
 for f in range(13):
  c=np.isfinite(ch4[f]);raw=np.isfinite(wind[f]).all(1);corrected=np.isfinite(corr[f]).all(1);dt=ds.datetime.values[f];dated=~pd.isna(dt)
  osd=np.isfinite(ds['OSD.latitude'].values[f])&np.isfinite(ds['OSD.longitude'].values[f]); rt=np.isfinite(ds['RTK.aircraftLatitude'].values[f])&np.isfinite(ds['RTK.aircraftLongitude'].values[f])&(ds['RTK.aircraftLatitude'].values[f]>70)&(ds['RTK.aircraftLatitude'].values[f]<90)&(ds['RTK.aircraftLongitude'].values[f]>0)&(ds['RTK.aircraftLongitude'].values[f]<40);gps=np.where(rt,ds['RTK.aircraftLatitude'].values[f],ds['OSD.latitude'].values[f]);lon=np.where(rt,ds['RTK.aircraftLongitude'].values[f],ds['OSD.longitude'].values[f]);pos=np.isfinite(gps)&np.isfinite(lon)&(gps>70)&(gps<90)&(lon>0)&(lon<40)
  active=c|raw|osd|dated;core=c&raw&pos&dated;corr_assumed=c&corrected&pos&dated
  active_time,_=episodes(t,active);rawtime,rawsegments=episodes(t,core);candidate_time,_=episodes(t,corr_assumed)
  tt=dt[dated];dated_unique=np.unique(tt);delta=np.diff(dated_unique).astype('timedelta64[ns]').astype('int64')/1e9
  row=dict(flight_index=f,flight_id=f'flight_index_{f:02d}',flight_axis='flight (no labels)',sensorsetup=int(ds.sensorsetup.values[f]),flightpattern=int(ds.flightpattern.values[f]),first_datetime=str(tt.min()) if len(tt) else None,last_datetime=str(tt.max()) if len(tt) else None,timezone='unspecified in file',elapsed_datetime_s=float((tt.max()-tt.min())/np.timedelta64(1,'s')) if len(tt) else None,active_grid_duration_s=active_time,ch4_samples=int(c.sum()),raw_uvw_samples=int(raw.sum()),corrected_axis_same_index_samples=int(corrected.sum()),joint_raw_ch4_gps_timestamp_samples=int(core.sum()),joint_raw_ch4_gps_timestamp_duration_s=rawtime,joint_raw_contiguous_segments=rawsegments,joint_corrected_assumed_same_index_samples=int(corr_assumed.sum()),joint_corrected_assumed_duration_s=candidate_time,corrected_joint_status='ASSUMED_ROW_MAPPING_NOT_VERIFIED',datetime_duplicate_count=int(len(tt)-len(dated_unique)),ch4_min_ppm=float(ch4[f,c].min()) if c.any() else None,ch4_max_ppm=float(ch4[f,c].max()) if c.any() else None,lat_min=float(gps[pos].min()) if pos.any() else None,lat_max=float(gps[pos].max()) if pos.any() else None,lon_min=float(lon[pos].min()) if pos.any() else None,lon_max=float(lon[pos].max()) if pos.any() else None)
  flight.append(row)
  row['joint_raw_exact_grid_slot_measure_s']=row.pop('joint_raw_ch4_gps_timestamp_duration_s')
  row['corrected_assumed_exact_grid_slot_measure_s']=row.pop('joint_corrected_assumed_duration_s')
  row['exact_grid_slot_measure_warning']='CH4 is sparse on20Hz union grid; summing50ms slots is NOT observed-flight duration'
  row['ch4_median_present_dt_s']=rate(t,c)[0]
  joint_t=t[core];row['joint_raw_endpoint_span_s']=float(joint_t[-1]-joint_t[0]) if len(joint_t)>1 else None
  for label,mask in [('CH4_present',c),('raw_UVW_present',raw),('corrected_UVW_same_ordinal_present',corrected),('position_present',pos),('joint_raw',core)]:
   md,hz,maxgap=rate(t,mask);rates.append(dict(flight_index=f,stream=label,present_count=int(mask.sum()),median_present_grid_dt_s=md,grid_presence_hz=hz,max_gap_s=maxgap,not_native_sensor_rate=True))
  for timestamp in ['datetime','Time','Time Stamp']:
   values=ds[timestamp].values[f];good=~pd.isna(values);v=values[good];u=np.unique(v);diff=np.diff(u).astype('timedelta64[ns]').astype('int64')/1e9
   rates.append(dict(flight_index=f,stream=timestamp+'_unique_timestamp',present_count=int(good.sum()),unique_count=len(u),median_unique_timestamp_dt_s=float(np.median(diff[diff>0])) if (diff>0).any() else None,duplicate_count=int(len(v)-len(u)),timezone='unspecified'))
   jointly=good&dated;offset=(values[jointly]-dt[jointly]).astype('timedelta64[ns]').astype('int64')/1e9
   if len(offset):sync.append(dict(flight_index=f,timestamp=timestamp,paired_slots=len(offset),median_minus_datetime_s=float(np.median(offset)),p05_minus_datetime_s=float(np.quantile(offset,.05)),p95_minus_datetime_s=float(np.quantile(offset,.95)),comment='remaining stored timestamp differences; not inferred physical sensor delay'))
  idx=np.flatnonzero(pos);xx,yy=transformer.transform(lon[idx],gps[idx]);storedx=ds['UTM.easting'].values[f,idx];storedy=ds['UTM.northing'].values[f,idx];valid=np.isfinite(storedx)&np.isfinite(storedy)
  row['utm_vs_projected_median_difference_m']=float(np.median(np.hypot(xx[valid]-storedx[valid],yy[valid]-storedy[valid]))) if valid.any() else None
  tr=pd.DataFrame({'flight_index':f,'tfs_s':t[idx],'datetime':dt[idx],'x_utm33n_m':xx,'y_utm33n_m':yy,'longitude':lon[idx],'latitude':gps[idx],'position_source':np.where(rt[idx],'RTK','OSD'),'height_relative_home_m':ds['OSD.height [m]'].values[f,idx],'altitude_logged_m':ds['OSD.altitude [m]'].values[f,idx],'rtk_ellipsoidal_m':ds['RTK.aircraftEllipsoidalHeight [m]'].values[f,idx],'rtk_geoid_height_m':ds['RTK.aircraftGeoidHeight [m]'].values[f,idx],'ch4_ppm':ch4[f,idx],'u_raw':wind[f,idx,0],'v_raw':wind[f,idx,1],'w_raw':wind[f,idx,2],'joint_raw_sample':core[idx],'surface_context':'UNCLASSIFIED','d_shore_m':np.nan,'altitude_agl_m':np.nan})
  tracks.append(tr)
  for g in range(13):
   mask=np.isfinite(corr[g]).all(1)&raw
   pair.append(dict(flight_index=f,flight_frec_index=g,support_overlap_slots=int(mask.sum()),overlap_fraction_of_raw=float(mask.sum()/max(raw.sum(),1)),mapping_verified=False))
 pd.DataFrame(flight).to_csv(ROOT/'audit/FLIGHT_INVENTORY.csv',index=False);pd.DataFrame(rates).to_csv(ROOT/'audit/SAMPLING_RATE.csv',index=False);pd.DataFrame(sync).to_csv(ROOT/'audit/TIMESTAMP_DIFFERENCES.csv',index=False);pd.DataFrame(pair).to_csv(ROOT/'audit/FLIGHT_AXIS_OVERLAP.csv',index=False)
 combined=pd.concat(tracks,ignore_index=True);combined.to_csv(ROOT/'derived/SAMPLE_CONTEXT.csv.gz',index=False,compression='gzip')
 crossings=[dict(flight_index=f,water_samples=None,transition_samples=None,land_samples=None,crossings=None,status='NOT_ESTABLISHED_NO_VALIDATED_2024_SHORELINE') for f in range(13)];pd.DataFrame(crossings).to_csv(ROOT/'audit/SHORELINE_CROSSINGS.csv',index=False)
 # Independent spreadsheet records are inventoried, never converted to UAV-defined source truth.
 wb=openpyxl.load_workbook(ROOT/'raw/Dissolved_methane_floating_flux_chamber_ebullition.xlsx',read_only=True,data_only=True);cells=[];sheets=[]
 for sheet in wb:
  sheets.append(dict(sheet=sheet.title,rows=sheet.max_row,columns=sheet.max_column))
  for row in sheet:
   for cell in row:
    if cell.value is not None:cells.append(dict(sheet=sheet.title,cell=cell.coordinate,value=str(cell.value)))
 pd.DataFrame(cells).to_csv(ROOT/'audit/EXCEL_NONEMPTY_CELLS.csv',index=False);write('EXCEL_SHEET_INVENTORY.json',sheets)
 field=list(wb['Fieldnotes'].values);source=[]
 for rn,row in enumerate(field,1):
  if len(row)>=4 and isinstance(row[2],(float,int)) and isinstance(row[3],(float,int)) and 70<row[2]<90 and 0<row[3]<40:
   x,y=transformer.transform(row[3],row[2]);source.append(dict(site_id=row[0],description=row[1],latitude=row[2],longitude=row[3],date=str(row[4]),x_utm33n_m=x,y_utm33n_m=y,sheet='Fieldnotes',row=rn,coordinate_support='explicit fieldnotes coordinate',source_localization_truth=False))
 flux=list(wb['Pingo CH4 Calcs'].values);flux_byid={r[0]:r for r in flux[1:] if r[0] is not None}
 for r in source:
  match=flux_byid.get(r['site_id']);r['flux_new_umol_m2_s']=match[16] if match is not None else None;r['flux_mg_ch4_m2_h']=match[17] if match is not None else None
 pd.DataFrame(source).to_csv(ROOT/'audit/INDEPENDENT_SOURCE_EVIDENCE.csv',index=False)
 fig,axes=plt.subplots(4,4,figsize=(13,12));sx=np.array([r['x_utm33n_m'] for r in source]);sy=np.array([r['y_utm33n_m'] for r in source]);cx=float(np.median(combined.x_utm33n_m));cy=float(np.median(combined.y_utm33n_m))
 for f,ax in enumerate(axes.flat):
  if f>=13:ax.set_visible(False);continue
  tr=combined[combined.flight_index==f];good=np.isfinite(tr.ch4_ppm);ax.plot(tr.x_utm33n_m-cx,tr.y_utm33n_m-cy,color='grey',alpha=.4,linewidth=.6);ax.scatter(tr.loc[good,'x_utm33n_m']-cx,tr.loc[good,'y_utm33n_m']-cy,c=tr.loc[good,'ch4_ppm'],s=2,cmap='viridis');ax.scatter(sx-cx,sy-cy,c='red',marker='x',s=15);ax.set_title(f'Flight index {f}');ax.set_aspect('equal');ax.set_xlabel('UTM33N east offset (m)');ax.set_ylabel('North offset (m)')
 fig.suptitle('Published CH4 tracks and independent fieldnotes coordinates; surface unclassified');fig.tight_layout();fig.savefig(ROOT/'derived/UAV_TRACKS_BY_FLIGHT.png',dpi=130);plt.close(fig)
 fig,ax=plt.subplots(figsize=(9,8))
 for f,tr in combined.groupby('flight_index'):ax.plot(tr.x_utm33n_m-cx,tr.y_utm33n_m-cy,lw=.65,label=str(f))
 ax.scatter(sx-cx,sy-cy,c='black',marker='x',label='fieldnotes source evidence');ax.set_aspect('equal');ax.legend(fontsize=7,ncol=3);ax.set_xlabel('East offset (m)');ax.set_ylabel('North offset (m)');ax.set_title('Track-only site map; no water/land mask established');fig.tight_layout();fig.savefig(ROOT/'derived/SITE_MAP.png',dpi=160);plt.close(fig)
 unavailable={'url':'https://github.com/johanage/lagoon-pingo-analysis','result':'GitHub web404 and git clone repository not found during audit','impact':'published processing code unavailable; no wind coordinate/rotation/vehicle-motion/clock-offset contract could be inspected'};write('PROCESSING_CODE_AVAILABILITY.json',unavailable)
 summary={'decision':'REAL_LAGOON_HOLD','stage_A':'STOP_SYNC_AND_WIND_CONTRACT_NOT_VERIFIED','stage_B':'TRACKS_PROJECTED_CONTEXT_NOT_CLASSIFIED; no crossing/coverage conclusion','stage_C':'NOT_RUN_GATE_CLOSED','stage_D':'NOT_RUN_GATE_CLOSED','stage_E':'INDEPENDENT_COORDINATE_INVENTORY_ONLY','flight_rows':13,'variables':94,'tfs_slots':len(t),'median_shared_grid_dt_s':float(np.median(np.diff(t))),'shared_grid_hz':float(1/np.median(np.diff(t))),'file_attr_median_sampling_rate':safe(ds.attrs.get('median_sampling_rate')),'nominal_raw_ch4_wind_gps_timestamp_samples':int(sum(r['joint_raw_ch4_gps_timestamp_samples'] for r in flight)),'exact_raw_joint_grid_slot_measure_s_not_flight_duration':float(sum(r['joint_raw_exact_grid_slot_measure_s'] for r in flight)),'verified_corrected_ch4_joint_duration_s':None,'corrected_wind_axis':'flight_frec, no coordinate labels or explicit mapping to flight','wind_component_coordinate_convention':'NOT_DOCUMENTED','motion_correction':'ucorr/vcorr/wcorr present; transform and units/frame undocumented','timezone':'NOT_DOCUMENTED','sensor_lag':'NOT_DOCUMENTED','independent_explicit_coordinate_sites':len(source),'water_transition_land_counts':None,'shoreline_crossings':None,'no_new_gaden_cfd_training_or_closed_loop':True,'reason':'corrected wind pairing and physical synchronization/convention remain unverified; unknown quality is HOLD, not proven unusability FAIL; stop before inference'}
 write('FINAL_DECISION.json',summary)
 description=['# Lagoon Pingo 数据与同步审计','', '**REAL_LAGOON_HOLD**：两个核心原始文件完整下载并通过官方MD5校验；按Stage A的STOP规则暂停后续机制与预测分析。','',f'NetCDF：13个flight行、独立的13个flight_frec行、55,747个共享tfs格点，94个数据变量。共享网格间隔约{summary["median_shared_grid_dt_s"]:.3f}s（约{summary["shared_grid_hz"]:.1f}Hz），属性median_sampling_rate=1不能直接解释为各传感器原生采样频率。请看SAMPLING_RATE.csv，分别列网格非空点间隔和各时间变量的唯一时间戳间隔。','', f'名义同flight行的CH4+未修正U/V/W+位置+datetime交集为{summary["nominal_raw_ch4_wind_gps_timestamp_samples"]:,}个观测格点；CH4在20Hz共享格点上是稀疏数据，不能把每个观测乘0.05s当飞行或同步持续时间。逐flight的时间端点跨度、CH4非空点间隔和格点占据量分别报告，后者仅用于数据结构QA。修正风ucorr/vcorr/wcorr在flight_frec轴，文件未提供与flight轴的标签映射，因此真正通过审计的修正CH4+3D wind时长为“未建立”，不能用同一ordinal行号自动认定。','', 'flight/flight_frec均是没有坐标值的维度。FLIGHT_INVENTORY.csv使用明确的ordinal索引，不伪造发布方架次编号。架次绝对时间范围来自datetime非NaT值；timezone未声明，不擅自标UTC。共同网格重复次数、timestamp数及Time/Time Stamp相对datetime的差值已输出；这些差值不能自动当作已知传感器响应延迟。','', 'U/V/W和ucorr/vcorr/wcorr无单位及坐标系属性，未说明ENU/NED/机体系、yaw旋转、无人机运动修正和传感器延迟补偿。文件提供vx_computed/vy_computed等名称，但名称不是算法或校准证据。官方Zenodo元数据说明已处理同步；其给出的处理代码链接目前web404/git repository not found，无法核查具体契约。保留发布方声明，但不把声明当作独立时间/坐标校准证明。','', 'Time与datetime的中位差在flight0约0.03s、flight1约56.739s、flight2约60.975s。它们可能是原始时钟差而已经在tfs中被补偿，也可能尚未补偿；缺少处理代码不能判定。不能简单把这些差值称为实际残留同步误差，更不能直接做基于物理lag的推断。','', '## 空间与水陆几何','', '位置优先有效范围内RTK，否则OSD，按WGS84经纬度投影至EPSG:32633。原文件UTM zone33/letterX与此一致，另报告与原UTM列的差值；WGS84基准来自DJI位置类型推定，文件未单独声明完整CRS定义。OSD.height为相对起飞参考高度，不等于各航迹点的地面以上高度。未使用DEM，因此AGL保持NaN。','', '已输出全部有位置样本的SAMPLE_CONTEXT.csv.gz与UAV_TRACKS_BY_FLIGHT.png、SITE_MAP.png。surface_context=UNCLASSIFIED，d_shore=NaN，crossings=未知；没有把未知填成0或把轨迹形状猜成岸线。','', '官方2024年8月影像在Zenodo中可用，元数据已保存，尚未建立经过视觉QC的2024水陆mask。首阶段按协议仅下载两个核心数据文件。旧DataverseNO DOI10.18710/IMPEG8的README明确是May2020春末存在icings，不能直接作为2024夏季water/land真值。由于Stage A门未过，未继续下载大影像或构造岸线机制证据。','', '## 独立源证据','', f'Excel有5张表；Fieldnotes中找到{len(source)}个显式经纬度记录，已投影并按site_id关联可匹配的chamber flux缓存值。Excel原文件未改动。其他仅有沿transect距离的点不擅自补坐标。Fieldnotes还提示display time可能与真实时间相差约10min，且ebullition样本注明2024-09-13；它们可以作为有限空间evasion证据，但不能当同期、精确点源定位真值。未使用UAV CH4定义源区，不运行源posterior评价。','', '## Stage C/D处理','', 'CH4 ACF/whiff/blank、current-versus-history、water/transition/land history gain均NOT_RUN_GATE_CLOSED，不报告伪数值。没有以不明风轴和传感器同步假设训练预测器。缺少可核查契约是证据HOLD；当前没有证明数据本身不可用，不判REAL_LAGOON_FAIL。','', '解锁需要：发布方flight↔flight_frec映射、风分量框架与运动修正/单位说明、时钟/lag/时区说明或可访问的处理代码。确认同步和wind契约后再以2024影像建立水陆mask、signed d_shore、crossings，然后按预定整flight留出做后续统计。','', '来源：[Zenodo](https://zenodo.org/records/19597182)；[旧几何数据](https://doi.org/10.18710/IMPEG8)。原始SHA256见metadata/SHA256SUMS.txt。']
 (ROOT/'audit/DATA_SCHEMA.md').write_text('\n'.join(description)+'\n',encoding='utf8');(ROOT/'reports/REPORT_zh.md').write_text('\n'.join(description)+'\n',encoding='utf8')
 print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':main()
