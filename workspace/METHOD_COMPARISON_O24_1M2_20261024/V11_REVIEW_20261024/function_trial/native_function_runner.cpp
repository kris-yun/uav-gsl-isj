#include <bits/stdc++.h>
#include <nlohmann/json.hpp>
#include <DDA/DDA.h>
#include <xxHash/xxhash32.h>
#include <gsl_server/algorithms/PMFS/internal/Simulations.hpp>
#include <gsl_server/algorithms/Common/Utils/Math.hpp>
#include <gsl_server/algorithms/Common/Utils/Profiling.hpp>
using json=nlohmann::json;
namespace Audit {
uint32_t seed,state;uint64_t uc,uh,gc,gh;int ix;std::array<float,2500> table;
uint64_t hstep(uint64_t h,uint64_t x){return(h^x)*1099511628211ULL;}
void loadTable(const std::string&p){std::ifstream f(p,std::ios::binary);f.read(reinterpret_cast<char*>(table.data()),10000);if(f.gcount()!=10000)throw std::runtime_error("cache read failed");}
void restore(const json&b){seed=b.at("seed");state=b.at("state");uc=b.at("uc");uh=b.at("uh");gc=b.at("gc");gh=b.at("gh");ix=b.at("index");}
json end(){return {{"seed",seed},{"state",state},{"uc",uc},{"uh",uh},{"gc",gc},{"gh",gh},{"index",ix}};}
struct RestoredCache {float nextValue(float mean,float stdev){ix=(ix+1)%2500;uint32_t b;std::memcpy(&b,&table[ix],4);gc++;gh=hstep(gh,b);return mean+stdev*table[ix];}};
}
namespace GSL::Utils {
double uniformRandom(double min,double max){Audit::state=XXHash32::hash(&Audit::state,sizeof(Audit::state),Audit::seed);++Audit::uc;Audit::uh=Audit::hstep(Audit::uh,Audit::state);constexpr double reciprocalMax=1/(double)std::numeric_limits<uint32_t>::max();double rndVal01=Audit::state*reciprocalMax;return min+rndVal01*(max-min);}
double lerp(double a,double b,double p){if(p<0||std::isnan(p))return a;return a+(b-a)*std::min(1.,p);}
double logOddsToProbability(double x){return 1.-1./(1+std::exp(x));}
}
namespace GSL {struct PMFSLib {static bool pathFree(Grid2DMetadata,const std::vector<Occupancy>&,const Vector2&,const Vector2&);};
bool PMFSLib::pathFree(Grid2DMetadata metadata, const std::vector<Occupancy>& occupancy, const Vector2& origin, const Vector2& end)
    {
        Vector2Int originInd = metadata.coordinatesToIndex(origin);
        Vector2Int endInd = metadata.coordinatesToIndex(end);

        DDA::_2D::Map<GSL::Occupancy> map(occupancy, metadata.origin, metadata.cellSize, {metadata.dimensions.x, metadata.dimensions.y});

        // check there are no obstacles between origin and end
        if (!(occupancy[metadata.indexOf(originInd)] == Occupancy::Free && occupancy[metadata.indexOf(endInd)] == Occupancy::Free))
            return false;
        Vector2 direction = end - origin;
        DDA::_2D::RayCastInfo raycastInfo = DDA::_2D::castRay<GSL::Occupancy>(
                origin, direction, vmath::length(direction),
                DDA::_2D::Map<GSL::Occupancy>(occupancy, metadata.origin, metadata.cellSize, {metadata.dimensions.x, metadata.dimensions.y}),
                [](const GSL::Occupancy & occ)
        {
            return occ == GSL::Occupancy::Free;
        });

        return !raycastInfo.hitSomething;
    }
}
namespace GSL::PMFS_internal {
static Audit::RestoredCache gaussian;
double Simulations::sourceProbFromMaps(const Grid2D<HitProbability>& measuredHitProb, const std::vector<float>& hitMap) const
    {
        ZoneScoped;
        double total = 1;
        for (int i = 0; i < measuredHitProb.data.size(); i++)
        {
            if (measuredHitProb.occupancy[i] != Occupancy::Free)
                continue;
            double measured = Utils::logOddsToProbability(measuredHitProb.data[i].logOdds);
            const double& simulated = hitMap[i];
            double val =
                Utils::lerp(1, (1 - std::abs(measured - simulated) * settings.sourceDiscriminationPower), measuredHitProb.data[i].confidence);
            total *= val;
            GSL_ASSERT(!std::isnan(total));
        }
        return total;
    }

void Simulations::moveFilament(Filament& filament, Vector2Int& indices, float deltaTime, float noiseSTDev) const
    {
        Vector2 velocity = wind.dataAt(indices.x, indices.y) + Vector2(gaussian.nextValue(0, noiseSTDev), gaussian.nextValue(0, noiseSTDev));

        Vector2 newPos = filament.position + deltaTime * velocity;
        moveAlongPath(filament.position, newPos);
    }

bool Simulations::filamentIsOutside(const Filament& filament) const
    {
        Vector2Int newIndices = measuredHitProb.metadata.coordinatesToIndex(filament.position.x, filament.position.y);
        return !measuredHitProb.metadata.indicesInBounds(newIndices);
    }

void Simulations::simulateSourceInPosition(const SimulationSource& source, std::vector<float>& hitMap, bool warmup, int warmupLimit,
            int timesteps, float deltaTime, float noiseSTDev) const
    {
        constexpr int numFilamentsIteration = 5;
        std::vector<Filament> filaments(warmupLimit * numFilamentsIteration + timesteps * numFilamentsIteration);

        std::vector<uint16_t> updated(hitMap.size(), 0); // index of the last iteration in which this cell was updated, to avoid double-counting

        int lastActivated = 0;

        // warm-up: we don't want to start recording frequency of hits until the shape of the plume has stabilized. Wait until a filament exits the
        // environment through an outlet, or a maximum number of steps
        {
            ZoneScopedN("Warmup");

            bool stable = false;
            int count = 0;
            while (!stable && count < warmupLimit)
            {
                for (int i = 0; i < numFilamentsIteration; i++)
                {
                    filaments[lastActivated].position = source.getPoint();
                    filaments[lastActivated].active = true;
                    lastActivated = (lastActivated + 1) % filaments.size();
                }

                for (Filament& filament : filaments)
                {
                    if (!filament.active)
                        continue;
                    auto indices = measuredHitProb.metadata.coordinatesToIndex(filament.position.x, filament.position.y);

                    // move active filaments
                    moveFilament(filament, indices, deltaTime * 2, noiseSTDev);

                    // remove filaments
                    if (filamentIsOutside(filament))
                    {
                        filament.active = false;
                        stable = true;
                        break;
                    }
                }
                count++;
            }
        }

        ZoneScopedN("Recording");
        // now, we do the thing
        for (int t = 1; t < timesteps + 1; t++)
        {
            // spawn new ones
            for (int i = 0; i < numFilamentsIteration; i++)
            {
                filaments[lastActivated].position = source.getPoint();
                filaments[lastActivated].active = true;
                lastActivated = (lastActivated + 1) % filaments.size();
            }

            for (Filament& filament : filaments)
            {
                if (!filament.active)
                    continue;

                // update map
                auto indices = measuredHitProb.metadata.coordinatesToIndex(filament.position.x, filament.position.y);
                size_t index = measuredHitProb.metadata.indexOf(indices);
                // mark as updated so it doesn't count multiple filaments in the same timestep
                if (updated[index] < t)
                {
                    hitMap[index]++;
                    updated[index] = t;
                }

                // move active filaments
                moveFilament(filament, indices, deltaTime, noiseSTDev);

                // remove filaments
                if (filamentIsOutside(filament))
                {
                    filament.active = false;
                }
            }
        }

        // convert the total hit count into relative frequency
        for (int i = 0; i < measuredHitProb.data.size(); i++)
        {
            if (measuredHitProb.occupancy[i] == Occupancy::Free)
                hitMap[i] = hitMap[i] / timesteps;
        }
    }

Vector2 SimulationSource::getPoint() const
    {
        if (mode == Mode::Point)
            return point;

        Vector2 start = metadata.indexToCoordinates(nqaNode->origin.x, nqaNode->origin.y, false);
        Vector2 end = metadata.indexToCoordinates(nqaNode->origin.x + nqaNode->size.x, nqaNode->origin.y + nqaNode->size.y, false);

        Vector2 randP(Utils::uniformRandom(start.x, end.x), Utils::uniformRandom(start.y, end.y));

        return randP;
    }

bool Simulations::moveAlongPath(Vector2& currentPosition, const Vector2& end) const
    {
        Vector2Int indexEnd = measuredHitProb.metadata.coordinatesToIndex(end.x, end.y);
        Vector2Int indexOrigin = measuredHitProb.metadata.coordinatesToIndex(currentPosition.x, currentPosition.y);

        if (!measuredHitProb.freeAt(indexOrigin.x, indexOrigin.y))
        {
            return false;
        }

        // try to avoid doing the raycast by looking at the pre-computed visibilityMap
        if (indexOrigin == indexEnd || (measuredHitProb.metadata.indicesInBounds(indexEnd) && measuredHitProb.freeAt(indexEnd.x, indexEnd.y) &&
                                        visibilityMap->isVisible(indexOrigin, indexEnd) == Visibility::Visible))
        {
            currentPosition = end;
            return true;
        }

#define USE_DDA 0
#if USE_DDA
        Vector2 movement = end - currentPosition;
        DDA::_2D::RayCastInfo raycastInfo = DDA::_2D::castRay<GSL::Occupancy>(
        {currentPosition.y, currentPosition.x}, {movement.y, movement.x}, vmath::length(movement),
        DDA::_2D::Map<GSL::Occupancy>(measuredHitProb.occupancy, measuredHitProb.metadata.origin, measuredHitProb.metadata.cellSize,
        {measuredHitProb.metadata.dimensions.y, measuredHitProb.metadata.dimensions.x}),
        [](const GSL::Occupancy & occ)
        {
            return occ == GSL::Occupancy::Free;
        });
        // This is a completely hacky arbitrary value to try and stop filaments from getting stuck right next to a wall
        // ideally, we should implement a "deflection" instead so they move along the wall a bit rather than stopping dead
        constexpr float wallStoppingProportion = 0.7;
        currentPosition += movement * raycastInfo.distance * wallStoppingProportion;

        return true;
#else
        const auto& metadata = measuredHitProb.metadata;
        bool pathIsFree = true;
        float stepSize = metadata.cellSize * 0.2f;

        Vector2 vector = end - currentPosition;
        Vector2 increment = vmath::normalized(vector) * stepSize;
        int steps = vmath::length(vector) / stepSize;

        int index = 0;
        while (index < steps && pathIsFree)
        {
            currentPosition += increment;
            index++;
            Vector2Int pair = metadata.coordinatesToIndex(currentPosition.x, currentPosition.y);
            pathIsFree = !metadata.indicesInBounds(pair) || measuredHitProb.freeAt(pair.x, pair.y);
            if (!pathIsFree)
                currentPosition -= increment;
        }
        return pathIsFree;
#endif
    }
}
struct Probe: GSL::PMFS_internal::Simulations {using Simulations::Simulations;using Simulations::simulateSourceInPosition;using Simulations::sourceProbFromMaps;};
json readj(const std::string&p){std::ifstream f(p);json j;f>>j;return j;}
int main(int argc,char**argv){
 try {
  if(argc!=6)throw std::runtime_error("runner scene mode spec outprefix cache");
  auto j=readj(argv[1]);std::string mode=argv[2];auto spec=readj(argv[3]);std::string out=argv[4];Audit::loadTable(argv[5]);
  using namespace GSL;using namespace GSL::PMFS_internal;
  Grid2DMetadata md;md.dimensions={j["nx"],j["ny"]};md.origin={j["origin"][0],j["origin"][1]};md.cellSize=j["cell_size"];md.scale=25;
  size_t n=md.dimensions.x*md.dimensions.y;std::vector<Occupancy>occ(n);std::vector<HitProbability>hit(n);std::vector<double>prior(n);std::vector<Vector2>wind(n);
  for(size_t i=0;i<n;i++){occ[i]=j["occupancy"][i]==0?Occupancy::Free:Occupancy::Obstacle;hit[i].logOdds=j["logodds"][i];hit[i].confidence=j["confidence"][i];wind[i]={j["wind_xy"][i][0],j["wind_xy"][i][1]};}
  Grid2D<HitProbability>hg(hit,occ,md);Grid2D<double>pg(prior,occ,md);Grid2D<Vector2>wg(wind,occ,md);
  SimulationSettings s{};s.sourceDiscriminationPower=j["params"]["sourceDiscriminationPower"];s.maxWarmupIterations=j["params"]["maxWarmupIterations"];s.iterationsToRecord=j["params"]["iterationsToRecord"];s.deltaTime=j["params"]["deltaTime"];s.noiseSTDev=j["params"]["noiseSTDev"];
  Probe probe(hg,pg,wg,s);VisibilityMap visibility(md.dimensions.y,md.dimensions.x,5);
  for(int x=0;x<md.dimensions.x;x++)for(int y=0;y<md.dimensions.y;y++){
   std::vector<Vector2Int>v;if(hg.freeAt(x,y)){
    int oi=std::max(0,x-5)-x,fi=std::min(md.dimensions.x-1,x+5)-x,oj=std::max(0,y-5)-y,fj=std::min(md.dimensions.y-1,y+5)-y;
    for(int dx=oi;dx<=fi;dx++)for(int dy=oj;dy<=fj;dy++){Vector2Int to(x+dx,y+dy);if(to==Vector2Int(x,y)||PMFSLib::pathFree(md,occ,md.indexToCoordinates(x,y),md.indexToCoordinates(to)))v.push_back(to);}
   }visibility.emplace({x,y},v);
  }probe.visibilityMap=&visibility;
  std::vector<std::vector<uint8_t>> qmap(md.dimensions.x,std::vector<uint8_t>(md.dimensions.y));for(int x=0;x<md.dimensions.x;x++)for(int y=0;y<md.dimensions.y;y++)qmap[x][y]=hg.freeAt(x,y)?1:0;
  int ox=6,oy=14,sx=5,sy=4;if(mode=="replay"){auto c=spec["candidate"];ox=std::stoi(c["origin_x"].get<std::string>());oy=std::stoi(c["origin_y"].get<std::string>());sx=std::stoi(c["size_x"].get<std::string>());sy=std::stoi(c["size_y"].get<std::string>());Audit::restore(spec["rng"]["before"]);}
  else {Audit::seed=spec["seed"];Audit::state=65535;Audit::uc=Audit::gc=0;Audit::uh=Audit::gh=1469598103934665603ULL;Audit::ix=Utils::uniformRandom(0,2500);}
  Utils::NQA::Node region(nullptr,{ox,oy},{sx,sy},qmap);Vector2 pt(0,0);if(mode!="replay"&&spec["arm"]!="A")pt={spec["point"][0],spec["point"][1]};
  SimulationSource src=(mode=="replay"||spec["arm"]=="A")?SimulationSource(&region,md):SimulationSource(pt,md);
  auto before=Audit::end();std::vector<float>freq(n,0.0f);auto t0=std::chrono::steady_clock::now();
  probe.simulateSourceInPosition(src,freq,true,s.maxWarmupIterations,s.iterationsToRecord,s.deltaTime,s.noiseSTDev);
  auto after=Audit::end();double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();
  json stops=json::array();for(auto q:j["stops"]){int k=q["cell"][0].get<int>()+q["cell"][1].get<int>()*md.dimensions.x;q["prediction"]=freq[k];stops.push_back(q);}
  double score=probe.sourceProbFromMaps(hg,freq);std::ofstream f(out+".f32",std::ios::binary);f.write(reinterpret_cast<const char*>(freq.data()),freq.size()*4);f.close();
  json result={{"mode",mode},{"spec",spec},{"score",score},{"before",before},{"after",after},{"simulation_wall_s",seconds},{"filament_moves",(after["gc"].get<uint64_t>()-before["gc"].get<uint64_t>())/2},{"stops",stops}};std::ofstream o(out+".json");o<<std::setw(2)<<result<<"\n";
  std::cout<<json({{"status","DONE_FUNCTION_CALL"},{"mode",mode},{"score",score},{"seconds",seconds}})<<"\n";
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 2;}
}
