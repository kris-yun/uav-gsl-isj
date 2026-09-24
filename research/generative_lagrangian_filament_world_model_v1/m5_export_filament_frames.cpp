#include <gaden/gaden.hpp>
#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <regex>
#include <string>
#include <vector>

namespace fs = std::filesystem;

static std::vector<fs::path> sorted_winds(const fs::path& dir) {
    std::regex re("^wind_iteration_([0-9]+)$");
    std::vector<std::pair<int,fs::path>> tmp;
    for (const auto& e : fs::directory_iterator(dir)) {
        if (!e.is_regular_file()) continue;
        std::smatch m;
        auto name=e.path().filename().string();
        if (std::regex_match(name,m,re)) tmp.emplace_back(std::stoi(m[1].str()),e.path());
    }
    std::sort(tmp.begin(),tmp.end(),[](auto const& a, auto const& b){return a.first<b.first;});
    std::vector<fs::path> out;
    for (auto const& p:tmp) out.push_back(p.second);
    return out;
}

static uint32_t stencil27(const gaden::Environment& env, const gaden::Vector3i& c) {
    uint32_t bits=0, bit=0;
    for(int dz=-1;dz<=1;dz++)
        for(int dy=-1;dy<=1;dy++)
            for(int dx=-1;dx<=1;dx++,bit++) {
                gaden::Vector3i q{c.x+dx,c.y+dy,c.z+dz};
                bool blocked=!env.IsInBounds(q) || env.at(q)!=gaden::Environment::CellState::Free;
                if(blocked) bits |= (uint32_t(1)<<bit);
            }
    return bits;
}

int main(int argc,char** argv){
    if(argc<6){
        std::cerr<<"usage: "<<argv[0]
                 <<" OCCUPANCY WIND_DIR RESULTS_DIR START_ITER MAX_FRAMES [OUT.csv]\n";
        return 2;
    }
    fs::path occupancy=argv[1], windDir=argv[2], resultsDir=argv[3];
    size_t start=std::stoull(argv[4]), maxFrames=std::stoull(argv[5]);
    fs::path outPath = argc>=7 ? fs::path(argv[6]) : fs::path("filament_frames.csv");

    auto cfg=std::make_shared<gaden::EnvironmentConfiguration>();
    auto rr=cfg->environment.ReadFromFile(occupancy);
    if(rr!=gaden::ReadResult::OK){std::cerr<<"occupancy read failed\n";return 3;}
    auto windFiles=sorted_winds(windDir);
    if(windFiles.empty()){std::cerr<<"no wind_iteration_* in "<<windDir<<"\n";return 4;}
    cfg->windSequence.Initialize(windFiles,cfg->environment.numCells(),{});

    gaden::PlaybackSimulation::Parameters pp;
    pp.startIteration=start;
    pp.resultsDirectory=resultsDir;
    gaden::PlaybackSimulation sim(pp,cfg,{});

    std::ofstream out(outPath);
    if(!out){std::cerr<<"cannot open "<<outPath<<"\n";return 5;}
    out<<"frame,iteration,row,x,y,z,sigma,wind_x,wind_y,wind_z,cell_x,cell_y,cell_z,stencil27\n";

    size_t frames=0, rows=0;
    for(size_t f=0; f<maxFrames; ++f){
        size_t iteration=start+f;
        fs::path fp=resultsDir/("iteration_"+std::to_string(iteration));
        if(!fs::exists(fp)) break;
        sim.AdvanceTimestep();
        if(sim.GetMode()!=gaden::PlaybackSimulation::Mode::Filaments){
            std::cerr<<"iteration "<<iteration<<" is not filament mode\n"; return 6;
        }
        const auto& fil=sim.GetFilaments();
        for(size_t i=0;i<fil.size();++i){
            const auto& q=fil[i];
            auto w=sim.SampleWind(q.position);
            auto c=cfg->environment.coordsToIndices(q.position);
            uint32_t st=stencil27(cfg->environment,c);
            out<<f<<','<<iteration<<','<<i<<','
               <<q.position.x<<','<<q.position.y<<','<<q.position.z<<','<<q.sigma<<','
               <<w.x<<','<<w.y<<','<<w.z<<','
               <<c.x<<','<<c.y<<','<<c.z<<','<<st<<'\n';
            rows++;
        }
        frames++;
        if((f%100)==0) std::cerr<<"frame "<<f<<" filaments "<<fil.size()<<"\n";
    }
    out.close();
    std::cerr<<"exported frames="<<frames<<" rows="<<rows<<" to "<<outPath<<"\n";
    if(frames<2) return 7;
    return 0;
}
