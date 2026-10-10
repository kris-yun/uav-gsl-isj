// Isolated candidate diagnostic. No updateSourceProbability, ROS init, navigation or posterior output.
#include "Fixture.hpp"
#include <omp.h>
namespace GSL::PMFS_internal {
void r4_set_gaussian(const std::array<float,2500>&,uint16_t);
uint16_t r4_gaussian_index();
}
using namespace R4;

class CandidateDiagnostic: public Simulations {
public:
    using Simulations::Simulations;
    long double one(const Utils::NQA::Node& node, const fs::path& output) {
        std::vector<float> hit(measuredHitProb.data.size(),0.f);
        R4Audit::begin(&node);
        SimulationSource source(&node,measuredHitProb.metadata);
        simulateSourceInPosition(source,hit,true,settings.iterationsToRecord,settings.deltaTime,settings.noiseSTDev);
        R4Audit::before_blur(&node,hit);
        if(settings.blurSigmaX>0 || settings.blurSigmaY>0) {
            cv::Mat image(hit);image=image.reshape(1,measuredHitProb.metadata.dimensions.y);blurHitMap(image);
        }
        long double score=sourceProbFromMaps(measuredHitProb,hit);
        R4Audit::end(&node,hit,score,r4_gaussian_index());
        R4Audit::candidate_log.close();R4Audit::active=false;
        return score;
    }
};

