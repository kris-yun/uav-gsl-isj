#include "gaden/RunningSimulation.hpp"
#include "gaden/datatypes/sources/PointSource.hpp"
#include <rclcpp/rclcpp.hpp>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>
#include <vector>

extern "C" void gaden_initialize_random_engines(std::uint64_t);

struct Sample { double time_s{}; float x{}, y{}, z{}; };

static std::vector<Sample> read_schedule(const std::filesystem::path& path) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("PF_DEI_V3_SCHEDULE_OPEN_FAILED:" + path.string());
    std::string line; std::getline(input, line);
    std::vector<Sample> out;
    while (std::getline(input, line)) {
        if (line.empty()) continue;
        std::stringstream row(line); std::string field; Sample s;
        std::getline(row, field, ','); s.time_s=std::stod(field);
        std::getline(row, field, ','); // step
        std::getline(row, field, ','); s.x=std::stof(field);
        std::getline(row, field, ','); s.y=std::stof(field);
        std::getline(row, field, ','); s.z=std::stof(field);
        if (!std::isfinite(s.time_s)||!std::isfinite(s.x)||!std::isfinite(s.y)||!std::isfinite(s.z))
            throw std::runtime_error("PF_DEI_V3_SCHEDULE_NONFINITE");
        out.push_back(s);
    }
    if (out.empty()) throw std::runtime_error("PF_DEI_V3_SCHEDULE_EMPTY");
    for (size_t i=1;i<out.size();++i) if (!(out[i].time_s>out[i-1].time_s))
        throw std::runtime_error("PF_DEI_V3_SCHEDULE_NOT_STRICTLY_MONOTONE");
    return out;
}

template <class T> static void write_scalar(std::ofstream& f, const T& value) {
    f.write(reinterpret_cast<const char*>(&value), sizeof(T));
}

int main(int argc, char** argv) {
    if (argc < 10) {
        std::cerr << "usage: pf_dei_v3_native_multistream ENV WIND_DIR X Y Z SEED DT OUTPUT_BIN SCHEDULE_CSV...\n";
        return 2;
    }
    rclcpp::init(argc, argv);
    try {
        const std::filesystem::path env_path=argv[1], wind_dir=argv[2], output_path=argv[8];
        const gaden::Vector3 source_xyz{std::stof(argv[3]),std::stof(argv[4]),std::stof(argv[5])};
        const auto seed=std::stoull(argv[6]); const float dt=std::stof(argv[7]);
        if (!(dt>0.f)||!std::isfinite(dt)) throw std::runtime_error("PF_DEI_V3_BAD_DT");
        std::vector<std::filesystem::path> schedule_paths;
        std::vector<std::vector<Sample>> schedules;
        for (int i=9;i<argc;++i) { schedule_paths.emplace_back(argv[i]); schedules.push_back(read_schedule(argv[i])); }

        auto config=std::make_shared<gaden::EnvironmentConfiguration>();
        if (config->environment.ReadFromFile(env_path)!=gaden::ReadResult::OK) throw std::runtime_error("PF_DEI_V3_OCCUPANCY_READ_FAILED");
        std::vector<std::filesystem::path> winds;
        for(int i=0;i<11;++i) winds.push_back(wind_dir/("wind_iteration_"+std::to_string(i)));
        config->windSequence.Initialize(winds,config->environment.numCells(),gaden::LoopConfig{.loop=true,.from=1,.to=10});
        if(!config->environment.IsInBounds(source_xyz)) throw std::runtime_error("PF_DEI_V3_SOURCE_OUT_OF_BOUNDS");
        double max_time=0.; for(const auto& s:schedules) max_time=std::max(max_time,s.back().time_s);
        auto source=std::make_shared<gaden::PointSource>(); source->sourcePosition=source_xyz; source->gasType=gaden::GasType::methane;
        gaden::RunningSimulation::Parameters p; p.source=source; p.deltaTime=dt; p.windIterationDeltaTime=1.f; p.temperature=298.f; p.pressure=1.f;
        p.filamentPPMcenter_initial=10.f; p.filamentInitialSigma=10.f; p.filamentGrowthGamma=15.f; p.filamentNoise_std=.01f; p.numFilaments_sec=7.f;
        p.expectedNumIterations=static_cast<size_t>(std::ceil(max_time/dt))+1; p.windLoop=gaden::LoopConfig{.loop=true,.from=1,.to=10}; p.saveResults=false; p.preCalculateConcentrations=false;
        gaden_initialize_random_engines(seed); gaden::RunningSimulation sim(p,config);

        std::vector<std::vector<float>> ppm(schedules.size());
        for(size_t k=0;k<schedules.size();++k) ppm[k].reserve(schedules[k].size());
        std::vector<size_t> index(schedules.size(),0); size_t remaining=0; for(const auto& s:schedules) remaining+=s.size();
        double sim_time=0.;
        while(remaining) {
            double next=std::numeric_limits<double>::infinity();
            for(size_t k=0;k<schedules.size();++k) if(index[k]<schedules[k].size()) next=std::min(next,schedules[k][index[k]].time_s);
            while(sim_time+1e-9<next) { sim.AdvanceTimestep(); sim_time+=dt; }
            for(size_t k=0;k<schedules.size();++k) {
                while(index[k]<schedules[k].size() && std::abs(schedules[k][index[k]].time_s-next)<1e-8) {
                    const auto& s=schedules[k][index[k]]; const gaden::Vector3 point{s.x,s.y,s.z};
                    if(!config->environment.IsInBounds(point)) throw std::runtime_error("PF_DEI_V3_QUERY_OUT_OF_BOUNDS");
                    const float value=sim.SampleConcentration(point);
                    if(!std::isfinite(value)||value<0.f) throw std::runtime_error("PF_DEI_V3_INVALID_PPM");
                    ppm[k].push_back(value); ++index[k]; --remaining;
                }
            }
        }

        std::ofstream output(output_path,std::ios::binary);
        if(!output) throw std::runtime_error("PF_DEI_V3_OUTPUT_OPEN_FAILED");
        const std::array<char,8> magic{'P','F','V','3','S','T','R','1'}; output.write(magic.data(),magic.size());
        const std::uint32_t count=static_cast<std::uint32_t>(ppm.size()); write_scalar(output,count);
        for(const auto& values:ppm){ const std::uint32_t n=static_cast<std::uint32_t>(values.size()); write_scalar(output,n); }
        for(const auto& values:ppm) output.write(reinterpret_cast<const char*>(values.data()),values.size()*sizeof(float));
        if(!output) throw std::runtime_error("PF_DEI_V3_OUTPUT_WRITE_FAILED");
        std::cout<<"PF_DEI_V3_NATIVE_MULTISTREAM=PASS trajectories="<<count<<" samples=";
        size_t total=0; for(const auto& values:ppm) total+=values.size(); std::cout<<total<<" seed="<<seed<<'\n';
    } catch(const std::exception& e) { std::cerr<<e.what()<<'\n'; rclcpp::shutdown(); return 3; }
    rclcpp::shutdown(); return 0;
}
