#include <gsl_server/algorithms/PMFS/PMFSLib.hpp>
#include <gsl_server/algorithms/PMFS/internal/Simulations.hpp>
#include <gsl_server/algorithms/PMFS/internal/VisibilityMap.hpp>
#include <rclcpp/rclcpp.hpp>
#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <iostream>
#include <cstdlib>
using namespace GSL;using namespace GSL::PMFS_internal;namespace fs=std::filesystem;
static std::vector<double> parse(std::string s){std::stringstream ss(s);std::string p;std::vector<double> v;while(std::getline(ss,p,','))v.push_back(std::stod(p));return v;}
static std::vector<std::vector<double>> csv(fs::path path){std::ifstream f(path);if(!f)throw std::runtime_error("Input absent");std::string line;std::getline(f,line);std::vector<std::vector<double>> rows;while(std::getline(f,line))if(!line.empty())rows.push_back(parse(line));return rows;}
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("usage: native_pmfs_demo SOURCE_BLIND_INPUT_DIRECTORY NEW_OUTPUT_DIRECTORY");fs::path in=argv[1],out=argv[2];if(fs::exists(out))throw std::runtime_error("No overwrite");fs::create_directory(out);rclcpp::init(argc,argv);
 setenv("NATIVE_RECOVERY_WIND_UPDATE_CSV",(out/"native_wind_at_update.csv").c_str(),1);setenv("NATIVE_RECOVERY_MEASURED_MAP_CSV",(out/"native_measured_map_at_update.csv").c_str(),1);setenv("NATIVE_RECOVERY_CANDIDATES_CSV",(out/"native_candidates.csv").c_str(),1);setenv("NATIVE_RECOVERY_UPDATE_COMPLETE_FILE",(out/"native_source_update_complete.txt").c_str(),1);
 auto dims=csv(in/"PMFS_GRID_META.csv")[0];Grid2DMetadata meta;meta.dimensions=Vector2Int(dims[0],dims[1]);meta.origin=Vector2(dims[2],dims[3]);meta.cellSize=dims[4];meta.scale=3;const size_t n=meta.dimensions.x*meta.dimensions.y;
 auto grid=csv(in/"PMFS_GRID_WIND.csv");if(grid.size()!=n)throw std::runtime_error("Grid shape");std::vector<Occupancy> occupancy(n);std::vector<HitProbability> measured(n);std::vector<double> posterior(n);std::vector<Vector2> wind(n);meta.numFreeCells=0;
 HitProbabilitySettings hit;hit.localEstimationWindowSize=2;hit.maxUpdatesPerStop=5;hit.prior=.3;hit.kernelSigma=1.5;hit.kernelStretchConstant=1.5;hit.confidenceMeasurementWeight=1;hit.confidenceSigmaSpatial=1;
 for(size_t i=0;i<n;++i){auto& r=grid[i];if(size_t(r[0])!=i)throw std::runtime_error("Original cell IDs");occupancy[i]=r[5]>.5?Occupancy::Free:Occupancy::Obstacle;if(occupancy[i]==Occupancy::Free)++meta.numFreeCells;wind[i]=Vector2(r[6],r[7]);measured[i].auxWeight=-1;measured[i].setProbability(hit.prior);}
 Grid2D<HitProbability> hg(measured,occupancy,meta);VisibilityMap visibility(meta.dimensions.x,meta.dimensions.y,5);
 for(int x=0;x<meta.dimensions.x;++x)for(int y=0;y<meta.dimensions.y;++y){Vector2Int ij(x,y);std::vector<Vector2Int> v;if(hg.freeAt(ij))for(int yy=std::max(0,y-5);yy<=std::min(meta.dimensions.y-1,y+5);++yy)for(int xx=std::max(0,x-5);xx<=std::min(meta.dimensions.x-1,x+5);++xx){Vector2Int q(xx,yy);if(q==ij||GridUtils::PathFree(meta,occupancy,meta.indicesToCoordinates(ij),meta.indicesToCoordinates(q)))v.push_back(q);}visibility.emplace(ij,std::move(v));}
 auto events=csv(in/"PMFS_MEASUREMENT_EVENTS.csv");size_t positives=0;
 for(auto& e:events){Vector2Int ij(e[1],e[2]);if(!meta.indicesInBounds(ij)||!hg.freeAt(ij))throw std::runtime_error("Observation outside native PMFS free map");bool detected=e[3]>.5;positives+=detected;PMFSLib::EstimateHitProbabilities(hg,visibility,hit,detected,e[4],e[5],ij);}
 for(size_t i=0;i<n;++i)posterior[i]=occupancy[i]==Occupancy::Free?1.0/meta.numFreeCells:0;
 SimulationSettings s;s.useWindGroundTruth=true;s.maxRegionSize=5;s.sourceDiscriminationPower=.3;s.refineFraction=.1;s.minWarmupIterations=200;s.maxWarmupIterations=500;s.iterationsToRecord=200;s.deltaTime=.1;s.noiseSTDev=.5;s.blurSigmaX=1.5;s.blurSigmaY=1.5;
 Simulations sim(hg,Grid2D<double>(posterior,occupancy,meta),Grid2D<Vector2>(wind,occupancy,meta),s);std::vector<std::vector<uint8_t>> mask(meta.dimensions.x,std::vector<uint8_t>(meta.dimensions.y));for(int x=0;x<meta.dimensions.x;++x)for(int y=0;y<meta.dimensions.y;++y)mask[x][y]=hg.freeAt(x,y)?1:0;sim.initializeMap(mask);sim.visibilityMap=&visibility;sim.varianceOfHitProb.assign(n,0.0);
 std::cout<<"ENGINEERING_DEMO_ONLY; NATIVE_PMFS; SOURCE_TRUTH_NOT_READ; events="<<events.size()<<" positive="<<positives<<std::endl;sim.updateSourceProbability(s.refineFraction);
 double sum=0;for(size_t i=0;i<n;++i){if(!std::isfinite(posterior[i])||posterior[i]<0)throw std::runtime_error("Invalid native probability");sum+=posterior[i];}if(!(sum>0))throw std::runtime_error("Empty probability map");
 std::ofstream f(out/"PMFS_SOURCE_PROBABILITY.csv");f<<std::setprecision(17)<<"cell_index,grid_i,grid_j,ENU_x,ENU_y,free,native_probability,normalized_probability,hit_probability,confidence\n";for(size_t i=0;i<n;++i){auto& r=grid[i];f<<i<<','<<r[1]<<','<<r[2]<<','<<r[3]<<','<<r[4]<<','<<r[5]<<','<<posterior[i]<<','<<posterior[i]/sum<<','<<measured[i].probability()<<','<<measured[i].confidence<<'\n';}
 std::ofstream audit(out/"NATIVE_PMFS_COMPLETED.json");audit<<"{\"classification\":\"ENGINEERING_DEMO_ONLY\",\"native_PMFS_updateSourceProbability\":true,\"source_truth_read\":false,\"events\":"<<events.size()<<",\"positive_events\":"<<positives<<",\"probability_sum\":"<<std::setprecision(17)<<sum<<",\"fixed_external_UAV_path\":true,\"PMFS_navigation_planner_run\":false,\"scientific_qualification\":false}\n";rclcpp::shutdown();std::cout<<"NATIVE_PMFS_ENGINEERING_COMPLETE\n";return 0;
}catch(const std::exception&e){std::cerr<<"FAILED "<<e.what()<<'\n';return 1;}}
