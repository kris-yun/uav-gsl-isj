"""Count crossed source/transport interventions using frozen metadata only."""
import argparse
from collections import defaultdict
import hashlib
import itertools
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    path=ROOT/'evidence/cstar_raw_provenance_20260906/CSTAR_RAW_REALIZATION_PROVENANCE_AUDIT_V1.json'
    audit=json.loads(path.read_text()); entries=audit['normalized_entries']; houses=[]
    for house in ('H01','H02','H03'):
        rows=[r for r in entries if r['house']==house]; matched=[];same_source=[]
        for a,b in itertools.combinations(rows,2):
            same=a['source_xyz_m']==b['source_xyz_m']
            context_equal=all(a[k]==b[k] for k in ('transport_fingerprint','release_fingerprint','sensor_mechanism_fingerprint'))
            if not same and context_equal: matched.append([a['realization_id'],b['realization_id']])
            if same and a['transport_fingerprint']!=b['transport_fingerprint']:
                same_source.append([a['realization_id'],b['realization_id']])
        sources=sorted({tuple(r['source_xyz_m']) for r in rows})
        anchor=[r for r in rows if tuple(r['source_xyz_m'])==sources[0]]
        # A reviewable minimal crossing, not authority to generate data or
        # assign new seeds. Each missing cell reuses an existing source and
        # transport setting; realized release noise must be matched or modeled.
        missing=[dict(source_xyz_m=list(s),transport_from_realization=r['realization_id'],
                      transport_fingerprint=r['transport_fingerprint'])
                 for s in sources[1:] for r in anchor
                 if not any(tuple(e['source_xyz_m'])==s and e['transport_fingerprint']==r['transport_fingerprint'] for e in rows)]
        houses.append(dict(house=house,realizations=len(rows),exact_source_count=len(sources),
                           same_source_transport_pairs=same_source,matched_context_source_pairs=matched,
                           release_setting_count=len({r['release_fingerprint'] for r in rows}),
                           sensor_setting_count=len({r['sensor_mechanism_fingerprint'] for r in rows}),
                           missing_crossed_cells=missing))
    report=dict(contract='CSTAR_SOURCE_TRANSPORT_CROSSING_AUDIT_V1',houses=houses,
                provenance_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                verdict='CROSSED_SOURCE_INTERVENTIONS_MISSING',formal_gate_authority=False,
                interpretation='Same-source nuisance variation exists. Different-source pairs change transport too; latent separation alone cannot attribute their difference to source. This is a coverage limit, not a proof that gas is uninformative.',
                next_data_requirement='Preserve current sources/Houses. Add the listed crossed transport settings only under a preregistered generator/release-state contract. No new seeds assigned or simulator jobs started by this audit.')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(report['verdict']); print([(h['house'],len(h['matched_context_source_pairs']),len(h['missing_crossed_cells'])) for h in houses])


if __name__=='__main__': main()
