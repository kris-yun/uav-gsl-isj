#include "gaden/RunningSimulation.hpp"
#include "gaden/datatypes/sources/PointSource.hpp"
#include <rclcpp/rclcpp.hpp>

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

struct Sample { double time_s{}; float x{}, y{}, z{}; };

static std::vector<Sample> read_schedule(const std::filesystem::path& path) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("PF_DEI_V3_WIND_SCHEDULE_OPEN_FAILED:" + path.string());
    std::string line; std::getline(input, line);
    std::vector<Sample> out;
    while (std::getline(input, line)) {
        if (line.empty()) continue;
        std::stringstream row(line); std::string field; Sample s;
        std::getline(row, field, ','); s.time_s=std::stod(field);
        std::getline(row, field, ',');
        std::getline(row, field, ','); s.x=std::stof(field);
        std::getline(row, field, ','); s.y=std::stof(field);
        std::getline(row, field, ','); s.z=std::stof(field);
        if (!std::isfinite(s.time_s)||!std::isfinite(s.x)||!std::isfinite(s.y)||!std::isfinite(s.z))
            throw std::runtime_error("PF_DEI_V3_WIND_SCHEDULE_NONFINITE");
        out.push_back(s);
    }
    if (out.empty()) throw std::runtime_error("PF_DEI_V3_WIND_SCHEDULE_EMPTY");
    for (size_t i=1;i<out.size();++i) if (!(out[i].time_s>out[i-1].time_s))
        throw std::runtime_error("PF_DEI_V3_WIND_SCHEDULE_NOT_STRICTLY_MONOTONE");
    return out;
}

template <class T> static void write_scalar(std::ofstream& f, const T& value) {
    f.write(reinterpret_cast<const char*>(&value), sizeof(T));
}

