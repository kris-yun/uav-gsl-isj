"""Frozen-observation analysis of the six captured 2D candidates; no forward execution."""
import sys
sys.dont_write_bytecode=True
import argparse,csv,json,math
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
import verify_m0_portable as portable

def rows(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def js(path):return json.loads(path.read_text(encoding='utf-8'))
def analyse(root):
    m0=root/'frozen_M0';module=portable.load_m0(m0)
    native=m0/'evidence/runtime/updates/update_2';meta=js(native/'metadata.json')
    input_rows=rows(native/'input.csv');n=len(input_rows);width=meta['width']
    free=np.array([r['occupancy']=='1' for r in input_rows]);indices=np.flatnonzero(free)
    xy=np.column_stack([meta['origin_x']+(np.arange(n)%width+.5)*.25,
                        meta['origin_y']+(np.arange(n)//width+.5)*.25])
    measured=1-1/(1+np.exp([float(r['logOdds']) for r in input_rows]))
    confidence=np.array([float(r['confidence']) for r in input_rows])
    _,stops=module.measure_events(m0/'evidence');direct=np.zeros(n,dtype=bool)
    for stop in stops:
        i,j=((np.array([stop['x'],stop['y']])-[meta['origin_x'],meta['origin_y']])/.25).astype(int)
        direct[i+j*width]=True
    band=(xy[:,1]>=1.7)&(xy[:,1]<=2.7)
    maps={};factors={};scores={};job_results={};score_rows=[]
    budget=js(root/'M1_A_FROZEN_FORWARD_BUDGET.json')
    maximum_error=0.
    for job in budget['jobs']:
        name=job['job'];folder=root/'evidence/forwards'/name
        record=js(folder/'RESULT.json');candidate=rows(folder/'candidates.csv')[0]
        hit=np.frombuffer((folder/candidate['map_file']).read_bytes(),dtype='<f4')
        factor=module.factors(measured,hit,confidence)
        with localcontext() as ctx:
            ctx.prec=60;product=Decimal(1)
            for value in factor[free]:product*=Decimal.from_float(float(value))
            native_score=Decimal(candidate['score']);relative=abs(product-native_score)/native_score
        assert float(relative)<5e-12,(name,relative)
        maximum_error=max(maximum_error,float(relative))
        assert np.all(np.isfinite(factor)) and np.all(factor>0)
        maps[name]=hit;factors[name]=factor;scores[name]=float(product);job_results[name]=record
        score_rows.append(dict(job=name,bundle=job['bundle'],source_kind=job['kind'],
                               origin_i=job['origin_i'],origin_j=job['origin_j'],size_i=job['size_i'],size_j=job['size_j'],
                               source_area_m2=job['size_i']*job['size_j']*.25*.25,
                               native_score=record['score'],decimal_recomputed_score=float(product),
                               relative_difference=float(relative),rng_before=record['rng_before'],rng_after=record['rng_after'],
                               gaussian_index_before=record['gaussian_index_before'],gaussian_index_after=record['gaussian_index_after'],
                               release_points=record['release_points']))
    pairs=[('T_TRUE_FINE_VS_COARSE','anchor_T_coarse','T_true_fine'),
           ('W_TRUE_FINE_VS_COARSE','W_true_coarse','W_true_fine'),
           ('T_WRONG_FINE_VS_TRUE_FINE','T_true_fine','T_wrong_fine'),
           ('W_WRONG_FINE_VS_TRUE_FINE','W_true_fine','anchor_W_fine')]
    cell_rows=[];region_rows=[];pair_checks=[]
    for label,a,b in pairs:
        delta=np.log(factors[b])-np.log(factors[a]);net=math.fsum(float(v) for v in delta[free])
        assert math.isclose(math.exp(net),scores[b]/scores[a],rel_tol=5e-12)
        for index in indices:
            cell_rows.append(dict(comparison=label,cell_index=int(index),grid_i=int(index%width),grid_j=int(index//width),
                                  x=float(xy[index,0]),y=float(xy[index,1]),measured_probability=float(measured[index]),
                                  confidence=float(confidence[index]),first_hit=float(maps[a][index]),second_hit=float(maps[b][index]),
                                  first_factor=float(factors[a][index]),second_factor=float(factors[b][index]),
                                  delta_log_second_over_first=float(delta[index]),direct_stop=bool(direct[index]),preset_y_band=bool(band[index])))
        for region,mask in [('ALL_447',free),('PRESET_Y_BAND',free&band),('OUTSIDE_Y_BAND',free&~band),
                            ('DIRECT_10',free&direct),('OTHER_437',free&~direct)]:
            part=math.fsum(float(v) for v in delta[mask])
            region_rows.append(dict(comparison=label,region=region,cells=int(mask.sum()),net_log_score_difference=part,
                                    second_over_first_score_ratio=math.exp(part),fraction_of_total_net_log_difference=part/net))
        pair_checks.append(dict(comparison=label,net_log_score_difference=net,second_over_first_score_ratio=math.exp(net)))
    bundles=[]
    for bundle,coarse,fine,wrong in [('T','anchor_T_coarse','T_true_fine','T_wrong_fine'),
                                    ('W','W_true_coarse','W_true_fine','anchor_W_fine')]:
        bundles.append(dict(bundle=bundle,true_coarse_score=scores[coarse],true_fine_score=scores[fine],wrong_fine_score=scores[wrong],
                            true_fine_over_coarse=scores[fine]/scores[coarse],
                            wrong_fine_over_true_coarse=scores[wrong]/scores[coarse],
                            wrong_fine_over_true_fine=scores[wrong]/scores[fine],
                            unified_source_area_m2=.0625,
                            scope='Same initial RNG/phase, not event-keyed common noise or independent physical sample'))
    masks=[]
    for bundle,true,wrong in [('T','T_true_fine','T_wrong_fine'),('W','W_true_fine','anchor_W_fine')]:
        for name,mask in [('ALL_447',free),('EXCLUDE_PRESET_Y_BAND',free&~band),('DIRECT_10',free&direct),('OTHER_437',free&~direct)]:
            log_ratio=math.fsum(float(v) for v in (np.log(factors[wrong])-np.log(factors[true]))[mask])
            masks.append(dict(bundle=bundle,mask=name,cells=int(mask.sum()),wrong_fine_over_true_fine=math.exp(log_ratio),
                              scope='Posthoc conditional score mask only; no posterior or localization outcome'))
    result=dict(verdict='M1_A_NATIVE_ANCHORS_PASS_FAIR_1X1_WRONG_PREFERENCE_PERSISTS',
                budgeted_forward_calls=6,actual_forward_calls=6,posterior_updates=0,navigation_goals=0,new_3D_realizations=0,
                independent_physical_samples_added=0,source_exact_coordinate_oracle_calls=0,
                scalar_verification_maximum_relative_difference=maximum_error,bundles=bundles,
                source_representation_decision='5x1 versus 1x1 area mismatch does not explain the wrong-source preference in this snapshot and these two recorded states',
                physical_cause='HOLD: distinguish evidence dependence, observability, stochastic prediction and 2D/3D transport using a separately approved reference',
                paired_masks=masks,pair_checks=pair_checks)
    return result,score_rows,cell_rows,region_rows

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--write-derived',action='store_true',help='Write NEW derivative outputs only; never changes frozen M0')
    args=parser.parse_args();root=args.root.resolve();result,scores,cells,regions=analyse(root)
    if args.write_derived:
        for name,records in [('M1_A_RAW_SCORES.csv',scores),('M1_A_PER_CELL_DIFFERENCES.csv',cells),('M1_A_REGION_DIFFERENCES.csv',regions)]:
            path=root/name;assert not path.exists()
            with path.open('w',encoding='utf-8',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
        path=root/'M1_A_RESULT.json';assert not path.exists();path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
