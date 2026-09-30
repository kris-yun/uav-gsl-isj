"""Official-semantic event adapter. No simulation, oracle plume or truth inputs."""
import ast,json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation as R

UP=Path(__file__).resolve().parents[2]/'Topography-aware-Gas-Source-Localization-lfs'

def official_functions():
    notebook=json.loads((UP/'train/GSLInference.ipynb').read_text(encoding='utf-8'))
    code=''.join(notebook['cells'][3]['source'])
    keep={'convert_coordinates','sensor_direction_in_world','mark_wind_direction'}
    nodes=[n for n in ast.parse(code).body if isinstance(n,ast.FunctionDef) and n.name in keep]
    assert {n.name for n in nodes}==keep
    namespace={'np':np,'R':R}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'<official-input-functions>','exec'),namespace)
    return namespace

def channels(occupancy,resolution,origin,observed_events,budget_s=300.):
    """Caller must supply verified official-angle semantics from actual local wind logs.

    Each event has timestamp_s, x, y, encounter, event_id, quaternion_xyzw and
    official_wind_clockwise_deg (or None for the upstream no-wind sentinel).
    No source labels, concentrations at unvisited cells, or full wind field.
    """
    occupancy=np.asarray(occupancy,np.float32)
    assert occupancy.ndim==2 and np.isfinite(occupancy).all()
    h,w=occupancy.shape
    assert h<=279 and w<=279 and resolution>0
    assert set(origin)=={'x','y'}
    # Official inference pads maps with zero; official training uses -1.
    map_channel=np.pad(occupancy,((0,279-h),(0,279-w)),constant_values=0)
    wind=np.zeros((279,279));encounter=np.zeros((279,279),dtype=int)
    functions=official_functions();ids=set();used=[]
    for event in sorted(observed_events,key=lambda e:(e['timestamp_s'],e['event_id'])):
        if event['timestamp_s']>budget_s:continue
        assert event['timestamp_s']>=0 and event['event_id'] not in ids
        ids.add(event['event_id'])
        assert set(event)=={'timestamp_s','x','y','encounter','event_id','quaternion_xyzw','official_wind_clockwise_deg'}
        assert isinstance(event['encounter'],(bool,np.bool_))
        if not event['encounter']:continue
        ix,iy=functions['convert_coordinates'](event['x'],event['y'],resolution,origin)
        assert 0<=ix<w and 0<=iy<h,('observed encounter outside map',event['event_id'])
        encounter[iy,ix]=1
        degrees=event['official_wind_clockwise_deg']
        if degrees is not None:
            q=event['quaternion_xyzw'];assert len(q)==4 and np.isfinite(q).all()
            yaw=functions['sensor_direction_in_world'](*q,-np.radians(int(degrees)))
            raster=np.zeros((279,279));raster[iy,ix]=1
            wind+=functions['mark_wind_direction'](raster,yaw)
        used.append(event['event_id'])
    return np.stack([map_channel,wind,encounter],axis=0).astype(np.float32),dict(
        budget_s=budget_s,encounter_events_used=used,visited_positive_pixels=int(encounter.sum()),
        channels=['official occupancy map','cumulative encounter-local wind halfplanes','binary encountered locations'],
        shape=[3,279,279],oracle_inputs=False,wind_semantics_must_be_verified=True)

def location(output,resolution,origin,height,width):
    """Paper's probability-weighted centroid; unnormalized sigmoid is not a posterior."""
    p=np.asarray(output,dtype=np.float64)[:height,:width]
    assert p.shape==(height,width) and np.isfinite(p).all() and (p>=0).all() and (p<=1).all()
    yy,xx=np.indices(p.shape);total=float(p.sum())
    if total<=0:raise ValueError('No finite source estimate: output has zero mass')
    cy=float(origin['y']+resolution*np.sum(p*yy)/total)
    cx=float(origin['x']+resolution*np.sum(p*xx)/total)
    i,j=np.unravel_index(int(np.argmax(p)),p.shape)
    return dict(centroid_xy=[cx,cy],peak_xy=[float(origin['x']+resolution*j),float(origin['y']+resolution*i)],
                peak_probability=float(p[i,j]),source_location_rule='paper probability-weighted centroid')

def smoke():
    occupancy=np.zeros((40,60),np.float32);occupancy[5:10,20:25]=100
    e=dict(timestamp_s=100.,x=1.,y=.5,encounter=True,event_id='observed-1',
           quaternion_xyzw=[0.,0.,0.,1.],official_wind_clockwise_deg=90)
    late=dict(e,timestamp_s=301.,event_id='after-budget',x=1.5)
    out,meta=channels(occupancy,.05,{'x':0.,'y':0.},[e,late])
    assert meta['encounter_events_used']==['observed-1'] and out[2].sum()==1
    # Exact parity with the original function, including atan/angle conventions.
    f=official_functions();raster=np.zeros((279,279));raster[10,20]=1
    yaw=f['sensor_direction_in_world'](0.,0.,0.,1.,-np.radians(90))
    assert np.array_equal(out[1],f['mark_wind_direction'](raster,yaw).astype(np.float32))
    assert np.all(out[0,:40,:60]==occupancy)
    try:channels(occupancy,.05,{'x':0.,'y':0.},[dict(e,true_source_x=9.)])
    except AssertionError:pass
    else:raise AssertionError('truth must not be an action/inference input')
    assert out[2,30,30]==0,'unvisited space stays empty'
    return dict(decision='VGR_ADAPTER_SOFTWARE_SMOKE_PASS',official_wind_raster_byte_parity=True,
                after_300s_rejected=True,truth_input_rejected=True,unvisited_encounter_not_filled=True,
                real_vgr_data_evaluated=False)

if __name__=='__main__':
    out=Path(__file__).resolve().parents[1]/'results/VGR_ADAPTER_SOFTWARE_SMOKE.json'
    out.write_text(json.dumps(smoke(),indent=2,sort_keys=True)+'\n')
    print('VGR_ADAPTER_SOFTWARE_SMOKE_PASS')
