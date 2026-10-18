from pathlib import Path
import difflib,hashlib,io,json,re,shutil,subprocess,tarfile
import requests
R=Path(__file__).resolve().parent;PROJECT=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
source_lock=json.loads((R/'SOURCE_LOCK.json').read_text(encoding='utf-8'))
deps=R/'dependencies';deps.mkdir(exist_ok=False)
for name,commit in [('DDA','e852a1870bcc5a9285244ffc1111d65e7e6e776a'),('StateMachine','3805501e55a272bf917cf5b1eb50b31d7146daed')]:
    if name=='StateMachine':
        source=PROJECT/'workspace/PMFS_OFFICIAL_REPRO_AUDIT_20261016/source_metadata/StateMachine_2024.tar';archive=deps/(name+'.tar');shutil.copyfile(source,archive)
        q=subprocess.run(['git','get-tar-commit-id'],input=archive.read_bytes(),capture_output=True);assert q.returncode==0 and q.stdout.decode().strip()==commit
        mode='tar';prefix=None
    else:
        archive=deps/(name+'.tar.gz');url='https://codeload.github.com/PepeOjeda/DDA/tar.gz/'+commit
        q=requests.get(url,timeout=(8,30));q.raise_for_status();assert len(q.content)<4*2**20;archive.write_bytes(q.content);mode='r:gz';prefix='DDA-'+commit+'/'
    target=deps/name;target.mkdir()
    with tarfile.open(archive,mode='r:*')as ar:
        for m in ar.getmembers():
            if not m.isfile():assert m.isdir();continue
            n=m.name
            if prefix:assert n.startswith(prefix);n=n[len(prefix):]
            p=target/n;assert p.resolve().is_relative_to(target.resolve());p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(ar.extractfile(m).read())
    put(deps/(name+'_LOCK.json'),dict(commit=commit,origin='Pinned Sep18 gitlink',archive_sha256=sha(archive),files=[dict(path=p.relative_to(target).as_posix(),sha256=sha(p))for p in sorted(target.rglob('*'))if p.is_file()]))
src=R/'source_runtime';shutil.copytree(R/'official_exact/gsl_server',src)
for name in ['DDA','StateMachine']:
    dst=src/'third_party'/name
    if dst.exists():assert not any(dst.iterdir())
    shutil.copytree(deps/name,dst,dirs_exist_ok=True)
patches=[]
def edit(rel,after,classification):
    p=src/rel;before=p.read_text();assert before!=after;dest=R/'patches';dest.mkdir(exist_ok=True)
    patch=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='official/'+rel,tofile='runtime/'+rel))
    (dest/(classification+'_'+Path(rel).name+'.patch')).write_text(patch,encoding='utf-8')
    p.write_text(after,encoding='utf-8',newline='\n');patches.append(dict(path=rel,kind=classification,original_sha256=hashlib.sha256(before.encode()).hexdigest(),runtime_sha256=sha(p)))
rel='CMakeLists.txt';cm=(src/rel).read_text()
for key in ['GSL_DEBUG','USE_GUI','USE_TRACY','USE_TRACY_INSTRUMENTATION','USE_GADEN']:
    cm,n=re.subn(r'set\('+key+r' (?:ON|OFF)\)',f'set({key} OFF)',cm);assert n==1,key
cm=cm.replace('"-g -Wno-narrowing','"-g0 -Wno-narrowing')
cm=cm.replace('  src\n','  src\n  /usr/local/include/magic_enum\n')
for name in ['PlumeTracking','Spiral','ParticleFilter','GrGSL','Semantics']:
    line=f'include(src/gsl_server/algorithms/{name}/CMakeLists.txt)';assert cm.count(line)==1;cm=cm.replace(line,'# Build only the selected PMFS action implementation: '+line)
edit(rel,cm,'BUILD_ONLY')
rel='src/gsl_server/algorithms/PMFS/PMFSLib.cpp';text=(src/rel).read_text();old='double exponent = -cell.omega / std::pow(settings.confidenceMeasurementWeight, 2);';assert text.count(old)==1
edit(rel,text.replace(old,'double exponent = -(cell.omega * cell.omega) / std::pow(settings.confidenceMeasurementWeight, 2);'),'PAPER_EQ6')
rel='src/gsl_server/algorithms/Common/StopAndMeasureState.cpp';text=(src/rel).read_text();text=text.replace('#include <gsl_server/algorithms/Common/Utils/Math.hpp>','#include <gsl_server/algorithms/Common/Utils/Math.hpp>\n#include <fstream>\n#include <iomanip>\n#include <cstdlib>')
needle='            double concentration = average_concentration();';assert text.count(needle)==1
text=text.replace(needle,'''            const char* tracePath = std::getenv("NATIVE_PMFS_WINDOW_TRACE");
            static std::ofstream trace;
            static size_t windowEvent = 0;
            if (tracePath && !trace.is_open()) {
                trace.open(tracePath);
                trace << "event,node_clock_ns,window_start_node_ns,gas_count,wind_count,concentration_mean_ppm,wind_speed_mean,wind_direction_mean,status\\n" << std::setprecision(17);
            }
            if (gas_v.empty() || windSpeed_v.empty() || windDirection_v.empty()) {
                if (trace.is_open()) {trace << ++windowEvent << "," << algorithm->node->now().nanoseconds() << "," << time_stopped.nanoseconds() << "," << gas_v.size() << "," << windSpeed_v.size() << ",,,,WAIT_EMPTY_OBSERVATION\\n";trace.flush();}
                return;
            }
            double concentration = average_concentration();''')
