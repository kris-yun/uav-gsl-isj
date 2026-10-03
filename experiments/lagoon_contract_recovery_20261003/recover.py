"""Recover exact file lineage without source coordinates or localization fitting.

This proves record identity, not physical synchronization or wind calibration.
"""
import argparse
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np
import pandas as pd


def identities(merged, original, keys):
    lookup = {}
    arrays = [original[k][:] for k in keys]
    for j in range(arrays[0].shape[0]):
        a = np.stack([x[j] for x in arrays], axis=1)
        for row in a[np.all(np.isfinite(a), axis=1)]:
            lookup.setdefault(tuple(row), set()).add(j)
    result = []
    for i in range(13):
        a = np.stack([merged[k][i] for k in keys], axis=1)
        a = a[np.all(np.isfinite(a), axis=1)]
        hits = [lookup.get(tuple(row), set()) for row in a]
        candidates = set.intersection(*hits) if hits else set()
        result.append(dict(flight=i, records=len(a), unmatched=sum(not x for x in hits),
                           unique_original_row=next(iter(candidates)) if len(candidates) == 1 else None))
    return result


def run(root, out):
    out.mkdir(parents=True, exist_ok=True)
    paths = [root/'raw/svalbard_merged.nc'] + sorted(
        (root/'unlock_20261003/raw_sensor_contract_inputs').glob('*.nc'))
    manifest = [{'path':str(p), 'bytes':p.stat().st_size,
                 'sha256':hashlib.file_digest(p.open('rb'), 'sha256').hexdigest()} for p in paths]
    m = h5py.File(paths[0])
    originals = {p.name:h5py.File(p) for p in paths[1:]}
    sonic = originals['svalbard_trisonica_corrected_split_flights.nc']
    sonic_rows = []
    for i in range(13):
        matches = [j for j in range(13) if all(np.array_equal(m[k][i], sonic[k][j], equal_nan=True)
                                               for k in ['U','V','W','Time'])]
        assert len(matches) == 1
        sonic_rows.append(matches[0])
    gps = identities(m, originals['svalbard_flightrecords.nc'],
                     ['OSD.latitude','OSD.longitude','OSD.height [m]','OSD.yaw'])
    gas = identities(m, originals['svalbard_aeris_all_flights.nc'],
                     ['CH4 (ppm)','H2O (ppm)','Latitude','Longitude'])
    velocities = np.stack([m['vx_computed'][:],m['vy_computed'][:]],axis=-1)
    matrix = []
    mapping = []
    for i in range(13):
        coords = np.stack([m['UTM.easting'][i],m['UTM.northing'][i]],axis=-1)
        clock = m['datetime'][i].astype(np.float64)/1e9
        ix = np.flatnonzero(np.all(np.isfinite(coords),axis=1))
        predicted = np.diff(coords[ix],axis=0)/np.diff(clock[ix])[:,None]
        estimates = []
        for j in range(13):
            target = velocities[j,ix[:-1]]
            ok = np.all(np.isfinite(target)&np.isfinite(predicted),axis=1)
            delta = predicted[ok]-target[ok]
            rmse = float(np.sqrt(np.mean(delta**2)))
            row = dict(flight=i,flight_frec=j,n=int(ok.sum()),rmse_m_s=rmse,
                       max_abs_m_s=float(np.max(abs(delta))))
            matrix.append(row); estimates.append(row)
        ordered = sorted(estimates,key=lambda r:r['rmse_m_s'])
        best = ordered[0]
        assert best['max_abs_m_s'] < 1e-6 and ordered[1]['rmse_m_s'] > 0.1
        assert gps[i]['unmatched'] == gas[i]['unmatched'] == 0
        mapping.append(dict(flight=i,flight_frec=best['flight_frec'],
                            sonic_row=sonic_rows[i],gps_original_row=gps[i]['unique_original_row'],
                            aeris_session_row=gas[i]['unique_original_row'],
                            gps_records=gps[i]['records'],gas_records=gas[i]['records'],
                            derivative_records=best['n'],derivative_max_abs_m_s=best['max_abs_m_s'],
                            second_best_rmse_m_s=ordered[1]['rmse_m_s']))
    pd.DataFrame(mapping).to_csv(out/'EXACT_RECORD_MAPPING.csv',index=False)
    pd.DataFrame(matrix).to_csv(out/'VELOCITY_MAPPING_ALL_169_PAIRS.csv',index=False)
    # Export localization inputs by the proved dimension join. No physical lag
    # correction is inferred, and nearest-row gaps remain explicit for callers.
    samples=[]
    tfs=m['tfs'][:]*0.001
    for row in mapping:
        i,j=row['flight'],row['flight_frec']
        gas_values=m['CH4 (ppm)'][i]
        winds=np.stack([m[k][j] for k in ['ucorr','vcorr','wcorr']],axis=-1)
        wi=np.flatnonzero(np.all(np.isfinite(winds),axis=1))
        gps_values=np.stack([m[k][i] for k in ['UTM.easting','UTM.northing','OSD.height [m]']],axis=-1)
        pi=np.flatnonzero(np.all(np.isfinite(gps_values),axis=1))
        for k in np.flatnonzero(np.isfinite(gas_values)):
            w=wi[np.argmin(abs(tfs[wi]-tfs[k]))]
            q=pi[np.argmin(abs(tfs[pi]-tfs[k]))]
            samples.append(dict(flight=i,flight_frec=j,tfs_s=tfs[k],ch4_ppm=gas_values[k],
                                easting_m=gps_values[q,0],northing_m=gps_values[q,1],height_m=gps_values[q,2],
                                ucorr_as_published=winds[w,0],vcorr_as_published=winds[w,1],wcorr_as_published=winds[w,2],
                                gps_grid_offset_s=tfs[q]-tfs[k],wind_grid_offset_s=tfs[w]-tfs[k],
                                physical_wind_and_lag_verified=False))
    pd.DataFrame(samples).to_csv(out/'LOCALIZATION_INPUT_CANDIDATES_NOT_PHYSICALLY_VERIFIED.csv',index=False)
    result = dict(decision='RECORD_LINEAGE_UNLOCKED_PHYSICAL_WIND_AND_LAG_UNRESOLVED',
                  evidence='exact multichannel record identity and independent GPS derivative reconstruction',
                  mapping_basis='No ordinal pairing; all 169 flight/flight_frec pairs evaluated.',
                  mapping=mapping,raw_file_manifest=manifest,
                  limitations=['Wind coordinate frame and publisher correction formula remain unverified.',
                               'Matching record lineage does not verify physical sensor lag or publisher clock adjustment.',
                               'Seven Excel flux/evasion sites are not established unique point-source truth.',
                               'GPS-derived velocities contain large spikes and must not be substituted for platform velocity.'])
    (out/'RECOVERY_RESULT.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    for f in originals.values(): f.close()
    m.close()
    print(json.dumps(dict(decision=result['decision'],flights=len(mapping),gps_records=sum(x['gps_records'] for x in mapping),
                          gas_records=sum(x['gas_records'] for x in mapping),
                          max_derivative_error=max(x['derivative_max_abs_m_s'] for x in mapping))))


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();run(a.root,a.out)
