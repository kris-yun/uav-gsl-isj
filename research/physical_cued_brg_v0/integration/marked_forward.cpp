#include <gsl_server/algorithms/Common/Grid2D.hpp>
#include <gsl_server/algorithms/PMFS/PMFSLib.hpp>
#include <gsl_server/algorithms/PMFS/internal/Simulations.hpp>
#include <gsl_server/algorithms/Common/Utils/Math.hpp>
#include <opencv2/imgproc.hpp>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <string>
#include <vector>
#include <cmath>
#include <iomanip>
namespace GSL::PMFS_internal { void setMarkedMultiplicityCounter(std::vector<float>*); }
namespace GSL::Utils { void seedMarkedReplay(unsigned int); }
using namespace GSL;
using namespace GSL::PMFS_internal;
namespace fs=std::filesystem;
using Row=std::map<std::string,std::string>;
static std::vector<std::string> split(const std::string& s) {
    std::vector<std::string> out;size_t b=0;
    while(true){size_t e=s.find(',',b);out.push_back(s.substr(b,e==std::string::npos?e:e-b));if(e==std::string::npos)break;b=e+1;}return out;
}
static std::vector<Row> csv(const fs::path& path) {
    std::ifstream f(path);if(!f)throw std::runtime_error("cannot read "+path.string());
    std::string line;std::getline(f,line);if(!line.empty()&&line.back()=='\r')line.pop_back();auto h=split(line);std::vector<Row> rows;
    while(std::getline(f,line)){if(!line.empty()&&line.back()=='\r')line.pop_back();if(line.empty())continue;auto v=split(line);if(v.size()!=h.size())throw std::runtime_error("CSV width");Row r;for(size_t i=0;i<h.size();++i)r[h[i]]=v[i];rows.push_back(r);}return rows;
}
class MarkedReplay:public Simulations {
public:
    using Simulations::Simulations;
    void run(Vector2 position,std::vector<float>& p,std::vector<float>& u,std::vector<float>& rawp,std::vector<float>& rawu) {
        SimulationSource source(position,measuredHitProb.metadata);
        setMarkedMultiplicityCounter(&u);
        simulateSourceInPosition(source,p,true,settings.iterationsToRecord,settings.deltaTime,settings.noiseSTDev);
        setMarkedMultiplicityCounter(nullptr);
        rawp=p;rawu=u;
        cv::Mat image(p);image=image.reshape(1,measuredHitProb.metadata.dimensions.y);blurHitMap(image);
        // Same native Gaussian and occupancy correction, without treating count as <=1.
        cv::Mat count(u);count=count.reshape(1,measuredHitProb.metadata.dimensions.y);
        cv::GaussianBlur(count,count,cv::Size(0,0),settings.blurSigmaX,settings.blurSigmaY);
        cv::Mat mask;cv::GaussianBlur(freeSpaceMask,mask,cv::Size(0,0),settings.blurSigmaX,settings.blurSigmaY);
        for(int j=0;j<mask.rows;++j)for(int i=0;i<mask.cols;++i)
            if(mask.at<float>(j,i)!=0) count.at<float>(j,i)/=mask.at<float>(j,i);
    }
};
int main(int argc,char**argv) {
 try{
    if(argc!=6)throw std::runtime_error("usage: marked_forward ENV_DIR SOURCE_INDEX STATE SEED OUT_PREFIX");
    const fs::path in(argv[1]),out(argv[5]);const int source=std::stoi(argv[2]),state=std::stoi(argv[3]),seed=std::stoi(argv[4]);
    if(source<0||source>=6||state<0||state>=11||seed<1||seed>8)throw std::runtime_error("frozen index range");
    if(fs::exists(out.string()+".p.f32"))throw std::runtime_error("refuse overwrite");
    cv::setNumThreads(1);Utils::seedMarkedReplay(seed);
    auto rows=csv(in/"meta.csv");auto r=rows.at(0);
    Grid2DMetadata meta;meta.dimensions=Vector2Int(std::stoi(r.at("width")),std::stoi(r.at("height")));
    meta.cellSize=std::stof(r.at("resolution"));meta.origin=Vector2(std::stof(r.at("origin_x")),std::stof(r.at("origin_y")));meta.scale=3;
    const size_t n=meta.dimensions.x*meta.dimensions.y;
    std::vector<unsigned char> bytes(n);std::ifstream f(in/"occupancy.u8",std::ios::binary);f.read(reinterpret_cast<char*>(bytes.data()),n);if(!f)throw std::runtime_error("occupancy read");
    std::vector<Occupancy> occ(n);std::vector<HitProbability> hp(n);std::vector<double> prior(n,0);std::vector<Vector2> wind(n,Vector2(0,0));meta.numFreeCells=0;
    for(size_t i=0;i<n;++i){if(bytes[i]>1)throw std::runtime_error("occupancy byte");occ[i]=bytes[i]?Occupancy::Free:Occupancy::Obstacle;if(bytes[i])++meta.numFreeCells;hp[i].setProbability(.3);hp[i].confidence=0;}
    auto wr=csv(in/("wind_"+std::to_string(state)+".csv"));if(wr.size()!=meta.numFreeCells)throw std::runtime_error("wind count");
    std::vector<bool> seen(n,false);for(const auto&row:wr){size_t k=std::stoul(row.at("cell_index"));if(k>=n||seen[k]||!bytes[k])throw std::runtime_error("wind index");seen[k]=true;wind[k]=Vector2(std::stof(row.at("u")),std::stof(row.at("v")));}
    Grid2D<HitProbability> hit(hp,occ,meta);VisibilityMap visibility(meta.dimensions.x,meta.dimensions.y,5);
    for(int x=0;x<meta.dimensions.x;++x)for(int y=0;y<meta.dimensions.y;++y){
        Vector2Int ij(x,y);if(!hit.freeAt(x,y)){visibility.emplace(ij,{});continue;}std::vector<Vector2Int> visible;
        for(int yy=std::max(0,y-5);yy<=std::min(meta.dimensions.y-1,y+5);++yy)
          for(int xx=std::max(0,x-5);xx<=std::min(meta.dimensions.x-1,x+5);++xx){Vector2Int cell(xx,yy);if(cell==ij||GridUtils::PathFree(meta,occ,meta.indicesToCoordinates(ij),meta.indicesToCoordinates(cell)))visible.push_back(cell);}
        visibility.emplace(ij,visible);
    }
    SimulationSettings settings;settings.useWindGroundTruth=true;settings.maxRegionSize=5;settings.sourceDiscriminationPower=.3;settings.refineFraction=.1;
    settings.minWarmupIterations=200;settings.maxWarmupIterations=500;settings.iterationsToRecord=200;settings.deltaTime=.1;settings.noiseSTDev=.5;settings.blurSigmaX=1.5;settings.blurSigmaY=1.5;
    MarkedReplay replay(hit,Grid2D<double>(prior,occ,meta),Grid2D<Vector2>(wind,occ,meta),settings);
    std::vector<std::vector<uint8_t>> nav(meta.dimensions.x,std::vector<uint8_t>(meta.dimensions.y));
    for(int x=0;x<meta.dimensions.x;++x)for(int y=0;y<meta.dimensions.y;++y)nav[x][y]=hit.freeAt(x,y)?1:0;
    replay.initializeMap(nav);replay.visibilityMap=&visibility;
    auto sr=csv(in/"sources.csv").at(source);if(std::stoi(sr.at("source_index"))!=source)throw std::runtime_error("source ordering");
    Vector2 point(std::stof(sr.at("x")),std::stof(sr.at("y")));auto ix=meta.coordinatesToIndices(point.x,point.y);
    if(!meta.indicesInBounds(ix)||!hit.freeAt(ix))throw std::runtime_error("source outside navigation");
    std::vector<float> p(n,0),u(n,0),rawp,rawu;replay.run(point,p,u,rawp,rawu);
    fs::create_directories(out.parent_path());
    for(const auto&pair:std::vector<std::pair<std::string,std::vector<float>*>>{{"p",&p},{"u",&u},{"rawp",&rawp},{"rawu",&rawu}}){
        for(float v:*pair.second)if(!std::isfinite(v)||v<0)throw std::runtime_error("nonfinite/negative moment");
        std::ofstream f(out.string()+"."+pair.first+".f32",std::ios::binary);f.write(reinterpret_cast<char*>(pair.second->data()),n*sizeof(float));if(!f)throw std::runtime_error("write failed");
    }
    std::cout<<"MARKED_FORWARD_COMPLETE source="<<source<<" state="<<state<<" seed="<<seed<<'\n';return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
