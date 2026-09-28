#!/usr/bin/env python3
"""Freeze geometry-only routes from D1 episodes without exporting gas readings."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
manifest_path = ROOT / "evidence/ds_pmfs_identity_d1/ASSET_FREEZE.json"
events_path = ROOT / "evidence/ds_pmfs_identity_d1/COMPACT_EVENTS.json"
assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == "c4b87c1a11571ba792bd79f1b82c9205ea17f3f32fb7e161aab42441adbd2328"
assert hashlib.sha256(events_path.read_bytes()).hexdigest() == "47b8fffb2764737ff0eb3b3f6a93bc495cfdf00c53e99bf8fa6a105128372051"
manifest = json.loads(manifest_path.read_text())
events = {r["case_id"]: r for r in json.loads(events_path.read_text())}
routes = []
for episode in manifest["episodes"]:
    if episode["env"] >= 3:
        continue
    entry = events[episode["case_id"]]
    prefix = entry["prefixes"][-1]
    assert prefix % 5 == 0 and prefix <= len(entry["events"])
    xy = []
    for start in range(0, prefix, 5):
        block = entry["events"][start:start+5]
        points = [[float(e["x"]), float(e["y"])] for e in block]
        assert all(p == points[0] for p in points)
        xy.append(points[0])
    routes.append(dict(case_id=episode["case_id"], env=episode["env"],
                       house=episode["house"], wind=episode["wind"],
                       source_id=episode["source_id"], event_prefix=prefix,
                       xy=xy))
assert len(routes) == 49
out = ROOT / "evidence/aec_d0/ROUTE_POSITIONS_ONLY.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(routes, indent=2, sort_keys=True) + "\n")
print(hashlib.sha256(out.read_bytes()).hexdigest(), len(routes))
