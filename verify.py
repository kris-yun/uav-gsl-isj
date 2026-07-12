import os
for i in range(1, 21):
    h = f"House{i:02d}"
    base = f"/home/zyc/vgr_data_scenarios/{h}"
    occ = os.path.isfile(f"{base}/OccupancyGrid3D.csv")
    gas = os.path.isdir(f"{base}/gas_simulations")
    wind = os.path.isdir(f"{base}/wind_simulations")
    ok = occ and gas and wind
    print(f"{h}: {'OK' if ok else 'MISSING'} [occ={occ} gas={gas} wind={wind}]")
