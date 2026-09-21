// Reuse frozen readers and exact public forward kernel. The historical main
// is compiled under an unused name; no truth argument is accepted by this tool.
#define main unused_meaci_truth_main
#include "../../ros2_package/tools/meaci_replay_true.cpp"
#undef main

int main(int argc, char** argv) {
    if (argc != 7) {
        std::cerr << "native_bank context_bank update sources.csv worlds.csv output_dir case_seed\n";
        return 2;
    }
    try {
        fs::path bank=argv[1], out=argv[5];
        const uint64_t update=std::stoull(argv[2]), seed=std::stoull(argv[6]);
        std::ostringstream un; un << "source_update_" << std::setw(4) << std::setfill('0') << update;
        fs::path d=bank/un.str();
        auto t=readTiming(bank/"source_update_timing.csv",readRunUUID(d/"candidate_manifest.csv"),update);
        auto cells=readMeasured(d/"measured_hit_probability.csv");
        Grid2DMetadata meta;
        meta.dimensions={t.width,t.height}; meta.cellSize=t.cellSize;
        meta.origin={static_cast<float>(t.originX),static_cast<float>(t.originY)};
        meta.scale=1; meta.numFreeCells=0;
        size_t n=t.width*t.height;
        std::vector<HitProbability> measured(n);
        std::vector<Occupancy> occ(n,Occupancy::Obstacle);
        std::vector<Vector2> basewind(n,Vector2(0,0));
        for (auto& c:cells) {
            measured[c.index].logOdds=c.logOdds; measured[c.index].confidence=c.confidence;
            measured[c.index].omega=c.omega; measured[c.index].distanceFromRobot=c.distance;
            measured[c.index].originalPropagationDirection={static_cast<float>(c.dirX),static_cast<float>(c.dirY)};
            occ[c.index]=c.occupancy;
        }
        readWind(d/"estimated_wind.csv",basewind);
        std::vector<Candidate> sources;
        std::string line;
        std::ifstream si(argv[3]); std::getline(si,line);
        while(std::getline(si,line)) { auto f=split(line); Candidate c;
            c.id=f.at(0);c.x=asDouble(f.at(1));c.y=asDouble(f.at(2)); sources.push_back(c); }
        std::ifstream wi(argv[4]); std::getline(wi,line);
        if(sources.empty()) throw std::runtime_error("empty source set");
        if(fs::exists(out/"responses.f32")) throw std::runtime_error("refuse overwrite bank");
        fs::create_directories(out);
        std::ofstream binary(out/"responses.f32",std::ios::binary);
        std::ofstream times(out/"timing.csv"); times << "world,source,seconds\n";
        std::ofstream vis(out/"visibility_weight.csv"); vis << "cell_index,weight\n";
        size_t worldCount=0;
        while(std::getline(wi,line)) {
            auto f=split(line); auto world=f.at(0);
            double a=asDouble(f.at(1))*M_PI/180.,speed=asDouble(f.at(2)),noise=asDouble(f.at(3));
            int replica=std::stoi(f.at(4));
            auto wind=basewind;
            for(auto& v:wind) { double x=v.x,y=v.y; v={static_cast<float>(speed*(cos(a)*x-sin(a)*y)),static_cast<float>(speed*(sin(a)*x+cos(a)*y))}; }
            SimulationSettings settings;
            settings.maxRegionSize=5; settings.maxWarmupIterations=3;settings.minWarmupIterations=1;
            settings.iterationsToRecord=200;settings.deltaTime=.2;settings.noiseSTDev=.5*noise;
            settings.blurSigmaX=0;settings.blurSigmaY=0;
            std::vector<double> sp(n,0.);
            Grid2D<HitProbability> mg(measured,occ,meta);
            Simulations sim(mg,Grid2D<double>(sp,occ,meta),Grid2D<Vector2>(wind,occ,meta),settings);
            VisibilityMap visibility(t.width,t.height,5);
            GSL::PMFSLib::InitializeMap(mg,sim,visibility,Vector2(t.robotX,t.robotY));
            if(worldCount==0) for(size_t j=0;j<n;++j) if(occ[j]==Occupancy::Free) {
                auto ij=meta.indices2D(j); double w=0;
                for(auto p:visibility.at(ij)) w+=std::exp(-std::hypot(double(ij.x-p.x),double(ij.y-p.y)));
                vis << j << ',' << std::setprecision(17) << w << '\n';
            }
            for(auto& s:sources) {
                auto ij=meta.coordinatesToIndices(s.x,s.y);
                if(!meta.indicesInBounds(ij) || occ[meta.indexOf(ij)]!=Occupancy::Free)
                    throw std::runtime_error("source point outside free map: "+s.id);
                EventKey key{seed,update,static_cast<uint64_t>(replica),5570802872545061271ULL};
                EventKeyedTransportRng rng(key); // same world key for ALL sources/cells
                std::vector<float> hit(n,0.);
                auto start=std::chrono::steady_clock::now();
                sim.runPointForwardReplay(Vector2(s.x,s.y),hit,200,.2f,.5f*noise,&rng);
                for(size_t j=0;j<hit.size();++j) {
                    // The frozen kernel normalizes only free cells. Obstacle
                    // entries are unused filament counters, not probabilities.
                    if(occ[j]!=Occupancy::Free) {
                        if(hit[j]>1) std::cerr << "OBSTACLE_RAW_COUNTER " << world << ' ' << s.id << ' ' << j << ' ' << hit[j] << '\n';
                        hit[j]=0;
                    } else if(!std::isfinite(hit[j])||hit[j]<0||hit[j]>1) {
                        throw std::runtime_error("invalid FREE-cell response: "+world+" "+s.id+" cell="+std::to_string(j)+" p="+std::to_string(hit[j]));
                    }
                }
                binary.write(reinterpret_cast<char*>(hit.data()),hit.size()*sizeof(float));
                times << world << ',' << s.id << ',' << std::setprecision(17)
                      << std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count() << '\n';
            }
            binary.flush(); times.flush(); ++worldCount;
            std::cout << "WORLD_COMPLETE " << world << " " << sources.size() << std::endl;
        }
        if(worldCount!=35) throw std::runtime_error("expected exactly 27 train plus 8 grid-off worlds");
        std::ofstream done(out/"COMPLETE.json");
        done << "{\"worlds\":" << worldCount << ",\"sources\":" << sources.size() << ",\"cells\":" << n << "}\n";
    } catch(const std::exception& e) {std::cerr << e.what() << '\n';return 1;}
    return 0;
}
