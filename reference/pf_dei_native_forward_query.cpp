#include <vector>

#include <gaden/EnvironmentConfiguration.hpp>
#include <gaden/PlaybackSimulation.hpp>
#include <gaden/Scene.hpp>
#include <gaden/internal/PathUtils.hpp>

#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <sstream>
#include <string>

// Auditable shared-library query path for PF-DEI forward-operator closure.
// This deliberately uses the same gaden::PlaybackSimulation and
// Scene::SampleConcentrations implementation as the ROS player, without ROS.
int main(int argc, char** argv)
{
    if (argc != 6)
    {
        std::cerr << "usage: pf_dei_native_forward_query "
                  << "OCCUPANCY RESULT_DIR WIND_DIR SCHEDULE_CSV OUTPUT_CSV\n";
        return 2;
    }

    const std::filesystem::path occupancy = argv[1];
    const std::filesystem::path resultDir = argv[2];
    const std::filesystem::path windDir = argv[3];
    const std::filesystem::path scheduleCsv = argv[4];
    const std::filesystem::path outputCsv = argv[5];

    auto config = std::make_shared<gaden::EnvironmentConfiguration>();
    if (config->environment.ReadFromFile(occupancy) != gaden::ReadResult::OK)
    {
        std::cerr << "PF_DEI_QUERY_OCCUPANCY_READ_FAILED\n";
        return 3;
    }
    const auto windFiles = gaden::paths::GetAllFilesInDirectory(windDir);
    if (windFiles.empty())
    {
        std::cerr << "PF_DEI_QUERY_WIND_MISSING\n";
        return 4;
    }
    config->windSequence.Initialize(windFiles, config->environment.numCells(), {});

    gaden::PlaybackSceneMetadata metadata;
    metadata.params.push_back({0, resultDir});
    metadata.gasDisplayColors.resize(1);
    gaden::Scene scene(metadata, config);
    auto playback = std::dynamic_pointer_cast<gaden::PlaybackSimulation>(
        scene.GetSimulations().at(0));
    if (!playback)
    {
        std::cerr << "PF_DEI_QUERY_PLAYBACK_CAST_FAILED\n";
        return 5;
    }

    std::ifstream input(scheduleCsv);
    std::ofstream output(outputCsv);
    if (!input || !output)
    {
        std::cerr << "PF_DEI_QUERY_CSV_OPEN_FAILED\n";
        return 6;
    }
    output << "sample_id,sample_time_s,iteration,x,y,z,concentration_ppm,wind_u,wind_v,wind_w\n";
    output << std::setprecision(17);

    std::string line;
    std::getline(input, line); // header
    size_t count = 0;
    while (std::getline(input, line))
    {
        if (line.empty())
            continue;
        std::stringstream row(line);
        std::string field;
        std::string sampleId;
        double sampleTime = 0;
        int iteration = 0;
        double x = 0, y = 0, z = 0;
        std::getline(row, sampleId, ',');
        std::getline(row, field, ','); sampleTime = std::stod(field);
        std::getline(row, field, ','); iteration = std::stoi(field);
        std::getline(row, field, ','); x = std::stod(field);
        std::getline(row, field, ','); y = std::stod(field);
        std::getline(row, field, ','); z = std::stod(field);

        if (!playback->LoadIteration(static_cast<size_t>(iteration)))
        {
            std::cerr << "PF_DEI_QUERY_ITERATION_MISSING=" << iteration << "\n";
            return 7;
        }
        const gaden::Vector3 point(x, y, z);
        if (!config->environment.IsInBounds(point))
        {
            std::cerr << "PF_DEI_QUERY_OUT_OF_BOUNDS=" << sampleId << "\n";
            return 8;
        }
        float concentration = 0.0f;
        for (const auto& value : scene.SampleConcentrations(point))
            concentration += value.second;
        const auto wind = scene.SampleWind(point);
        output << sampleId << ',' << sampleTime << ',' << iteration << ',' << x << ',' << y << ',' << z
               << ',' << concentration << ',' << wind.x << ',' << wind.y << ',' << wind.z << '\n';
        ++count;
    }
    std::cout << "PF_DEI_NATIVE_FORWARD_QUERY_PASS samples=" << count << '\n';
    return 0;
}
