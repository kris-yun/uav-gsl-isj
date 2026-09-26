#!/usr/bin/env python3
"""Add process snapshots around the unchanged historical C-arm score kernel."""
from pathlib import Path
root=Path(__file__).parent
source=(root/'historical_replay.cpp').read_text()
source=source.replace('#include <vector>', '#include <vector>\n#include <sys/wait.h>\n#include <unistd.h>')
source=source.replace('using Simulations::Simulations;', 'using Simulations::Simulations;\n    void setWind(const std::vector<Vector2>& values) { wind.data = values; }')
source=source.replace('if (argc != 4)', 'if (argc != 5)')
source=source.replace('SNAPSHOT_DIR ARM OUTPUT_DIR', 'SNAPSHOT_DIR ARM OUTPUT_DIR STATE_INPUT_DIR_OR_DASH')
source=source.replace('fs::path run(argv[1]), out(argv[3]);', 'cv::setNumThreads(1);\n        fs::path run(argv[1]), out(argv[3]), states(argv[4]);\n        const bool generateBank = states != fs::path("-");')
source=source.replace('if (arm != "A" && arm != "B" && arm != "C")', 'if (arm != "C")')
insert='''        std::vector<std::vector<Vector2>> stateWinds;
        if (generateBank) {
            for (int state = 0; state < 11; ++state) {
                std::vector<Vector2> stateWind(n, Vector2(0, 0));
                std::vector<bool> seen(n, false);
                auto rows = csv(states / ("state_" + std::to_string(state) + ".csv"));
                if (rows.size() != meta.numFreeCells) throw std::runtime_error("state wind shape mismatch");
                for (const auto& row : rows) {
                    const int k = integer(row, "cell_index");
                    if (k < 0 || k >= static_cast<int>(n) || seen[k] || occupancy[k] != Occupancy::Free)
                        throw std::runtime_error("invalid state wind cell");
                    seen[k] = true;
                    stateWind[k] = Vector2(static_cast<float>(d(row, "internal_u")), static_cast<float>(d(row, "internal_v")));
                }
                stateWinds.push_back(std::move(stateWind));
                fs::create_directories(out / "bank" / ("state_" + std::to_string(state)) / "maps");
            }
        }
'''
source=source.replace('        fs::create_directories(out / "maps");',insert+'        fs::create_directories(out / "maps");')
insert='''            if (generateBank) {
                scores.flush();
                // Each sibling inherits the same entire historical RNG engine
                // and normal-distribution cache at this candidate boundary.
                // The parent advances only under the original z=0 state0 field.
                for (int state = 0; state < 11; ++state) {
                    const pid_t pid = fork();
                    if (pid < 0) throw std::runtime_error("fork failed");
                    if (pid == 0) {
                        try {
                            replay.setWind(stateWinds[state]);
                            auto result = replay.score(frozenLeaves[i]);
                            const fs::path target = out / "bank" / ("state_" + std::to_string(state)) / "maps" / (row.at("candidate_id") + ".f32");
                            std::ofstream file(target, std::ios::binary);
                            file.write(reinterpret_cast<const char*>(result.second.data()), result.second.size() * sizeof(float));
                            file.close();
                            if (!file) _exit(92);
                            _exit(0);
                        } catch (...) { _exit(93); }
                    }
                    int status = 0;
                    if (waitpid(pid, &status, 0) != pid || !WIFEXITED(status) || WEXITSTATUS(status) != 0)
                        throw std::runtime_error("wind-state child failed");
                }
            }
'''
source=source.replace('            auto [score, map] = replay.score(frozenLeaves[i]);', insert+'            auto [score, map] = replay.score(frozenLeaves[i]);')
source=source.replace('        std::ofstream audit(out / "source_blind_replay_audit.txt");', '        scores.close();\n        std::ofstream audit(out / "source_blind_replay_audit.txt");')
source=source.replace("                   << score << ',' << mapFile.generic_string() << '\\n';", "                   << score << ',' << mapFile.generic_string() << '\\n';\n            std::cout << \"WIND_ALIGNMENT_CANDIDATE_COMPLETE \" << (i+1) << \"/\" << candidates.size() << std::endl;")
assert source.count('fork();')==1
(root/'wind_alignment_replay.cpp').write_text(source)