int main(int argc,char**argv) {
try {
    if(argc!=4)throw std::runtime_error("usage: candidate_forward SNAPSHOT ONE_JOB.csv NEW_OUTPUT");
    fs::path snapshot=argv[1],job_file=argv[2],output=argv[3];
    if(fs::exists(output))throw std::runtime_error("output must be new");
    if(omp_get_max_threads()!=1)throw std::runtime_error("OMP_NUM_THREADS must equal 1");
    cv::setNumThreads(1);
    auto job_rows=csv(job_file);if(job_rows.size()!=1)throw std::runtime_error("exactly one frozen job");
    auto job=job_rows[0];
    const int ox=integer(job,"origin_i"),oy=integer(job,"origin_j"),sx=integer(job,"size_i"),sy=integer(job,"size_j");
    if(!((ox==17&&oy==18&&sx==5&&sy==1)||(ox==17&&oy==18&&sx==1&&sy==1)||
         (ox==23&&oy==37&&sx==1&&sy==1)))throw std::runtime_error("region outside frozen M1 contract");
    auto input=csv(snapshot/"input.csv"),metadata=csv(snapshot/"metadata.csv");const auto& row=metadata.at(0);
    Grid2DMetadata meta;meta.dimensions={integer(row,"width"),integer(row,"height")};
    meta.origin={float(d(row,"origin_x")),float(d(row,"origin_y"))};meta.cellSize=d(row,"cell_size");
    meta.numFreeCells=integer(row,"free_cells");meta.scale=25;
    if(meta.dimensions.x!=34||meta.dimensions.y!=45||meta.cellSize!=.25||meta.numFreeCells!=447)
        throw std::runtime_error("unexpected B4 grid");
    size_t count=meta.dimensions.x*meta.dimensions.y;if(input.size()!=count)throw std::runtime_error("grid length");
    std::vector<Occupancy> occupancy(count);std::vector<HitProbability> measured(count);
    std::vector<Vector2> wind(count);std::vector<double> frozen_posterior(count);
    std::vector<std::vector<uint8_t>> image(meta.dimensions.x,std::vector<uint8_t>(meta.dimensions.y));
    for(size_t i=0;i<count;i++) {
        if(integer(input[i],"cell_index")!=i)throw std::runtime_error("cell ordering");
        occupancy[i]=integer(input[i],"occupancy")==1?Occupancy::Free:Occupancy::Obstacle;
        measured[i].logOdds=d(input[i],"logOdds");measured[i].omega=d(input[i],"omega");
        measured[i].confidence=d(input[i],"confidence");wind[i]={float(d(input[i],"u")),float(d(input[i],"v"))};
        frozen_posterior[i]=d(input[i],"prior_posterior");
        image[i%meta.dimensions.x][i/meta.dimensions.x]=occupancy[i]==Occupancy::Free;
    }
    for(int y=oy;y<oy+sy;y++)for(int x=ox;x<ox+sx;x++)
        if(occupancy[meta.indexOf({x,y})]!=Occupancy::Free)throw std::runtime_error("unsupported candidate cell");
    auto parameter_rows=csv(snapshot/"simulation_parameters.csv");const auto& pars=parameter_rows.at(0);
    SimulationSettings settings;settings.maxRegionSize=integer(pars,"maxRegionSize");
    settings.sourceDiscriminationPower=d(pars,"sourceDiscriminationPower");settings.refineFraction=d(pars,"refineFraction");
    settings.deltaTime=d(pars,"deltaTime");settings.noiseSTDev=d(pars,"noiseSTDev");
    settings.iterationsToRecord=integer(pars,"iterationsToRecord");settings.minWarmupIterations=integer(pars,"minWarmupIterations");
    settings.maxWarmupIterations=integer(pars,"maxWarmupIterations");settings.blurSigmaX=d(pars,"blurSigmaX");settings.blurSigmaY=d(pars,"blurSigmaY");
    if(settings.sourceDiscriminationPower!=.4||settings.deltaTime!=.1||settings.noiseSTDev!=.2||
       settings.iterationsToRecord!=200||settings.minWarmupIterations!=200||settings.maxWarmupIterations!=500||
       settings.blurSigmaX!=1.5||settings.blurSigmaY!=1.5)throw std::runtime_error("B4 parameters changed");
    CandidateDiagnostic simulation(Grid2D<HitProbability>(measured,occupancy,meta),
        Grid2D<double>(frozen_posterior,occupancy,meta),Grid2D<Vector2>(wind,occupancy,meta),settings);
    simulation.initializeMap(image);
    VisibilityMap visibility(meta.dimensions.x,meta.dimensions.y,5);
    auto grid=Grid2D<HitProbability>(measured,occupancy,meta);
    for(int x=0;x<meta.dimensions.x;x++)for(int y=0;y<meta.dimensions.y;y++) {
        Vector2Int ij(x,y);std::vector<Vector2Int> visible;
        if(grid.freeAt(x,y))for(int j=std::max(0,y-5);j<=std::min(meta.dimensions.y-1,y+5);j++)
            for(int i=std::max(0,x-5);i<=std::min(meta.dimensions.x-1,x+5);i++) {
                Vector2Int z(i,j);
                if(z==ij||GridUtils::PathFree(meta,occupancy,meta.indicesToCoordinates(ij),meta.indicesToCoordinates(z)))visible.push_back(z);
            }
        visibility.emplace(ij,visible);
    }
    simulation.visibilityMap=&visibility;
    std::array<float,2500> cache;
    std::ifstream cache_file(snapshot/"gaussian_cache.f32",std::ios::binary);
    cache_file.read(reinterpret_cast<char*>(cache.data()),sizeof(cache));if(!cache_file)throw std::runtime_error("gaussian cache");
    const uint16_t phase=integer(job,"gaussian_index_before");
    // Restore Gaussian table/phase BEFORE engine state, cancelling lazy cache-init draws.
    r4_set_gaussian(cache,phase);Utils::r4_rng_restore(job.at("rng_before"));
    R4Replay::enabled=false;R4Replay::points.clear();R4Replay::offset=0;  // Native uniform sampling, no old-point substitution.
    fs::create_directories(output/"maps");fs::create_directories(output/"points");
    R4Audit::initialize(output);R4Audit::cache_ready=true;R4Audit::last_index=phase;
    R4Audit::binary(output/"gaussian_cache.f32",std::vector<float>(cache.begin(),cache.end()));
    Utils::NQA::Node node(nullptr,{ox,oy},{sx,sy},image);
    const std::string before=Utils::r4_rng_state();
    const long double score=simulation.one(node,output);
    if(R4Replay::enabled||R4Replay::offset!=0)throw std::runtime_error("recorded-point substitution prohibited");
    std::ofstream result(output/"RESULT.json");result<<std::setprecision(21)
        <<"{\"scope\":\"ONE_2D_CANDIDATE_FORWARD_NO_POSTERIOR_UPDATE\",\"score\":"<<score
        <<",\"forward_calls\":1,\"native_updates\":0,\"ROS_nodes\":0,\"source_region\":["<<ox<<","<<oy<<","<<sx<<","<<sy
        <<"],\"rng_before\":\""<<before<<"\",\"rng_after\":\""<<Utils::r4_rng_state()
        <<"\",\"gaussian_index_before\":"<<phase<<",\"gaussian_index_after\":"<<r4_gaussian_index()
        <<",\"release_points\":"<<R4Audit::point_count<<",\"captured_point_substitution\":false}";
    return 0;
} catch(const std::exception& error) {std::cerr<<error.what()<<"\n";return 1;}
}
