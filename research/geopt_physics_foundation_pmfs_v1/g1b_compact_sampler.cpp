// M6 G1-B compact, source-blind GADEN sampler.
// This executable links against the audited seeded GADEN build and writes only
// sensor-plane samples. GADEN_RNG_SEED is supplied before process start.
#include <rclcpp/rclcpp.hpp>
#include "gaden/EnvironmentConfiguration.hpp"
#include "gaden/RunningSimulation.hpp"
#include "gaden/datatypes/GasTypes.hpp"
#include "gaden/datatypes/sources/PointSource.hpp"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;
using namespace gaden;

namespace {
struct GridPoint { std::size_t cell_index{}; int grid_i{}; int grid_j{}; float x{}; float y{}; };

std::vector<std::string> split_csv(std::string const& line) {
    std::vector<std::string> out; std::stringstream ss(line); std::string item;
    while (std::getline(ss, item, ',')) out.push_back(item);
    return out;
}

std::vector<GridPoint> read_free_grid(fs::path const& path) {
    std::ifstream in(path); if (!in) throw std::runtime_error("cannot open grid csv");
    std::string line; if (!std::getline(in, line)) throw std::runtime_error("empty grid csv");
    std::vector<GridPoint> points;
    while (std::getline(in, line)) {
        if (line.empty()) continue;
        auto c = split_csv(line); if (c.size() < 6) throw std::runtime_error("malformed grid csv row");
        if (c[5] != "Free") continue;
        points.push_back(GridPoint{static_cast<std::size_t>(std::stoull(c[0])), std::stoi(c[1]),
                                   std::stoi(c[2]), std::stof(c[3]), std::stof(c[4])});
    }
    return points;
}

template <typename T> void write_binary(fs::path const& path, std::vector<T> const& values) {
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) throw std::runtime_error("cannot write " + path.string());
    out.write(reinterpret_cast<char const*>(values.data()), static_cast<std::streamsize>(values.size() * sizeof(T)));
    if (!out) throw std::runtime_error("short write " + path.string());
}

std::string json_escape(std::string const& s) {
    std::string out; for (char ch : s) { if (ch == '\\' || ch == '"') out.push_back('\\'); out.push_back(ch); }
    return out;
}
} // namespace

