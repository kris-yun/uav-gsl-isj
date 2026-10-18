from pathlib import Path
import csv,hashlib,json
R=Path(__file__).resolve().parent;F=next((R/'cases').iterdir());rt=F/'runtime';O=R/'minimal_score_sample';O.mkdir(exist_ok=True)
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8')))
def write(p,rr):
 with p.open('w',newline='',encoding='utf-8')as f:w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
post=rows(rt/'native_posterior_updates.csv');u=min(int(x['update'])for x in post);post=[x for x in post if int(x['update'])==u];cand=[x for x in rows(rt/'native_candidate_maps.csv')if int(x['update'])==u];blob=(rt/'native_candidate_maps.f32').read_bytes();out=bytearray()
for x in cand:
 start=int(x['offset_bytes']);n=int(x['count'])*4;x['original_offset_bytes']=start;x['offset_bytes']=len(out);out.extend(blob[start:start+n])
write(O/'measurement_and_posterior.csv',post);write(O/'candidates.csv',cand);(O/'candidate_maps.f32').write_bytes(out)
nav=json.loads((rt/'NAVIGATION_MAP_METADATA.json').read_text());nav.update(nx=nav['width']//25,ny=nav['height']//25,role=F.name,update=u,selection='First source update, fixed before looking at score or error',D=.2,meaning='Actual native blur response maps and native consumer map; no reference bank, new physical simulation or source labels used in scorer.')
(O/'geometry_and_identity.json').write_text(json.dumps(nav,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(O/'README_zh.md').write_text('此样例取补跑A2的第一次源更新，供Pro不安装ROS复算原生全图源评分和后验。运行python3 replay_score.py；需要NumPy。它只验证保存计算，不产生新航线、观测或闭环收益。C++主程序位于recovery/source_runtime，C++原生读出复算位于recovery/native_readout_check.cpp。\n',encoding='utf-8')
print(json.dumps(dict(update=u,source_cells=len(post),candidates=len(cand),response_bytes=len(out))))
