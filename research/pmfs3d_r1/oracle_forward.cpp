// Offline transport-only replay. Never changes a live PMFS/ROS process.
// Native and Oracle-2D call the frozen PMFS library, not a reimplementation.
#include <gsl_server/algorithms/PMFS/internal/Simulations.hpp>
#include <gsl_server/algorithms/PMFS/internal/EventKeyedRng.hpp>
#include <gsl_server/algorithms/PMFS/PMFSLib.hpp>
#include <nanoflann.hpp>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <array>
#include <stdexcept>

using namespace GSL;
using namespace GSL::PMFS_internal;
namespace fs = std::filesystem;
using Row = std::map<std::string, std::string>;
static std::vector<std::string> split(const std::string& s) {
    std::vector<std::string> v; std::string t; bool quoted=false;
    for(size_t i=0;i<s.size();i++) {
        char ch=s[i];
        if(ch=='"') {if(quoted&&i+1<s.size()&&s[i+1]=='"'){t+='"';i++;}else quoted=!quoted;}
        else if(ch==','&&!quoted){v.push_back(t);t.clear();}
        else t+=ch;
    }
    if(quoted) throw std::runtime_error("unterminated CSV quote");
    v.push_back(t);return v;
}
static std::vector<Row> csv(const fs::path& p) {
    std::ifstream in(p); if (!in) throw std::runtime_error("missing CSV " + p.string());
    std::string s; std::getline(in,s); if (!s.empty() && s.back()=='\r') s.pop_back();
    auto h=split(s); std::vector<Row> rows;
    while (std::getline(in,s)) {
        if (!s.empty() && s.back()=='\r') s.pop_back(); if(s.empty()) continue;
        auto v=split(s); if(v.size()!=h.size()) throw std::runtime_error("CSV shape");
        Row r; for(size_t j=0;j<h.size();j++) r[h[j]]=v[j]; rows.push_back(r);
    } return rows;
}
static double num(const Row& r,const char* k) {return std::stod(r.at(k));}
static int integer(const Row& r,const char* k) {return std::stoi(r.at(k));}