int main(int argc, char** argv) {
    if (argc < 6) {
        std::cerr << "usage: pf_dei_v3_native_wind_multistream ENV WIND_DIR DT OUTPUT_BIN SCHEDULE_CSV...\n";
        return 2;
    }
    rclcpp::init(argc, argv);
    try {
        const std::filesystem::path env_path=argv[1], wind_dir=argv[2], output_path=argv[4];
        const float dt=std::stof(argv[3]);
        if (!(dt>0.f)||!std::isfinite(dt)) throw std::runtime_error("PF_DEI_V3_WIND_BAD_DT");
        std::vector<std::vector<Sample>> schedules;
        for (int i=5;i<argc;++i) schedules.push_back(read_schedule(argv[i]));

        auto config=std::make_shared<gaden::EnvironmentConfiguration>();
        if (config->environment.ReadFromFile(env_path)!=gaden::ReadResult::OK)
            throw std::runtime_error("PF_DEI_V3_WIND_OCCUPANCY_READ_FAILED");
        std::vector<std::filesystem::path> winds;
        for(int i=0;i<11;++i) winds.push_back(wind_dir/("wind_iteration_"+std::to_string(i)));
        config->windSequence.Initialize(winds,config->environment.numCells(),gaden::LoopConfig{.loop=true,.from=1,.to=10});
        // RunningSimulation::SampleWind adds this optional runtime field. The
        // direct CLI has no disturbance model, so materialize the native zero
        // field explicitly rather than leaving the vector empty.
        config->localAirflowDisturbances.assign(config->environment.numCells(), gaden::Vector3{0.f,0.f,0.f});
        double max_time=0.; for(const auto& s:schedules) max_time=std::max(max_time,s.back().time_s);

        auto source=std::make_shared<gaden::PointSource>();
        source->sourcePosition={schedules[0][0].x,schedules[0][0].y,schedules[0][0].z};
        source->gasType=gaden::GasType::methane;
        gaden::RunningSimulation::Parameters p; p.source=source; p.deltaTime=dt; p.windIterationDeltaTime=1.f;
        p.temperature=298.f; p.pressure=1.f; p.numFilaments_sec=0.f;
        p.expectedNumIterations=static_cast<size_t>(std::ceil(max_time/dt))+1;
        p.windLoop=gaden::LoopConfig{.loop=true,.from=1,.to=10}; p.saveResults=false; p.preCalculateConcentrations=false;
        gaden::RunningSimulation sim(p,config);

        std::vector<std::vector<float>> values(schedules.size());
        for(size_t k=0;k<schedules.size();++k) values[k].reserve(3*schedules[k].size());
        std::vector<size_t> index(schedules.size(),0); size_t remaining=0;
        for(const auto& schedule:schedules) remaining+=schedule.size();
        double sim_time=0.;
        while(remaining) {
            double next=std::numeric_limits<double>::infinity();
            for(size_t k=0;k<schedules.size();++k)
                if(index[k]<schedules[k].size()) next=std::min(next,schedules[k][index[k]].time_s);
            while(sim_time+1e-9<next) { sim.AdvanceTimestep(); sim_time+=dt; }
            for(size_t k=0;k<schedules.size();++k) {
                while(index[k]<schedules[k].size() && std::abs(schedules[k][index[k]].time_s-next)<1e-8) {
                    const auto& s=schedules[k][index[k]]; const gaden::Vector3 point{s.x,s.y,s.z};
                    if(!config->environment.IsInBounds(point)) throw std::runtime_error("PF_DEI_V3_WIND_QUERY_OUT_OF_BOUNDS");
                    const auto point_indices=config->environment.coordsToIndices(point);
                    const auto point_index=config->environment.indexFrom3D(point_indices);
                    gaden::Vector3 wind;
                    try {
                        // RunningSimulation's index overload hides the base
                        // point overload; pass explicit native voxel indices.
                        wind=sim.SampleWind(point_indices);
                    } catch (const std::exception& error) {
                        std::ostringstream detail;
                        detail << "PF_DEI_V3_WIND_SAMPLE_FAILED trajectory=" << k
                               << " index=" << index[k] << " time=" << s.time_s
                               << " xyz=" << s.x << ',' << s.y << ',' << s.z
                               << " ijk=" << point_indices.x << ',' << point_indices.y << ',' << point_indices.z
                               << " flat=" << point_index
                               << " cause=" << error.what();
                        throw std::runtime_error(detail.str());
                    }
                    if(!std::isfinite(wind.x)||!std::isfinite(wind.y)||!std::isfinite(wind.z))
                        throw std::runtime_error("PF_DEI_V3_WIND_NONFINITE");
                    values[k].push_back(wind.x); values[k].push_back(wind.y); values[k].push_back(wind.z);
                    ++index[k]; --remaining;
                }
            }
        }

        std::ofstream output(output_path,std::ios::binary);
        if(!output) throw std::runtime_error("PF_DEI_V3_WIND_OUTPUT_OPEN_FAILED");
        const std::array<char,8> magic{'P','F','V','3','W','N','D','1'}; output.write(magic.data(),magic.size());
        const std::uint32_t count=static_cast<std::uint32_t>(values.size()); write_scalar(output,count);
        for(const auto& trajectory:values) {
            const std::uint32_t n=static_cast<std::uint32_t>(trajectory.size()/3); write_scalar(output,n);
        }
        for(const auto& trajectory:values)
            output.write(reinterpret_cast<const char*>(trajectory.data()),trajectory.size()*sizeof(float));
        if(!output) throw std::runtime_error("PF_DEI_V3_WIND_OUTPUT_WRITE_FAILED");
        size_t samples=0; for(const auto& trajectory:values) samples+=trajectory.size()/3;
        std::cout<<"PF_DEI_V3_NATIVE_WIND_MULTISTREAM=PASS trajectories="<<count<<" samples="<<samples<<'\n';
    } catch(const std::exception& e) { std::cerr<<e.what()<<'\n'; rclcpp::shutdown(); return 3; }
    rclcpp::shutdown(); return 0;
}
