import csv, json, pathlib, sys, collections, math
run=pathlib.Path(sys.argv[1]); bank=run/'context_bank'
timing=list(csv.DictReader((bank/'source_update_timing.csv').open()))
row=max((r for r in timing if float(r['sim_time'])<=300),key=lambda r:float(r['sim_time']))
d=bank/f"source_update_{int(row['source_update_id']):04d}"
manifest=list(csv.DictReader((d/'candidate_manifest.csv').open()))
alignment=list(csv.DictReader((d/'candidate_support_alignment.csv').open()))
measured=list(csv.DictReader((d/'measured_hit_probability.csv').open()))
expected={r['cell_index'] for r in measured if r['occupancy']=='Free' and float(r['confidence'])>0}
ids={r['candidate_id'] for r in manifest}; grouped=collections.defaultdict(list)
for r in alignment: grouped[r['candidate_id']].append(r)
details={cid:{'rows':len(rows),'distinct_cells':len({r['cell_index'] for r in rows}),'complete':{r['cell_index'] for r in rows}==expected and len(rows)==len(expected) and all(math.isfinite(float(r['simulated_hit_probability'])) for r in rows)} for cid,rows in grouped.items()}
p={'source_update_id':int(row['source_update_id']),'sim_time':float(row['sim_time']),'native_forward_candidate_count':int(row['native_candidate_count']),'manifest_distinct':len(ids),'alignment_distinct':len(grouped),'expected_support_rows_per_candidate':len(expected),'support_completeness_pass':ids==set(grouped) and bool(expected) and all(r['complete'] for r in details.values()),'candidates':details,'f32_required':False}
print(json.dumps(p,indent=2))
