#include <gaden/EnvironmentConfiguration.hpp>
#include <gaden/PlaybackSimulation.hpp>
#include <gaden/Scene.hpp>

#include <algorithm>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <limits>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

static bool load_scene(const fs::path& env_root,
                       const fs::path& gas_results,
                       std::shared_ptr<gaden::EnvironmentConfiguration>& env,
                       gaden::Scene*& scene_out,
                       std::shared_ptr<gaden::Scene>& owner_out,
                       std::shared_ptr<gaden::PlaybackSimulation>& playback_out)
{
    env = std::make_shared<gaden::EnvironmentConfiguration>();
    const auto read_result = env->environment.ReadFromFile(env_root / "OccupancyGrid3D.csv");
    if (read_result == gaden::ReadResult::NO_FILE ||
        read_result == gaden::ReadResult::READING_FAILED) {
        std::cerr << "RAW_QUERY_ERROR occupancy_load\n";
        return false;
    }

    std::vector<fs::path> wind_files;
    const fs::path wind_directory = gas_results / "wind";
    if (!fs::exists(wind_directory)) {
        std::cerr << "RAW_QUERY_ERROR wind_directory_missing\n";
        return false;
    }
    for (const auto& entry : fs::directory_iterator(wind_directory)) {
        const std::string name = entry.path().filename().string();
        if (entry.is_regular_file() && name.rfind("wind_iteration_", 0) == 0)
            wind_files.push_back(entry.path());
    }
    std::sort(wind_files.begin(), wind_files.end(), [](const fs::path& a, const fs::path& b) {
        return a.filename().string() < b.filename().string();
    });
    if (wind_files.empty()) {
        std::cerr << "RAW_QUERY_ERROR wind_files_empty\n";
        return false;
    }
    env->windSequence.Initialize(wind_files, env->environment.numCells(), {});

    gaden::PlaybackSceneMetadata metadata;
    metadata.params.push_back({.startIteration = 0, .resultsDirectory = gas_results});
    metadata.gasDisplayColors.push_back({0.4f, 0.4f, 0.4f, 1.0f});
    metadata.loop = {};
    owner_out = std::make_shared<gaden::Scene>(metadata, env);
    auto playback = std::dynamic_pointer_cast<gaden::PlaybackSimulation>(owner_out->GetSimulations().at(0));
    if (!playback) {
        std::cerr << "RAW_QUERY_ERROR playback_create\n";
        return false;
    }
    scene_out = owner_out.get();
    playback_out = std::move(playback);
    std::cerr << "RAW_QUERY_READY wind_files=" << wind_files.size() << "\n";
    return true;
}

int main(int argc, char** argv)
{
    if (argc != 3) {
        std::cerr << "usage: house1_raw_query ENV_ROOT GAS_RESULTS\n";
        return 2;
    }
    std::shared_ptr<gaden::EnvironmentConfiguration> env;
    gaden::Scene* scene = nullptr;
    std::shared_ptr<gaden::Scene> scene_owner;
    std::shared_ptr<gaden::PlaybackSimulation> playback;
    if (!load_scene(argv[1], argv[2], env, scene, scene_owner, playback)) return 3;

    size_t current_iteration = std::numeric_limits<size_t>::max();
    std::cout << std::setprecision(17);
    std::string line;
    while (std::getline(std::cin, line)) {
        if (line.empty()) continue;
        std::istringstream input(line);
        size_t iteration = 0;
        double x = 0.0, y = 0.0, z = 0.0;
        if (!(input >> iteration >> x >> y >> z)) {
            std::cout << "ERR parse\n" << std::flush;
            continue;
        }
        if (iteration != current_iteration) {
            if (!playback->LoadIteration(iteration)) {
                std::cout << "ERR load_iteration " << iteration << "\n" << std::flush;
                continue;
            }
            current_iteration = iteration;
        }
        const gaden::Vector3 point(static_cast<float>(x), static_cast<float>(y), static_cast<float>(z));
        const auto gases = scene->SampleConcentrations(point);
        float concentration = 0.0f;
        for (const auto& value : gases) concentration += value.second;
        const auto wind = scene->SampleWind(point);
        std::cout << "OK " << concentration << ' ' << wind.x << ' ' << wind.y << ' ' << wind.z
                  << ' ' << env->windSequence.GetCurrentIndex() << '\n' << std::flush;
    }
    return 0;
}