int main(int argc, char** argv) {
    // occ wind_dir grid_csv sx sy sz seed source_id split out_dir
    if (argc != 11) {
        std::cerr << "usage: sampler <occupancy> <wind_dir> <grid_csv> <sx> <sy> <sz> <seed> <source_id> <split> <out_dir>\n";
        return 2;
    }
    const fs::path occupancy_path = argv[1], wind_dir = argv[2], grid_csv = argv[3], out_dir = argv[10];
    const float source_x = std::stof(argv[4]), source_y = std::stof(argv[5]), source_z = std::stof(argv[6]);
    const std::uint64_t seed = std::stoull(argv[7]);
    const std::string source_id = argv[8], split = argv[9];
    const char* env_seed = std::getenv("GADEN_RNG_SEED");
    if (!env_seed || std::stoull(env_seed) != seed) { std::cerr << "GADEN_RNG_SEED mismatch\n"; return 3; }

    try {
        fs::create_directories(out_dir);
        auto grid = read_free_grid(grid_csv);
        if (grid.size() != 631) throw std::runtime_error("expected 631 free rows");
        auto env = std::make_shared<EnvironmentConfiguration>();
        if (env->environment.ReadFromFile(occupancy_path) != ReadResult::OK) throw std::runtime_error("occupancy read failed");
        std::vector<fs::path> wind_files; for (int i = 0; i <= 10; ++i) wind_files.push_back(wind_dir / ("wind_iteration_" + std::to_string(i)));
        env->windSequence.Initialize(wind_files, env->environment.numCells(), LoopConfig{true, 1, 10});
        for (auto const& p : grid) {
            Vector3 q{p.x, p.y, 0.30f};
            if (!env->environment.IsInBounds(q) || env->environment.at(q) != Environment::CellState::Free)
                throw std::runtime_error("grid point not free at sensor z");
        }
        Vector3 source{source_x, source_y, source_z};
        if (!env->environment.IsInBounds(source) || env->environment.at(source) != Environment::CellState::Free)
            throw std::runtime_error("source point not free");

        RunningSimulation::Parameters params;
        params.source = std::make_shared<PointSource>(); params.source->gasType = GasType::butane; params.source->sourcePosition = source;
        params.deltaTime = 0.1f; params.windIterationDeltaTime = 1.0f; params.temperature = 298.0f; params.pressure = 1.0f;
        params.filamentPPMcenter_initial = 10.0f; params.filamentInitialSigma = 10.0f; params.filamentGrowthGamma = 15.0f;
        params.filamentNoise_std = 0.01f; params.numFilaments_sec = 7.0f; params.expectedNumIterations = 3000;
        params.windLoop = LoopConfig{true, 1, 10}; params.saveResults = false; params.preCalculateConcentrations = false;

        int ros_argc = 0; char** ros_argv = nullptr; rclcpp::init(ros_argc, ros_argv);
        RunningSimulation sim(params, env);
        constexpr int kSteps = 3000, kBurnInStep = 500, kSampleStep = 10, kSampleCount = 250;
        constexpr float kThreshold = 0.1f; const std::size_t n = grid.size();
        std::vector<std::uint8_t> hit_samples(static_cast<std::size_t>(kSampleCount) * n, 0);
        std::vector<double> sum(n, 0.0), sum_sq(n, 0.0); int sample_idx = 0;
        for (int step = 1; step <= kSteps; ++step) {
            sim.AdvanceTimestep();
            if (step < kBurnInStep || step >= kSteps || ((step - kBurnInStep) % kSampleStep) != 0) continue;
            if (sample_idx >= kSampleCount) throw std::runtime_error("too many samples");
            for (std::size_t j = 0; j < n; ++j) {
                float c = sim.SampleConcentration(Vector3{grid[j].x, grid[j].y, 0.30f});
                if (!std::isfinite(c)) throw std::runtime_error("non-finite concentration");
                sum[j] += c; sum_sq[j] += static_cast<double>(c) * c;
                hit_samples[static_cast<std::size_t>(sample_idx) * n + j] = static_cast<std::uint8_t>(c > kThreshold);
            }
            ++sample_idx;
        }
        if (sample_idx != kSampleCount) throw std::runtime_error("sample count mismatch");
        std::vector<float> hit_frequency(n), mean_concentration(n), variance(n), hit_frequency_100(n);
        for (std::size_t j = 0; j < n; ++j) {
            int hits = 0, hits100 = 0;
            for (int i = 0; i < sample_idx; ++i) {
                hits += hit_samples[static_cast<std::size_t>(i) * n + j] != 0;
                if (i >= 50) hits100 += hit_samples[static_cast<std::size_t>(i) * n + j] != 0;
            }
            hit_frequency[j] = static_cast<float>(hits) / sample_idx;
            hit_frequency_100[j] = static_cast<float>(hits100) / (sample_idx - 50);
            mean_concentration[j] = static_cast<float>(sum[j] / sample_idx);
            double m = sum[j] / sample_idx; variance[j] = static_cast<float>(std::max(0.0, sum_sq[j] / sample_idx - m * m));
        }
        write_binary(out_dir / "hit_samples_u8.bin", hit_samples);
        write_binary(out_dir / "hit_frequency_f32.bin", hit_frequency);
        write_binary(out_dir / "mean_concentration_f32.bin", mean_concentration);
        write_binary(out_dir / "variance_concentration_f32.bin", variance);
        write_binary(out_dir / "hit_frequency_window100_f32.bin", hit_frequency_100);
        std::ofstream meta(out_dir / "metadata.json", std::ios::trunc);
        meta << std::setprecision(9) << "{\n"
             << "  \"source_id\": \"" << json_escape(source_id) << "\",\n"
             << "  \"split\": \"" << json_escape(split) << "\",\n"
             << "  \"seed\": " << seed << ",\n"
             << "  \"source_xyz\": [" << source_x << ", " << source_y << ", " << source_z << "],\n"
             << "  \"sensor_z\": 0.30, \"threshold\": 0.1, \"horizon_s\": 300, \"burn_in_s\": 50,\n"
             << "  \"sample_start_s\": 50, \"sample_end_s_exclusive\": 300, \"sample_hz\": 1, \"sample_count\": " << sample_idx << ",\n"
             << "  \"grid_count_free\": " << n << ", \"delta_time_s\": 0.1, \"wind_iteration_delta_s\": 1.0,\n"
             << "  \"wind_loop\": [1, 10], \"gas_type\": \"butane\", \"num_filaments_sec\": 7.0,\n"
             << "  \"filament_ppm_center\": 10.0, \"filament_initial_sigma_cm\": 10.0,\n"
             << "  \"filament_growth_gamma_cm2_s\": 15.0, \"filament_noise_std\": 0.01,\n"
             << "  \"compact_outputs_only\": true\n}\n";
        meta.close(); if (!meta) throw std::runtime_error("metadata write failed");
        rclcpp::shutdown();
        std::cout << "G1B_SAMPLER_OK source=" << source_id << " seed=" << seed << " samples=" << sample_idx << " free=" << n << "\n";
        return 0;
    } catch (std::exception const& e) {
        std::cerr << "G1B_SAMPLER_ERROR " << e.what() << "\n";
        if (rclcpp::ok()) rclcpp::shutdown(); return 1;
    }
}
