import json
with open("D:/ZYC/A-gas/literature_review/openalex_targeted_round6.json","r",encoding="utf-8") as f:
    data=json.load(f)
keywords=['odor','gas source','plume','olfact','gaden','infotaxis','pmfs','chemical plume','gas distribution','gas leak','gas concentration','entrotaxis','klinotaxis']
relevant=[]
seen=set()
for q,papers in data.items():
    for p in papers:
        t=p['title'].lower()
        if any(k in t for k in keywords):
            k=p['title'][:60].lower()
            if k not in seen:
                seen.add(k)
                relevant.append(p)
relevant.sort(key=lambda x:(-x['cited']))
for p in relevant[:35]:
    oa='OA' if p['oa'] else 'PAY'
    print(f"{p['year']} | cite={p['cited']} | {oa} | {p['title'][:95]}")
    print(f"  venue: {p['venue'][:60]}")
    if p['doi']: print(f"  doi: {p['doi']}")
    print()
