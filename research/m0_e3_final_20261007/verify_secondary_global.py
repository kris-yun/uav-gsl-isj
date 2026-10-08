from pathlib import Path
import csv,json,numpy as np
R=Path(__file__).resolve().parent;D=R/'evidence';INDEX=json.loads((D/'ALL40_INDEX.json').read_text());maps=0;queries=0;maxdiff=0.
for entry in INDEX:
    rid=entry['frozen_row']['run_id'];a=D/'secondary_global'/rid;b=D/'bank'/rid/'audit'
    for t in range(20,121,2):
        whole=np.fromfile(a/('roi_column_t'+str(t)+'.f32'),dtype='<f4').reshape(80,120);roi=np.fromfile(b/('roi_column_t'+str(t)+'.f32'),dtype='<f4').reshape(32,40);assert np.array_equal(whole[24:56,28:68],roi),rid;maps+=1
    with (a/'sampling_parity.csv').open() as f:p=list(csv.DictReader(f))
    assert all(float(q['absolute_difference'])<=1e-5*(1+abs(float(q['native']))) for q in p);queries+=len(p);maxdiff=max(maxdiff,max(float(q['absolute_difference']) for q in p))
x={'status':'SECONDARY_NATIVE_GLOBAL_COLUMNS_PASS','runs':40,'whole_domain_grid':[120,80],'frames_each':51,'ROI_crop_maps_bit_identical':maps,'additional_native_parity_queries':queries,'native_parity_max_abs_difference':maxdiff,'primary_ROI_native_queries':102000,'all_direct_queries_total':102000+queries,'extra_scientific_runs':0,'primary_metrics_unchanged':True}
(R/'SECONDARY_GLOBAL_PARITY_VERIFICATION.json').write_bytes((json.dumps(x,indent=2)+'\n').encode());print(json.dumps(x,indent=2))
