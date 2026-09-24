#include <gaden/gaden.hpp>
#include <gaden/datatypes/GasTypes.hpp>
#include <algorithm>
#include <cfloat>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
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

static float dot3(const gaden::Vector3& a,const gaden::Vector3& b){
    return a.x*b.x+a.y*b.y+a.z*b.z;
}
static float len3(const gaden::Vector3& a){ return std::sqrt(dot3(a,a)); }

static gaden::Environment::CellState step_towards(
    const gaden::Environment& env, gaden::Vector3& pos, const gaden::Vector3& end, int depth=0)
{
    if(depth>16) return env.at(pos);
    auto startCell=env.coordsToIndices(pos);
    auto endCell=env.coordsToIndices(end);
    if(startCell==endCell){ pos=end; return env.at(startCell); }

    gaden::Vector3 d=end-pos;
    float dist=len3(d);
    if(!(dist>0)) return env.at(pos);
    gaden::Vector3 dir=d*(1.0f/dist);
    int steps=std::max(1,(int)std::ceil(dist/env.description.cellSize));
    float inc=dist/steps;
    for(int i=0;i<steps;i++){
        gaden::Vector3 previous=pos;
        pos=pos+dir*inc;
        auto state=env.at(pos);
        if(state==gaden::Environment::CellState::Obstacle ||
           state==gaden::Environment::CellState::OutOfBounds){
            auto prevCell=env.coordsToIndices(previous);
            auto currCell=env.coordsToIndices(pos);
            gaden::Vector3 normal{
                float(prevCell.x-currCell.x),
                float(prevCell.y-currCell.y),
                float(prevCell.z-currCell.z)};
            pos=previous;
            gaden::Vector3 rem=end-pos;
            float nn=dot3(normal,normal);
            gaden::Vector3 proj = nn>0 ? normal*(dot3(rem,normal)/nn) : gaden::Vector3{0,0,0};
            gaden::Vector3 rejected=rem-proj;
            if(len3(rejected)<1e-9f) return env.at(pos);
            return step_towards(env,pos,pos+rejected,depth+1);
        }
        if(state==gaden::Environment::CellState::Outlet) return state;
    }
    return gaden::Environment::CellState::Free;
}

static float concentration_at_center(
    const gaden::Filament& f, const gaden::SimulationMetadata::Constants& c)
{
    constexpr float pi=3.14159265358979323846f;
    float numTarget = c.totalMolesInFilament /
        (std::sqrt(8.0f*pi*pi*pi)*f.sigma*f.sigma*f.sigma);
    return 1e6f*numTarget/c.numMolesAllGasesIncm3;
}

static std::vector<size_t> save_steps(size_t physicsSteps,float dt,float saveDt){
    std::vector<size_t> out;
    float current=0.0f, last=-FLT_MAX;
    for(size_t step=0;step<physicsSteps;step++){
        if(current > last + saveDt){ out.push_back(step); last=current; }
        current += dt;
    }
    return out;
}

static std::vector<size_t> wind_indices(
    size_t physicsSteps,float dt,float windDt,size_t nWind,size_t loopFrom,size_t loopTo)
{
    std::vector<size_t> out; out.reserve(physicsSteps);
    float current=0.0f,last=0.0f; size_t idx=0;
    for(size_t step=0;step<physicsSteps;step++){
        out.push_back(idx);
        if(current > last + windDt){
            idx++;
            if(idx>loopTo) idx=loopFrom;
            else if(idx>=nWind) idx=nWind-1;
            last=current;
        }
        current += dt;
    }
    return out;
}

static bool deterministic_predict(
    gaden::Filament& f,
    const gaden::Environment& env,
    gaden::WindSequence& winds,
    const std::vector<size_t>& windIdx,
    size_t stepBeginInclusive,
    size_t stepEndInclusive,
    float dt,
    float gamma,
    gaden::GasType gasType,
    const gaden::SimulationMetadata::Constants& constants)
{
    constexpr float g=9.8f, rhoAir=1.205f, mu=19e-6f;
    const size_t gi=static_cast<size_t>(gasType);
    for(size_t step=stepBeginInclusive; step<=stepEndInclusive; ++step){
        winds.SetCurrentIndex(windIdx.at(step));
        if(!env.IsInBounds(f.position)) return false;
        auto ci=env.coordsToIndices(f.position);
        auto w=winds.GetCurrent().at(env.indexFrom3D(ci));
        gaden::Vector3 end=f.position+w*dt;
        float buoy=(g*(1.0f-gaden::SpecificGravity.at(gi))*rhoAir*
                    concentration_at_center(f,constants)*1e-6f)/(18.0f*mu);
        end.z += buoy*dt;
        auto state=step_towards(env,f.position,end);
        if(state==gaden::Environment::CellState::Outlet) return false;
        f.sigma += gamma/(2.0f*f.sigma)*dt;
    }
    return true;
}

