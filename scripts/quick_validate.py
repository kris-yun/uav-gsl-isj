#!/usr/bin/env python3
import subprocess, time, csv, os, re

HOUSES = [
    {"name":"House01","path":"/home/zyc/vgr_data_scenarios/House01","sx":-0.40,"sy":-2.90,"sz":-0.30},
    {"name":"House02","path":"/home/zyc/vgr_data_scenarios/House02","sx":0.0,"sy":-1.0,"sz":0.2},
    {"name":"House03","path":"/home/zyc/vgr_data_scenarios/House03","sx":-0.45,"sy":1.9,"sz":-0.1},
]
SEEDS=[0,1,2]
TIMEOUT=300

def kill_all():
    subprocess.run("pkill -9 -f gsl_actionserver; pkill -9 -f vgr_sim_node",shell=True,stderr=subprocess.DEVNULL)
    time.sleep(2)

def run_one(h,s):
    lbl=h["name"]+"_s"+str(s)
    lf="/tmp/cp_sbd_quick/"+lbl+".log"
    kill_all()
    subprocess.run("rm -f /tmp/gsl_result.csv",shell=True)
    cmd=";".join([
        "cd /home/zyc/gsl_ws",
        "source install/setup.bash",
        "ros2 launch vgr_bridge vgr_ablation.launch.py "
        "vgr_data_path:="+h["path"]+" "
        "config_id:=2,4-1_fast algorithm:=OPGSL "
        "source_x:="+str(h["sx"])+" source_y:="+str(h["sy"])+" source_z:="+str(h["sz"])+" "
        "start_x:=-0.9 start_y:=0.15 seed:="+str(s)+" "
        "timeout_sec:="+str(TIMEOUT)+" use_sbd:=true resultsFile:=/tmp/gsl_result.csv"
    ])
    proc=subprocess.Popen(["bash","-c",cmd],stdout=open(lf,"w"),stderr=subprocess.STDOUT,preexec_fn=os.setsid)
    t0=time.time()
    r={"house":h["name"],"seed":s,"map_dist":"N/A","steps":"N/A","elapsed":"0"}
    while time.time()-t0<TIMEOUT+60:
        time.sleep(5)
        if os.path.exists("/tmp/gsl_result.csv"):
            with open("/tmp/gsl_result.csv") as f:
                c=f.read().strip()
                if c and len(c.split("\n"))>1: break
        if proc.poll() is not None:
            time.sleep(3)
            break
    r["elapsed"]="%.1f"%(time.time()-t0)
    if os.path.exists("/tmp/gsl_result.csv"):
        try:
            with open("/tmp/gsl_result.csv") as f:
                for row in csv.DictReader(f):
                    for k in ["map_dist","search_d","final_distance","distance_to_source"]:
                        if k in row and row[k]: r["map_dist"]=row[k]; break
                    if "steps" in row: r["steps"]=row["steps"]
        except: pass
    try:
        with open(lf) as f:
            for line in f:
                for p in [r"Search_d=([0-9.e]+)",r"final_distance[=:]\s*([0-9.e]+)",r"distance_to_source[=:]\s*([0-9.e]+)"]:
                    m=re.search(p,line,re.I)
                    if m: r["map_dist"]=m.group(1)
    except: pass
    kill_all()
    return r

os.makedirs("/tmp/cp_sbd_quick",exist_ok=True)
results=[]
print("house,seed,map_dist,steps,elapsed",flush=True)
for h in HOUSES:
    for s in SEEDS:
        r=run_one(h,s)
        results.append(r)
        print("%s,%s,%s,%s,%s"%(r["house"],r["seed"],r["map_dist"],r["steps"],r["elapsed"]),flush=True)
with open("/tmp/cp_sbd_quick/summary.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["house","seed","map_dist","steps","elapsed"])
    w.writeheader()
    w.writerows(results)
print("=== Summary ===")
for hn in ["House01","House02","House03"]:
    ds=[float(r["map_dist"]) for r in results if r["house"]==hn and r["map_dist"]!="N/A"]
    if ds: print("%s: n=%d median=%.2fm"%(hn,len(ds),sorted(ds)[len(ds)//2]))
    else: print("%s: no valid results"%hn)
