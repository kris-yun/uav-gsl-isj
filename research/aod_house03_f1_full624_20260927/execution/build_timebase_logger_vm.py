#!/usr/bin/env python3
"""Stage B only: isolated node logging; the seeded GADEN numerical core is unchanged."""
import hashlib, json, shlex, shutil, subprocess
from pathlib import Path

R=Path('/home/zyc/aod_house03_f1_full624_20260927')
G=Path('/home/zyc/hcmc_gaden_seed_build_20260922')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    assert json.loads((R/'PRE_TARGET_FREEZE.json').read_text())['passed']
    assert json.loads((R/'TEMPLATE_FREEZE.json').read_text())['passed']
    src=G/'src/GADEN/gaden_filament_simulator/src'
    out=R/'timebase_logger';out.mkdir(exist_ok=False)
    shutil.copyfile(src/'filament_simulator.h',out/'filament_simulator.h')
    code=(src/'filament_simulator.cpp').read_text()
    include='#include <gaden_common/Visualization.hpp>'
    assert code.count(include)==1
    code=code.replace(include,include+'\n#include <fstream>\n#include <iomanip>\n#include <cstdlib>')
    needle='    while (rclcpp::ok() && sim->GetCurrentTime() < maxSimTime)'
    assert code.count(needle)==1
    logger=r'''
    const char* auditDir = std::getenv("AOD_TIME_AUDIT_DIR");
    if (!auditDir) throw std::runtime_error("AOD_TIME_AUDIT_DIR required");
    const char* runIdEnv = std::getenv("AOD_RUN_ID");
    const std::string auditRunId = runIdEnv ? runIdEnv : "unknown";
    std::ofstream aodMap(std::filesystem::path(auditDir)/"RESULT_TIME_MAP.tsv");
    std::ofstream aodRelease(std::filesystem::path(auditDir)/"RELEASE_TIME_METADATA.tsv");
    aodMap << "run_id\tsave_record_id\tphysical_sim_time_s\toutput_path\twind_index\tintegration_step\n" << std::setprecision(17);
    aodRelease << "event\tphysical_sim_time_s\tfilament_count\tdelta_time_s\n" << std::setprecision(17);
    aodRelease << "release_enabled_first_step\t" << sim->GetCurrentTime() << "\t0\t" << params.deltaTime << "\n";
    size_t aodNextSave = 0, aodStep = 0;
    bool aodFirstGasLogged = false;
'''
    code=code.replace(needle,logger+'\n'+needle)
    needle='        sim->AdvanceTimestep();'
    assert code.count(needle)==1
    code=code.replace(needle,r'''
        // SaveResults executes before the core increments currentTime or wind
        // index. These getters record the exact state/time used by the writer.
        const float aodTimeBefore = sim->GetCurrentTime();
        const size_t aodWindBefore = envConfig->windSequence.GetCurrentIndex();
        sim->AdvanceTimestep();
        const auto aodOutput = params.saveDataDirectory / ("iteration_" + std::to_string(aodNextSave));
        if (std::filesystem::exists(aodOutput)) {
            aodMap << auditRunId << "\t" << aodNextSave << "\t" << aodTimeBefore << "\t" << aodOutput.string()
                   << "\t" << aodWindBefore << "\t" << aodStep << "\n";
            aodMap.flush();
            ++aodNextSave;
        }
        if (!aodFirstGasLogged && !sim->GetFilaments().empty()) {
            aodRelease << "first_nonzero_filament_count\t" << aodTimeBefore << "\t" << sim->GetFilaments().size()
                       << "\t" << params.deltaTime << "\n";
            aodRelease.flush();
            aodFirstGasLogged = true;
        }
        ++aodStep;
''')
    patched=out/'filament_simulator_timebase.cpp';patched.write_text(code)
    flags=[]
    for line in (G/'build/gaden_filament_simulator/CMakeFiles/filament_simulator.dir/flags.make').read_text().splitlines():
        if line.startswith(('CXX_DEFINES =','CXX_INCLUDES =','CXX_FLAGS =')):
            flags+=shlex.split(line.split('=',1)[1])
    command=shlex.split((G/'build/gaden_filament_simulator/CMakeFiles/filament_simulator.dir/link.txt').read_text())
    for i,x in enumerate(command):
        if x.endswith('.cpp.o'):command[i]=str(patched)
        if i>0 and command[i-1]=='-o':command[i]=str(out/'filament_simulator_timebase')
    command=command[:1]+flags+command[1:]
    # The installed seeded library retains external bsc_init/bsc_compress
    # symbols. Bind the existing compression library explicitly; no rebuild of
    # the seeded numerical core, compression code, clock or writer is made.
    bsc=G/'build/gaden_common/third_party/gaden_core/third_party/libbsc/libbsc.so'
    assert bsc.is_file()
    command += [str(bsc), '-Wl,-rpath,'+str(bsc.parent)]
    with (out/'build.log').open('w') as log:
        log.write(shlex.join(command)+'\n');log.flush()
        subprocess.run(command,cwd=G/'build/gaden_filament_simulator',stdout=log,stderr=subprocess.STDOUT,check=True)
    provenance=dict(original_node_sha256=sha(src/'filament_simulator.cpp'),
        node_header_sha256=sha(src/'filament_simulator.h'),patched_node_sha256=sha(patched),
        binary_sha256=sha(out/'filament_simulator_timebase'),
        seeded_numerical_library_sha256=sha(G/'install/gaden_common/lib/libgaden.so'),
        seeded_math_source_sha256=sha(G/'src/GADEN/gaden_common/third_party/gaden_core/include/gaden/internal/MathUtils.hpp'),
        original_seeded_binary_sha256=sha(G/'install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator'),
        compression_library_path=str(bsc),compression_library_sha256=sha(bsc),
        command=command,scope='logging only; no numerical core, clock, writer, parameters, RNG or gas outputs modified')
    (out/'LOGGER_BUILD_PROVENANCE.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print('LOGGING_ONLY_TIMEBASE_NODE_BUILT',flush=True)

if __name__=='__main__':main()
