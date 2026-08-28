#include "gaden/RunningSimulation.hpp"
#include "gaden/datatypes/sources/PointSource.hpp"
#include <rclcpp/rclcpp.hpp>

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

extern "C" void gaden_initialize_random_engines(std::uint64_t);

struct Sample {
    double time_s{};
    std::uint64_t step{};
    float x{}, y{}, z{};
};

static std::vector<Sample> read_schedule(const std::filesystem::path& path) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("PF_DEI_V3_SCHEDULE_OPEN_FAILED");
    std::string line;
    std::getline(input, line);
    std::vector<Sample> out;
    while (std::getline(input, line)) {
        if (line.empty()) continue;
        std::stringstream row(line);
        std::string field;
        Sample s;
        std::getline(row, field, ','); s.time_s = std::stod(field);
        std::getline(row, field, ','); s.step = std::stoull(field);
        std::getline(row, field, ','); s.x = std::stof(field);
        std::getline(row, field, ','); s.y = std::stof(field);
        std::getline(row, field, ','); s.z = std::stof(field);
        if (!std::isfinite(s.time_s) || !std::isfinite(s.x) || !std::isfinite(s.y) || !std::isfinite(s.z))
            throw std::runtime_error("PF_DEI_V3_SCHEDULE_NONFINITE");
        out.push_back(s);
    }
    if (out.empty()) throw std::runtime_error("PF_DEI_V3_SCHEDULE_EMPTY");
    if (!std::is_sorted(out.begin(), out.end(), [](const Sample& a, const Sample& b){ return a.time_s < b.time_s; }))
        throw std::runtime_error("PF_DEI_V3_SCHEDULE_NOT_MONOTONE");
    return out;
}

int main(int argc, char** argv) {
    if (argc != 10) {
        std::cerr << "usage: pf_dei_v3_native_stream ENV WIND_DIR SOURCE_X SOURCE_Y SOURCE_Z SEED SCHEDULE_CSV OUTPUT_CSV DT\n";
        return 2;
    }
    rclcpp::init(argc, argv);
    try {
        const auto env_path = std::filesystem::path(argv[1]);
        const auto wind_dir = std::filesystem::path(argv[2]);
        const auto source_xyz = gaden::Vector3{std::stof(argv[3]), std::stof(argv[4]), std::stof(argv[5])};
        const auto seed = std::stoull(argv[6]);
        const auto schedule = read_schedule(argv[7]);
        const auto output_path = std::filesystem::path(argv[8]);
        const float dt = std::stof(argv[9]);
        if (!(dt > 0.f) || !std::isfinite(dt)) throw std::runtime_error("PF_DEI_V3_BAD_DT");

        auto config = std::make_shared<gaden::EnvironmentConfiguration>();
        if (config->environment.ReadFromFile(env_path) != gaden::ReadResult::OK)
            throw std::runtime_error("PF_DEI_V3_OCCUPANCY_READ_FAILED");
        std::vector<std::filesystem::path> winds;
        for (int i = 0; i < 11; ++i) winds.push_back(wind_dir / ("wind_iteration_" + std::to_string(i)));
        config->windSequence.Initialize(winds, config->environment.numCells(), gaden::LoopConfig{.loop=true,.from=1,.to=10});
        if (!config->environment.IsInBounds(source_xyz)) throw std::runtime_error("PF_DEI_V3_SOURCE_OUT_OF_BOUNDS");

        auto source = std::make_shared<gaden::PointSource>();
        source->sourcePosition = source_xyz;
        source->gasType = gaden::GasType::methane;
        gaden::RunningSimulation::Parameters p;
        p.source=source; p.deltaTime=dt; p.windIterationDeltaTime=1.f; p.temperature=298.f; p.pressure=1.f;
        p.filamentPPMcenter_initial=10.f; p.filamentInitialSigma=10.f; p.filamentGrowthGamma=15.f;
        p.filamentNoise_std=.01f; p.numFilaments_sec=7.f;
        p.expectedNumIterations=static_cast<size_t>(std::ceil(schedule.back().time_s/dt))+1;
        p.windLoop=gaden::LoopConfig{.loop=true,.from=1,.to=10}; p.saveResults=false; p.preCalculateConcentrations=false;
        gaden_initialize_random_engines(seed);
        gaden::RunningSimulation sim(p, config);

        std::ofstream output(output_path);
        if (!output) throw std::runtime_error("PF_DEI_V3_OUTPUT_OPEN_FAILED");
        output << "t_sim_s,step,x,y,z,physical_ppm\n" << std::setprecision(9);
        double sim_time = 0.0;
        for (const auto& sample : schedule) {
            while (sim_time + 1e-9 < sample.time_s) {
                sim.AdvanceTimestep();
                sim_time += dt;
            }
            const gaden::Vector3 point{sample.x, sample.y, sample.z};
            if (!config->environment.IsInBounds(point)) throw std::runtime_error("PF_DEI_V3_QUERY_OUT_OF_BOUNDS");
            const float ppm = sim.SampleConcentration(point);
            if (!std::isfinite(ppm) || ppm < 0.f) throw std::runtime_error("PF_DEI_V3_INVALID_PPM");
            output << sample.time_s << ',' << sample.step << ',' << sample.x << ',' << sample.y << ',' << sample.z << ',' << ppm << '\n';
        }
        std::cout << "PF_DEI_V3_NATIVE_STREAM=PASS samples=" << schedule.size() << " seed=" << seed << '\n';
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n';
        rclcpp::shutdown();
        return 3;
    }
    rclcpp::shutdown();
    return 0;
}
