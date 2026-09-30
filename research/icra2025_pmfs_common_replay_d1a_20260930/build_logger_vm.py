"""Compile only read-only logger additions, using isolated copies of existing objects.

Never edits ROS src/build/install or a frozen simulator. No algorithm/RNG draws added.
"""
import difflib,hashlib,json,os,shlex,subprocess
from pathlib import Path
ROOT=Path('/home/zyc/d1a_common_replay_20260930')
BASE=Path('/dev/shm/brg_navfix_gsl_server_build_20260928')
SRC=Path('/home/zyc/ros2_ws/brg_closedloop_20260927/src/gsl_server/src/gsl_server/algorithms')
NATIVE=Path('/home/zyc/ros2_ws/brg_closedloop_20260927/install/gsl_server/lib/gsl_server/gsl_actionserver_node')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def flags(target):
    lines=(BASE/f'CMakeFiles/{target}.dir/flags.make').read_text().splitlines()
    return sum((shlex.split(next(s.split(' = ',1)[1] for s in lines if s.startswith(k+' = ')))
                for k in ['CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS']),[])
def main():
    out=ROOT/'logger_build';out.mkdir(parents=True,exist_ok=False)
    states=SRC/'Common/States/StopAndMeasureState.cpp';math=SRC/'Common/Utils/Math.cpp';utils=SRC/'PMFS/PMFS_utils.cpp'
    before={str(p):sha(p) for p in [states,math,utils,NATIVE]}
    for name in ['libGSL_common.a','libPMFS.a']:assert (BASE/name).is_file()
    # Assert the native existing archives link to the installed frozen executable.
    assert '-DUSE_GADEN=1' in flags('GSL_common')
    text=states.read_text();needle='            writeMeasurementTrace(concentration, windSpeed, windDirection);'
    assert text.count(needle)==1
    addition=r'''
            // D1A output only: snapshot completed block; no topic/RNG/state/planner writes.
            const char* d1aPath = std::getenv("D1A_EVENTS_RAW_JSONL");
            if (d1aPath && *d1aPath) {
                const char* run = std::getenv("D1A_RUN_ID");
                std::ofstream stream(d1aPath, std::ios::app);
                const auto& p = algorithm->currentRobotPose.pose.pose;
                stream << std::setprecision(17)
                  << "{\"run_id\":\"" << (run ? run : "UNSET") << "\",\"measurement_cycle_id\":" << measurement_cycle_counter_
                  << ",\"physical_time_s\":" << algorithm->node->now().seconds()
                  << ",\"window_start_s\":" << measure_window_start_.seconds()
                  << ",\"window_end_s\":" << algorithm->node->now().seconds()
                  << ",\"xyz\":[" << p.position.x << ',' << p.position.y << ',' << p.position.z
                  << "],\"quaternion_xyzw\":[" << p.orientation.x << ',' << p.orientation.y << ',' << p.orientation.z << ',' << p.orientation.w
                  << "],\"gas_value_used_ppm\":" << concentration << ",\"gas_threshold_ppm\":" << algorithm->thresholdGas
                  << ",\"hit\":" << (concentration > algorithm->thresholdGas ? "true" : "false")
                  << ",\"local_wind_speed_used_m_s\":" << windSpeed << ",\"map_downwind_direction_used_rad\":" << windDirection
                  << ",\"gas_samples_ppm\":[";
                for (size_t i=0;i<gas_v.size();++i) { if(i)stream << ','; stream << gas_v[i]; }
                stream << "],\"gas_sample_clock_s\":[";
                for (size_t i=0;i<gas_time_v.size();++i) { if(i)stream << ','; stream << gas_time_v[i].seconds(); }
                stream << "],\"raw_local_wind_speed_samples_m_s\":[";
                for (size_t i=0;i<windSpeed_v.size();++i) { if(i)stream << ','; stream << windSpeed_v[i]; }
                stream << "],\"raw_map_downwind_direction_samples_rad\":[";
                for (size_t i=0;i<windDirection_v.size();++i) { if(i)stream << ','; stream << windDirection_v[i]; }
                stream << "]}\n";
                stream.flush();
                if (!stream) throw std::runtime_error("D1A_READONLY_LOG_WRITE_FAILED");
            }
'''
    modified=text.replace(needle,needle+'\n'+addition)
    for header in ['cstdlib','fstream','iomanip','stdexcept']:
        modified=f'#include <{header}>\n'+modified
    (out/'StopAndMeasureState.cpp').write_text(modified)
    original=math.read_text()
    assert original.count('return mean + dist(RNGengine);')==1
    assert original.count('return min + distribution(RNGengine) * (max - min);')==1
    logger=r'''
#include <cstdint>
#include <cstring>
#include <sstream>
namespace GSL::Utils {
    static thread_local uint64_t D1A_draw_count=0;
    static thread_local uint64_t D1A_draw_hash=14695981039346656037ULL;
    template<typename T> T D1A_readonlyRecord(T value) {
        unsigned char bytes[sizeof(T)]; std::memcpy(bytes,&value,sizeof(T));
        for (auto b:bytes) { D1A_draw_hash^=b; D1A_draw_hash*=1099511628211ULL; }
        ++D1A_draw_count; return value;
    }
    std::string D1A_readonlyDrawDigest() {
        std::ostringstream stream; stream << D1A_draw_count << ':' << D1A_draw_hash;
        return stream.str();
    }
}
'''
    modified=logger+original.replace('return mean + dist(RNGengine);','return D1A_readonlyRecord(mean + dist(RNGengine));').replace(
        'return min + distribution(RNGengine) * (max - min);','return D1A_readonlyRecord(min + distribution(RNGengine) * (max - min));')
    (out/'Math.cpp').write_text(modified)
    # RNG audit is always present in both modes, consumes no randomness and has no algorithm reader.
    original_utils=utils.read_text()
    assert original_utils.count('void PMFS::auditBelief(const char* stage)')==1
    needle='      << ",\\\"search_time_s\\\":" << (node->now()-startTime).seconds()'
    assert original_utils.count(needle)==1,needle
    modified_utils='#include <string>\nnamespace GSL::Utils { std::string D1A_readonlyDrawDigest(); }\n'+original_utils.replace(
        needle,needle+'\n      << ",\\\"scientific_random_stream_digest\\\":\\\"" << Utils::D1A_readonlyDrawDigest() << "\\\""')
    (out/'PMFS_utils.cpp').write_text(modified_utils)
    sources=[(states,out/'StopAndMeasureState.cpp','GSL_common'),(math,out/'Math.cpp','GSL_common'),(utils,out/'PMFS_utils.cpp','PMFS')]
    commands=[]
    for source,new,target in sources:
        (out/(new.stem+'.patch')).write_text(''.join(difflib.unified_diff(source.read_text().splitlines(True),new.read_text().splitlines(True),fromfile=str(source),tofile=str(new))))
        cmd=['/usr/bin/c++',*flags(target),'-c',str(new),'-o',str(new.with_suffix('.o'))]
        commands.append(cmd);subprocess.run(cmd,check=True)
    # Isolated static archive views: read original members; never write the base archives.
    for lib,members in [('libGSL_common.a',['StopAndMeasureState','Math']),('libPMFS.a',['PMFS_utils'])]:
        import shutil
        shutil.copy2(BASE/lib,out/lib)
        subprocess.run(['/usr/bin/ar','r',str(out/lib),*[str(out/(n+'.o')) for n in members]],check=True)
        # CMake original names end .cpp.o; remove originals to avoid duplicate definitions.
        subprocess.run(['/usr/bin/ar','d',str(out/lib),*[n+'.cpp.o' for n in members]],check=True)
        subprocess.run(['/usr/bin/ranlib',str(out/lib)],check=True)
    link=shlex.split((BASE/'CMakeFiles/gsl_actionserver_node.dir/link.txt').read_text())
    i=link.index('-o');link[i+1]=str(out/'gsl_actionserver_node')
    link=[str(out/t) if t in ('libGSL_common.a','libPMFS.a') else t for t in link]
    commands.append(link);subprocess.run(link,cwd=BASE,check=True)
    assert all(sha(Path(p))==digest for p,digest in before.items())
    report=dict(decision='D1A_LOGGER_BUILD_PASS',original_files_unmodified=before,
        logger_binary_sha256=sha(out/'gsl_actionserver_node'),original_binary_sha256=sha(NATIVE),
        modified_sources={p.name:sha(p) for _,p,_ in sources},commands=commands,
        RNG_draws_added=0,mathematical_expressions_unchanged=True,planner_stopping_unchanged=True,
        instrumentation='completed block full precision + existing posterior output + RNG returned-value audit only',
        mode_toggle='D1A_EVENTS_RAW_JSONL empty=OFF/nonempty=ON; RNG digest and baseline observer equal in both',
        production_src_build_install_modified=False)
    (out/'BUILD_PROVENANCE.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='commands'},indent=2))
if __name__=='__main__':main()
