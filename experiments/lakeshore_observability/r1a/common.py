import pathlib,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[3]
EXP=ROOT/'experiments/lakeshore_observability'; OLD=ROOT/'evidence/lakeshore_observability_r0_r2'
OUT=ROOT/'evidence/lakeshore_r1a_deconfound_20261003'; OUT.mkdir(exist_ok=True)
HERE=pathlib.Path(__file__).parent
ENVS=['C20','C06','C08','S06','S08','H1','H2','F1','F2']
SOURCES=[(x,y) for x in [20,50,80] for y in [-20,0,20]]
SEEDS=list(range(31001,31009));HEIGHTS=[10,30,60,100]
HOST='zyc@192.168.111.128'; REMOTE='/home/zyc/lakeshore_r1a_deconfound_20261003'
ADAPTER='/home/zyc/lakeshore_observability_20261003/adapter'
LIB='/home/zyc/PF_DEI_V3_GADEN_BUILD/install/lib/libgaden.so'
PREFIX='source /opt/ros/humble/setup.bash; export LD_LIBRARY_PATH=/home/zyc/PF_DEI_V3_GADEN_BUILD/build/gaden_common/third_party/gaden_core/third_party/libbsc:$LD_LIBRARY_PATH; export OMP_NUM_THREADS=1; '
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def write_json(name,value): (OUT/name).write_text(json.dumps(value,indent=2,allow_nan=False),encoding='utf-8')