int main(int argc,char** argv){
    if(argc<7){
        std::cerr<<"usage: "<<argv[0]
                 <<" OCCUPANCY WIND_DIR RESULTS_DIR START_ITER MAX_FRAMES OUT.csv"
                 <<" [dt=.1] [save_dt=.5] [wind_dt=1] [loop_from=1] [loop_to=10] [gamma=15]\n";
        return 2;
    }
    fs::path occupancy=argv[1], windDir=argv[2], resultsDir=argv[3], outPath=argv[6];
    size_t start=std::stoull(argv[4]), maxFrames=std::stoull(argv[5]);
    float dt=argc>7?std::stof(argv[7]):0.1f;
    float saveDt=argc>8?std::stof(argv[8]):0.5f;
    float windDt=argc>9?std::stof(argv[9]):1.0f;
    size_t loopFrom=argc>10?std::stoull(argv[10]):1;
    size_t loopTo=argc>11?std::stoull(argv[11]):10;
    float gamma=argc>12?std::stof(argv[12]):15.0f;

    auto cfg=std::make_shared<gaden::EnvironmentConfiguration>();
    auto rr=cfg->environment.ReadFromFile(occupancy);
    if(rr!=gaden::ReadResult::OK){std::cerr<<"occupancy read failed\n";return 3;}
    auto windFiles=sorted_winds(windDir);
    if(windFiles.empty()){std::cerr<<"no wind_iteration_* in "<<windDir<<"\n";return 4;}
    cfg->windSequence.Initialize(windFiles,cfg->environment.numCells(),{});

    const size_t physicsSteps=20000;
    auto saves=save_steps(physicsSteps,dt,saveDt);
    if(saves.size()<start+maxFrames+1){
        std::cerr<<"save schedule too short\n"; return 8;
    }
    auto windIdx=wind_indices(physicsSteps,dt,windDt,windFiles.size(),loopFrom,loopTo);

    gaden::PlaybackSimulation::Parameters pp;
    pp.startIteration=start;
    pp.resultsDirectory=resultsDir;
    gaden::PlaybackSimulation sim(pp,cfg,{});

    std::ofstream out(outPath);
    if(!out){std::cerr<<"cannot open "<<outPath<<"\n";return 5;}
    out<<std::setprecision(9);
    out<<"frame,iteration,physics_step,row,x,y,z,sigma,wind_index,wind_x,wind_y,wind_z,"
          "cell_x,cell_y,cell_z,stencil27,pred_alive,pred_x,pred_y,pred_z,pred_sigma,next_step,delta_s\n";

    size_t frames=0, rows=0;
    for(size_t f=0; f<maxFrames; ++f){
        size_t iteration=start+f;
        fs::path fp=resultsDir/("iteration_"+std::to_string(iteration));
        if(!fs::exists(fp)) break;
        sim.AdvanceTimestep();
        if(sim.GetMode()!=gaden::PlaybackSimulation::Mode::Filaments){
            std::cerr<<"iteration "<<iteration<<" is not filament mode\n"; return 6;
        }
        const size_t scheduleIndex=start+f;
        const size_t k=saves.at(scheduleIndex);
        const size_t kNext=saves.at(scheduleIndex+1);
        const size_t fileWindIdx=cfg->windSequence.GetCurrentIndex();
        if(fileWindIdx!=windIdx.at(k)){
            std::cerr<<"wind-index mismatch frame "<<f<<" file="<<fileWindIdx
                     <<" reconstructed="<<windIdx.at(k)<<"\n"; return 9;
        }

        const auto& fil=sim.GetFilaments();
        for(size_t i=0;i<fil.size();++i){
            const auto& q=fil[i];
            auto w=sim.SampleWind(q.position);
            auto c=cfg->environment.coordsToIndices(q.position);
            uint32_t st=stencil27(cfg->environment,c);

            gaden::Filament pred=q;
            bool alive=deterministic_predict(
                pred,cfg->environment,cfg->windSequence,windIdx,k+1,kNext,dt,gamma,
                sim.simulationMetadata.source->gasType,sim.simulationMetadata.constants);

            out<<f<<','<<iteration<<','<<k<<','<<i<<','
               <<q.position.x<<','<<q.position.y<<','<<q.position.z<<','<<q.sigma<<','
               <<fileWindIdx<<','<<w.x<<','<<w.y<<','<<w.z<<','
               <<c.x<<','<<c.y<<','<<c.z<<','<<st<<','
               <<(alive?1:0)<<','<<pred.position.x<<','<<pred.position.y<<','<<pred.position.z<<','<<pred.sigma<<','
               <<kNext<<','<<float(kNext-k)*dt<<'\n';
            rows++;
        }
        frames++;
        if((f%100)==0) std::cerr<<"frame "<<f<<" physics_step "<<k<<" filaments "<<fil.size()<<"\n";
    }
    out.close();
    std::cerr<<"exported frames="<<frames<<" rows="<<rows<<" to "<<outPath<<"\n";
    if(frames<2) return 7;
    return 0;
}
