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

static constexpr double MASS=6.440736978853164e-06;
static constexpr double AIR=4.0894632701667424e-05;
static constexpr double SIGMA0=10.0,GAMMA=15.0,THRESHOLD=0.1;
static float single(float sigma,const std::array<float,3>& p,const std::array<float,3>& q){
    float dx=p[0]-q[0],dy=p[1]-q[1],dz=p[2]-q[2];
    float distance_cm=100*std::sqrt(dx*dx+dy*dy+dz*dz);
    constexpr float pi_cubed=M_PI*M_PI*M_PI;
    float moles=float(MASS)/(std::sqrt(8*pi_cubed)*sigma*sigma*sigma);
    float center=1e6*moles/float(AIR);
    return center*std::exp(-(distance_cm*distance_cm)/(2*sigma*sigma));
}
static bool los(const Volume& vol,const std::array<float,3>& start,const std::array<float,3>& end){
    if(!vol.free(start)||!vol.free(end))return false;
    std::array<float,3> v;float distance=0;
    for(int k=0;k<3;k++){v[k]=end[k]-start[k];distance+=v[k]*v[k];}distance=std::sqrt(distance);
    int steps=distance/float(vol.cell);
    if(steps<=1)return true; // same no-interior-query result, avoids unused division by zero
    for(int k=0;k<3;k++)v[k]/=distance;
    float increment=distance/steps;
    for(int j=1;j<steps;j++){std::array<float,3> p;for(int k=0;k<3;k++)p[k]=start[k]+v[k]*(increment*j);if(!vol.free(p))return false;}
    return true;
}
class Replay: public Simulations{
public:
    using Simulations::Simulations;
    std::vector<float> meanC,maxC,nonzeroFraction;
    uint64_t totalActive=0,maxActive=0,queryCount=0,contributionCount=0;
    std::vector<float> gaussian(const fs::path& centers,const Volume& vol,double sensorZ){
        const auto& meta=measuredHitProb.metadata;size_t n=measuredHitProb.data.size();
        std::vector<float> hit(n,0);meanC.assign(n,0);maxC.assign(n,0);nonzeroFraction.assign(n,0);
        std::vector<double> sumC(n,0);totalActive=maxActive=queryCount=contributionCount=0;
        std::ifstream in(centers,std::ios::binary);if(!in)throw std::runtime_error("missing frozen centers");
        for(int t=0;t<settings.iterationsToRecord;t++){
            uint32_t count;in.read((char*)&count,4);if(!in)throw std::runtime_error("trajectory truncated");
            totalActive+=count;maxActive=std::max(maxActive,uint64_t(count));
            std::vector<float> concentration(n,0);
            for(uint32_t j=0;j<count;j++){
                std::array<float,3> p;double age;in.read((char*)p.data(),12);in.read((char*)&age,8);
                if(!in||age<0||!std::isfinite(age))throw std::runtime_error("bad trajectory");
                float sigma=std::sqrt(SIGMA0*SIGMA0+GAMMA*age),radius=sigma*3/100.f;
                if(std::abs(float(sensorZ)-p[2])>=radius)continue;
                // Superset of all sensor-plane queries within cutoff; exact radial test follows.
                int xmin=std::max(0,int(std::floor((p[0]-radius-meta.origin.x)/meta.cellSize))-1);
                int xmax=std::min(meta.dimensions.x-1,int(std::ceil((p[0]+radius-meta.origin.x)/meta.cellSize))+1);
                int ymin=std::max(0,int(std::floor((p[1]-radius-meta.origin.y)/meta.cellSize))-1);
                int ymax=std::min(meta.dimensions.y-1,int(std::ceil((p[1]+radius-meta.origin.y)/meta.cellSize))+1);
                for(int y=ymin;y<=ymax;y++)for(int x=xmin;x<=xmax;x++){
                    auto idx=meta.indexOf({x,y});if(measuredHitProb.occupancy[idx]!=Occupancy::Free)continue;
                    auto xy=meta.indicesToCoordinates({x,y});std::array<float,3> q{xy.x,xy.y,float(sensorZ)};
                    float dx=p[0]-q[0],dy=p[1]-q[1],dz=p[2]-q[2];
                    if(dx*dx+dy*dy+dz*dz<radius*radius&&los(vol,q,p)){concentration[idx]+=single(sigma,p,q);contributionCount++;}
                }
            }
            for(size_t i=0;i<n;i++)if(measuredHitProb.occupancy[i]==Occupancy::Free){
                queryCount++;sumC[i]+=concentration[i];maxC[i]=std::max(maxC[i],concentration[i]);
                if(concentration[i]>0)nonzeroFraction[i]++;
                // Frozen D0 charter boundary; historical PMFS used strict >. Equality audited separately.
                if(concentration[i]>=THRESHOLD)hit[i]++;
            }
        }
        char extra;if(in.read(&extra,1))throw std::runtime_error("extra trajectory records");
        for(size_t i=0;i<n;i++)if(measuredHitProb.occupancy[i]==Occupancy::Free){
            hit[i]/=settings.iterationsToRecord;meanC[i]=sumC[i]/settings.iterationsToRecord;nonzeroFraction[i]/=settings.iterationsToRecord;
        }
        return hit;
    }
};
int main(int argc,char** argv) {
    try {
        if(argc==2&&std::string(argv[1])=="--selftest"){
            std::cout<<"age_s,distance_m,concentration_ppm\n"<<std::setprecision(17);
            for(double age:{0.,0.2,1.,10.,40.})for(float d:{0.f,0.05f,0.1f,0.2f}){
                float sigma=std::sqrt(SIGMA0*SIGMA0+GAMMA*age);
                std::cout<<age<<','<<d<<','<<single(sigma,{0,0,0},{d,0,0})<<'\n';
            }
            float tiny=1e-4f; if(!(single(tiny,{0,0,0},{0,0,0})>0&&single(tiny,{0,0,0},{0.01f,0,0})==0))throw std::runtime_error("tiny sigma support");
            return 0;
        }
        if(argc!=6) throw std::runtime_error("usage: oracle_forward INPUT_DIR CONFIG_CSV native|oracle2d|oracle3d OUTPUT_DIR");
        fs::path input(argv[1]),out(argv[4]);std::string arm(argv[3]);
        if(arm!="g2"&&arm!="g3") throw std::runtime_error("unknown arm");
        if(fs::exists(out)) throw std::runtime_error("output exists; refusing overwrite");
        auto configs=csv(argv[2]);if(configs.size()!=1) throw std::runtime_error("single config required");const Row& cfg=configs[0];
        auto cells=csv(input/"measured_hit_probability.csv"),leaves=csv(input/"active_candidates.csv");
        Grid2DMetadata meta;meta.dimensions={integer(cfg,"width"),integer(cfg,"height")};meta.cellSize=float(num(cfg,"cell"));meta.origin={float(num(cfg,"origin_x")),float(num(cfg,"origin_y"))};meta.scale=3;meta.numFreeCells=0;
        size_t n=size_t(meta.dimensions.x)*meta.dimensions.y;
        if(cells.size()!=n) throw std::runtime_error("cell count");
        std::vector<Occupancy> occ(n);std::vector<HitProbability> hp(n);std::vector<Vector2> wind(n,Vector2(0,0));std::vector<double> posterior(n,0);
        for(auto& row:cells){int i=integer(row,"cell_index");if(i<0||size_t(i)>=n)throw std::runtime_error("cell index");occ[i]=row.at("occupancy")=="Free"?Occupancy::Free:Occupancy::Obstacle;hp[i].logOdds=num(row,"logOdds");hp[i].confidence=num(row,"confidence");if(occ[i]==Occupancy::Free)meta.numFreeCells++;}
        auto volume=std::make_unique<Volume>(cfg.at("occupancy3d"));
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
        fs::create_directories(out/"concentration");fs::create_directories(out/"maps");
        std::ofstream diagnostics(out/"gaussian_diagnostics.csv");diagnostics<<"candidate_id,total_active,max_active,query_count,contribution_count\n";std::ofstream scores(out/"candidate_log_scores.csv");scores<<"candidate_id,log_score\n"<<std::setprecision(21);
        for(const auto& row:leaves) {
            Utils::NQA::Node leaf(nullptr,{integer(row,"origin_i"),integer(row,"origin_j")},{integer(row,"size_i"),integer(row,"size_j")},occupancyMap);
            auto hit=replay.gaussian(fs::path(argv[5])/"trajectories"/(row.at("candidate_id")+".trajbin"),*volume,num(cfg,"sensor_z"));
            long double logScore=0;
            for(size_t i=0;i<n;i++)if(occ[i]==Occupancy::Free) {
                double factor=replay.probabilityFromSingleCell(hp[i],hit[i]);
                if(factor<0||!std::isfinite(factor))throw std::runtime_error("invalid Native factor");
                logScore+=factor==0?-INFINITY:std::log((long double)factor);
            }
            diagnostics<<row.at("candidate_id")<<','<<replay.totalActive<<','<<replay.maxActive<<','<<replay.queryCount<<','<<replay.contributionCount<<'\n';
            for(auto item:{std::make_pair("mean",&replay.meanC),std::make_pair("max",&replay.maxC),std::make_pair("nonzero_fraction",&replay.nonzeroFraction)}){
                std::ofstream stream(out/"concentration"/(row.at("candidate_id")+"_"+item.first+".f32"),std::ios::binary);
                stream.write((const char*)item.second->data(),item.second->size()*sizeof(float));
            }
            scores<<row.at("candidate_id")<<','<<logScore<<'\n';
            std::ofstream binary(out/"maps"/(row.at("candidate_id")+".f32"),std::ios::binary);binary.write(reinterpret_cast<const char*>(hit.data()),hit.size()*sizeof(float));
        }
        std::cout<<"SOURCE_BLIND_FORWARD_COMPLETE arm="<<arm<<" candidates="<<leaves.size()<<'\n';return 0;
    } catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