needle='            algorithm->processGasAndWindMeasurements(concentration, windSpeed, windDirection);';assert text.count(needle)==1
text=text.replace(needle,'''            if (trace.is_open()) {trace << ++windowEvent << "," << algorithm->node->now().nanoseconds() << "," << time_stopped.nanoseconds() << "," << gas_v.size() << "," << windSpeed_v.size() << "," << concentration << "," << windSpeed << "," << windDirection << ",CONSUMED\\n";trace.flush();}
'''+needle)
edit(rel,text,'INPUT_VALIDITY_AND_PASSIVE_TRACE')
rel='src/gsl_server/algorithms/PMFS/PMFS.cpp';text=(src/rel).read_text();needle='        dynamic_cast<MovingStatePMFS*>(movingState.get())->publishMarkers();';assert text.count(needle)==1
text=text.replace(needle,'        if (!visibilityMap.has_value()) return; // Do not read map-derived arrays before the map callback.\n'+needle)
edit(rel,text,'MAP_STARTUP_GUARD')
rel='src/gsl_server/algorithms/PMFS/internal/Simulations.cpp';text=(src/rel).read_text();text=text.replace('#include <DDA/DDA.h>','#include <DDA/DDA.h>\n#include <fstream>\n#include <iomanip>\n#include <cstdlib>')
needle='        GSL_INFO("Time ellapsed in simulation = {} s", stopwatch.ellapsed());';assert text.count(needle)==1
text=text.replace(needle,needle+'''
        if (const char* path = std::getenv("NATIVE_PMFS_POSTERIOR_TRACE")) {
            static std::ofstream trace(path);static size_t update = 0;
            if (update==0) trace << "update,row,col,x_m,y_m,cell_size_m,source_probability,hit_log_odds,hit_omega,hit_confidence,estimated_wind_u,estimated_wind_v\\n";
            trace << std::setprecision(17);++update;
            for (int y=0;y<sourceProb.metadata.dimensions.y;++y) for (int x=0;x<sourceProb.metadata.dimensions.x;++x) if(sourceProb.freeAt(x,y)) {
                const auto p=sourceProb.metadata.indexToCoordinates(x,y);const auto h=measuredHitProb.dataAt(x,y);const auto w=wind.dataAt(x,y);
                trace<<update<<","<<y<<","<<x<<","<<p.x<<","<<p.y<<","<<sourceProb.metadata.cellSize<<","<<sourceProb.dataAt(x,y)<<","<<h.logOdds<<","<<h.omega<<","<<h.confidence<<","<<w.x<<","<<w.y<<"\\n";
            } trace.flush();
        }''')
edit(rel,text,'PASSIVE_SOURCE_OMEGA_TRACE')
put(R/'PATCH_CLASSIFICATION.json',dict(patches=patches,scientific_change='Eq6 only plus separately frozen paper parameter overrides',not_innovation=True,age_growth_not_added=True,all_other_author_files_unchanged=True))
put(R/'BUILD_PRECOMMIT.json',dict(source_commit=source_lock['commit'],complete_source_identity=source_lock['tree'],guest_root='/home/zyc/ros2_ws/pmfs_paper_first_qual_20261017',new_guest_build=True,reuse_July_objects=False,build_parallelism=1,runtime_OMP_threads=4,guest_free_floor_bytes=5*2**30,host_D_floor_bytes=2*2**30,max_build_wall_s=1200,primary_cases=['A2','B2'],primary_goals=2,max_optional_technical_retries=2,max_total_goals=4,main_time_limit_from_pinned_GitHub_seconds=300.0,no_new_worlds=True,no_new_external_prediction_seed=True,no_AIMMD=True,clock_policy='Pinned public launch: PMFS wall seconds; BasicSim5x; sensor wall10/20Hz; file-wall2Hz cadence and author loop restored by disclosed existing player adapter. Record all three domains.',qualification_not_30_repeat_reproduction=True))
print(json.dumps(dict(status='BUILD_INPUTS_READY',source_files=len(source_lock['files']),patches=len(patches))))