struct CFD {
    struct Point {std::array<double,3> x,u;}; std::vector<Point> points;
    size_t kdtree_get_point_count() const {return points.size();}
    double kdtree_get_pt(size_t i,size_t k) const {return points[i].x[k];}
    template<class B> bool kdtree_get_bbox(B&) const {return false;}
    using Tree=nanoflann::KDTreeSingleIndexAdaptor<nanoflann::L2_Simple_Adaptor<double,CFD>,CFD,3,size_t>;
    std::unique_ptr<Tree> tree;
    explicit CFD(const fs::path& path) {
        std::ifstream in(path); if(!in) throw std::runtime_error("CFD CSV missing");
        std::string line; std::getline(in,line);
        while(std::getline(in,line)) {
            auto v=split(line); if(v.size()!=6) throw std::runtime_error("CFD columns");
            Point p; for(int k=0;k<3;k++){p.u[k]=std::stod(v[k]);p.x[k]=std::stod(v[k+3]);}
            points.push_back(p);
        }
        if(points.empty()) throw std::runtime_error("CFD empty");
        tree=std::make_unique<Tree>(3,*this,nanoflann::KDTreeSingleIndexAdaptorParams(10));
        tree->buildIndex();
    }
    std::array<double,3> at(double x,double y,double z) const {
        double q[3]={x,y,z},distance; size_t i;
        if(tree->knnSearch(q,1,&i,&distance)!=1) throw std::runtime_error("CFD query failed");
        return points[i].u;
    }
};
struct Volume {
    std::array<double,3> origin; std::array<int,3> dims; double cell;
    std::vector<int> state;
    explicit Volume(const fs::path& p) {
        std::ifstream in(p); if(!in) throw std::runtime_error("3D occupancy missing");
        std::string s,tag; std::getline(in,s); std::stringstream a(s); a>>tag>>origin[0]>>origin[1]>>origin[2];
        std::getline(in,s); std::getline(in,s); std::stringstream b(s); b>>tag>>dims[0]>>dims[1]>>dims[2];
        std::getline(in,s); std::stringstream c(s); c>>tag>>cell;
        if(cell<=0||dims[0]<=0||dims[1]<=0||dims[2]<=0) throw std::runtime_error("3D header");
        state.assign(size_t(dims[0])*dims[1]*dims[2],-1);
        int x=0,z=0;
        // GADEN text format: constant-x rows, y columns, semicolon between z layers.
        while(std::getline(in,s)) {
            if(!s.empty()&&s.back()=='\r') s.pop_back();
            if(s==";") {if(x!=dims[0]) throw std::runtime_error("3D plane rows");x=0;z++;continue;}
            if(s.empty()) continue;
            if(x>=dims[0]||z>=dims[2]) throw std::runtime_error("3D overflow");
            std::stringstream row(s); int value,y=0;
            while(row>>value) {if(y>=dims[1]) throw std::runtime_error("3D row overflow");state[x+y*dims[0]+z*dims[0]*dims[1]]=value;y++;}
            if(y!=dims[1]) throw std::runtime_error("3D row length");x++;
        }
        for(auto value:state) if(value<0||value>2) throw std::runtime_error("3D unfilled/unknown cell");
    }
    std::array<int,3> indices(const std::array<float,3>& p) const {
        return {int(std::floor((p[0]-origin[0])/cell)),int(std::floor((p[1]-origin[1])/cell)),int(std::floor((p[2]-origin[2])/cell))};
    }
    bool inside(const std::array<float,3>& p) const {
        auto j=indices(p);for(int k=0;k<3;k++) if(j[k]<0||j[k]>=dims[k]) return false;return true;
    }
    bool free(const std::array<float,3>& p) const {
        if(!inside(p)) return false;auto j=indices(p);return state[j[0]+j[1]*dims[0]+j[2]*dims[0]*dims[1]]==0;
    }
    int layer(double z) const {return int(std::floor((z-origin[2])/cell));}
};
class Replay: public Simulations {
public:
    using Simulations::Simulations;
    std::vector<float> twoD(const Utils::NQA::Node& leaf,EventKey key) const {
        EventKeyedTransportRng rng(key); SimulationSource source(&leaf,measuredHitProb.metadata,&rng);
        std::vector<float> hit(measuredHitProb.data.size(),0);
        simulateSourceInPosition(source,hit,true,settings.iterationsToRecord,settings.deltaTime,settings.noiseSTDev,nullptr,&rng);
        return hit;
    }
    std::vector<float> threeD(const Utils::NQA::Node& leaf,EventKey key,const CFD& cfd,const Volume& volume,double releaseZ,double sensorZ) const {
        EventKeyedTransportRng rng(key);
        EventKey verticalKey=key; verticalKey.transportSubstream ^= 0x33565F4E4F495345ULL;
        EventKeyedTransportRng verticalRng(verticalKey);
        SimulationSource source(&leaf,measuredHitProb.metadata,&rng);
        using Pos=std::array<float,3>;std::vector<Pos> active,next;
        std::vector<float> hit(measuredHitProb.data.size(),0);
        std::vector<int> updated(hit.size(),0);
        uint64_t draw=0,zdraw=0; const auto& meta=measuredHitProb.metadata;
        auto release=[&]() {for(int j=0;j<5;j++){auto xy=source.getPoint();Pos p{xy.x,xy.y,float(releaseZ)};if(volume.free(p)) active.push_back(p);}};
        auto advance=[&](Pos& p,float dt) {
            auto ij=meta.coordinatesToIndices(p[0],p[1]);
            auto center=meta.indicesToCoordinates(ij); // identical horizontal wind-grid resolution in both oracle arms
            auto velocity=cfd.at(center.x,center.y,p[2]);
            Pos end;
            end[0]=p[0]+dt*float(velocity[0]+rng.normalAt(draw++,0,settings.noiseSTDev));
            end[1]=p[1]+dt*float(velocity[1]+rng.normalAt(draw++,0,settings.noiseSTDev));
            end[2]=p[2]+dt*float(velocity[2]+verticalRng.normalAt(zdraw++,0,settings.noiseSTDev));
            double length=0;for(int k=0;k<3;k++) length+=std::pow(double(end[k])-p[k],2);length=std::sqrt(length);
            int steps=std::max(1,int(std::ceil(length/(volume.cell*0.5))));
            auto start=p;
            for(int j=1;j<=steps;j++) {
                Pos q;for(int k=0;k<3;k++) q[k]=start[k]+(end[k]-start[k])*float(j)/steps;
                if(!volume.inside(q)){p=q;return;}
                if(!volume.free(q)) return; // stay at last valid 3D point, no tunnelling
                p=q;
            }
        };
        bool stable=false;int warm=0;
        while(warm<settings.minWarmupIterations||(!stable&&warm<settings.maxWarmupIterations)) {
            release();next.clear();
            for(auto p:active){advance(p,settings.deltaTime*2);auto ij=meta.coordinatesToIndices(p[0],p[1]);if(!volume.inside(p)||!meta.indicesInBounds(ij)) stable=true;else next.push_back(p);}
            active.swap(next);warm++;
        }
        const int sensorLayer=volume.layer(sensorZ);
        for(int t=1;t<=settings.iterationsToRecord;t++) {
            release();next.clear();
            for(auto p:active) {
                auto ij=meta.coordinatesToIndices(p[0],p[1]);
                if(meta.indicesInBounds(ij)&&volume.indices(p)[2]==sensorLayer) {
                    auto index=meta.indexOf(ij);
                    if(measuredHitProb.occupancy[index]==Occupancy::Free&&updated[index]<t){hit[index]++;updated[index]=t;}
                }
                advance(p,settings.deltaTime);ij=meta.coordinatesToIndices(p[0],p[1]);
                if(volume.inside(p)&&meta.indicesInBounds(ij)) next.push_back(p);
            }active.swap(next);
        }
        for(size_t i=0;i<hit.size();i++) if(measuredHitProb.occupancy[i]==Occupancy::Free) hit[i]/=settings.iterationsToRecord;
        return hit;
    }
};
int main(int argc,char** argv) {
    try {
        if(argc!=5) throw std::runtime_error("usage: oracle_forward INPUT_DIR CONFIG_CSV native|oracle2d|oracle3d OUTPUT_DIR");
        fs::path input(argv[1]),out(argv[4]);std::string arm(argv[3]);
        if(arm!="native"&&arm!="oracle2d"&&arm!="oracle3d") throw std::runtime_error("unknown arm");
        if(fs::exists(out)) throw std::runtime_error("output exists; refusing overwrite");
        auto configs=csv(argv[2]);if(configs.size()!=1) throw std::runtime_error("single config required");const Row& cfg=configs[0];
        auto cells=csv(input/"measured_hit_probability.csv"),leaves=csv(input/"active_candidates.csv");
        Grid2DMetadata meta;meta.dimensions={integer(cfg,"width"),integer(cfg,"height")};meta.cellSize=float(num(cfg,"cell"));meta.origin={float(num(cfg,"origin_x")),float(num(cfg,"origin_y"))};meta.scale=3;meta.numFreeCells=0;
        size_t n=size_t(meta.dimensions.x)*meta.dimensions.y;
        if(cells.size()!=n) throw std::runtime_error("cell count");
        std::vector<Occupancy> occ(n);std::vector<HitProbability> hp(n);std::vector<Vector2> wind(n,Vector2(0,0));std::vector<double> posterior(n,0);
        for(auto& row:cells){int i=integer(row,"cell_index");if(i<0||size_t(i)>=n)throw std::runtime_error("cell index");occ[i]=row.at("occupancy")=="Free"?Occupancy::Free:Occupancy::Obstacle;hp[i].logOdds=num(row,"logOdds");hp[i].confidence=num(row,"confidence");if(occ[i]==Occupancy::Free)meta.numFreeCells++;}
        std::unique_ptr<CFD> cfd;std::unique_ptr<Volume> volume;
        if(arm=="native") {for(auto& row:csv(input/"estimated_wind.csv")){int i=integer(row,"cell_index");wind.at(i)={float(num(row,"wind_x")),float(num(row,"wind_y"))};}}
        else {
            cfd=std::make_unique<CFD>(cfg.at("cfd_csv"));
            for(size_t i=0;i<n;i++) if(occ[i]==Occupancy::Free){auto xy=meta.indexToCoordinates(i);auto uv=cfd->at(xy.x,xy.y,num(cfg,"sensor_z"));wind[i]={float(uv[0]),float(uv[1])};}
            if(arm=="oracle3d") volume=std::make_unique<Volume>(cfg.at("occupancy3d"));
        }
        SimulationSettings settings;settings.minWarmupIterations=integer(cfg,"min_warmup");settings.maxWarmupIterations=integer(cfg,"max_warmup");settings.iterationsToRecord=integer(cfg,"record_steps");settings.deltaTime=float(num(cfg,"dt"));settings.noiseSTDev=float(num(cfg,"noise"));settings.blurSigmaX=0;settings.blurSigmaY=0;settings.sourceDiscriminationPower=float(num(cfg,"power"));
        Replay replay(Grid2D<HitProbability>(hp,occ,meta),Grid2D<double>(posterior,occ,meta),Grid2D<Vector2>(wind,occ,meta),settings);
        VisibilityMap visibility(meta.dimensions.x,meta.dimensions.y,5);
        std::vector<std::vector<uint8_t>> occupancyMap(meta.dimensions.x,std::vector<uint8_t>(meta.dimensions.y));
        for(int x=0;x<meta.dimensions.x;x++)for(int y=0;y<meta.dimensions.y;y++) {
            Vector2Int ij(x,y);occupancyMap[x][y]=occ[meta.indexOf(ij)]==Occupancy::Free;
            std::vector<Vector2Int> visible;
            if(occupancyMap[x][y])for(int row=std::max(0,y-5);row<=std::min(meta.dimensions.y-1,y+5);row++)for(int col=std::max(0,x-5);col<=std::min(meta.dimensions.x-1,x+5);col++) {
                Vector2Int j(col,row);if(j==ij||GridUtils::PathFree(meta,occ,meta.indicesToCoordinates(ij),meta.indicesToCoordinates(j)))visible.push_back(j);
            }visibility.emplace(ij,visible);
        }
        replay.initializeMap(occupancyMap);replay.visibilityMap=&visibility;
        EventKey key{std::stoull(cfg.at("native_rng_seed")),std::stoull(cfg.at("update_id")),0,0x4E4154495645504DULL};
        fs::create_directories(out/"maps");std::ofstream scores(out/"candidate_log_scores.csv");scores<<"candidate_id,log_score\n"<<std::setprecision(21);
        for(const auto& row:leaves) {
            Utils::NQA::Node leaf(nullptr,{integer(row,"origin_i"),integer(row,"origin_j")},{integer(row,"size_i"),integer(row,"size_j")},occupancyMap);
            auto hit=arm=="oracle3d"?replay.threeD(leaf,key,*cfd,*volume,num(cfg,"source_z"),num(cfg,"sensor_z")):replay.twoD(leaf,key);
            long double logScore=0;
            for(size_t i=0;i<n;i++)if(occ[i]==Occupancy::Free) {
                double factor=replay.probabilityFromSingleCell(hp[i],hit[i]);
                if(factor<0||!std::isfinite(factor))throw std::runtime_error("invalid Native factor");
                logScore+=factor==0?-INFINITY:std::log((long double)factor);
            }
            scores<<row.at("candidate_id")<<','<<logScore<<'\n';
            std::ofstream binary(out/"maps"/(row.at("candidate_id")+".f32"),std::ios::binary);binary.write(reinterpret_cast<const char*>(hit.data()),hit.size()*sizeof(float));
        }
        std::cout<<"SOURCE_BLIND_FORWARD_COMPLETE arm="<<arm<<" candidates="<<leaves.size()<<'\n';return 0;
    } catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
