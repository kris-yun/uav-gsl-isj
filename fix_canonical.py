p = '/home/zyc/gsl_ws/src/vgr_bridge/vgr_bridge/result_contract.py'
with open(p) as f:
    c = f.read()
if 'B4_PMFS_official' not in c:
    old = '"B3_surge_cast_pf_official": dict(method_family="official_hybrid", ablation_id="NA", use_sdbe=0, use_iasc=0, use_sepf=0, use_pcrd=0, use_pgn=0),'
    new = old + '\n    "B4_PMFS_official": dict(method_family="official_path", ablation_id="NA", use_sdbe=0, use_iasc=0, use_sepf=0, use_pcrd=0, use_pgn=0),\n    "B5_GrGSL_official": dict(method_family="official_path", ablation_id="NA", use_sdbe=0, use_iasc=0, use_sepf=0, use_pcrd=0, use_pgn=0),'
    c = c.replace(old, new)
    with open(p, 'w') as f:
        f.write(c)
    print('Added PMFS and GrGSL')
else:
    print('Already exists')