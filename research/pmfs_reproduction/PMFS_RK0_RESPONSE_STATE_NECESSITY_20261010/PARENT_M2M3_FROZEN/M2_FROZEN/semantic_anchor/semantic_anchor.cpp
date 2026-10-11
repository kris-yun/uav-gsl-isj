// Synthetic single-cell source-level anchor. No ROS init, candidate transport,
// source posterior update, navigation, or external observations are invoked.
#include <gsl_server/algorithms/PMFS/PMFSLib.hpp>
#include <gsl_server/algorithms/PMFS/internal/HitProbability.hpp>
#include <gsl_server/algorithms/PMFS/internal/VisibilityMap.hpp>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>

using namespace GSL;
using namespace GSL::PMFS_internal;
namespace fs = std::filesystem;

int main(int argc, char** argv) {
    if (argc != 2) { std::cerr << "usage: semantic_anchor NEW_OUTPUT\n"; return 2; }
    fs::path out = argv[1];
    if (fs::exists(out)) { std::cerr << "refuse existing output\n"; return 3; }
    fs::create_directory(out);
    Grid2DMetadata meta;
    meta.dimensions = {1,1}; meta.origin = {0,0}; meta.cellSize = .25;
    meta.numFreeCells = 1; meta.scale = 1;
    std::vector<Occupancy> occupancy(1,Occupancy::Free);
    std::vector<HitProbability> measured(1);
    std::vector<double> posterior(1,1);
    std::vector<Vector2> wind(1,Vector2{0,0});
    Grid2D<HitProbability> grid(measured,occupancy,meta);
    Grid2D<double> source(posterior,occupancy,meta);
    Grid2D<Vector2> flow(wind,occupancy,meta);
    VisibilityMap visible(1,1,0);
    visible.emplace(Vector2Int{0,0},std::vector<Vector2Int>{{0,0}});
    HitProbabilitySettings hp;
    hp.prior=.3; hp.kernelSigma=1.5; hp.kernelStretchConstant=1.5;
    hp.confidenceMeasurementWeight=1; hp.confidenceSigmaSpatial=1;
    hp.localEstimationWindowSize=0; hp.maxUpdatesPerStop=200;
    SimulationSettings settings; settings.sourceDiscriminationPower=.4;
    Simulations scoring(grid,source,flow,settings);
    std::vector<float> q_true(1,.6f), q_wrong(1,.9f);
    std::ofstream steps(out/"native_steps.csv"), finals(out/"native_counts.csv");
    const char* header="n,total_hits,ordering,step,event_hit,logOdds,probability,omega,confidence,auxWeight,source_score_true,source_score_wrong,unit_confidence_score_true,unit_confidence_score_wrong,frequency_score_true_double,frequency_score_wrong_double\n";
    steps << std::setprecision(21) << header;
    finals << std::setprecision(21) << header;
    size_t updates=0, score_calls=0;
    for (int n : {5,10,20,50,100,200}) {
        for (int k=0;k<=n;k++) {
            for (int order=0;order<2;order++) {
                measured[0]=HitProbability{};
                measured[0].setProbability(hp.prior);
                for (int step=0;step<=n;step++) {
                    bool hit=false;
                    if (step>0) {
                        hit=order==0 ? step<=k : step>n-k;
                        PMFSLib::EstimateHitProbabilities(grid,visible,hp,hit,0.,0.,{0,0});
                        updates++;
                    }
                    // All scoring calls operate on explicitly supplied scalar frequencies,
                    // not on newly generated candidate predictions.
                    long double st=scoring.sourceProbFromMaps(grid,q_true);
                    long double sw=scoring.sourceProbFromMaps(grid,q_wrong);
                    score_calls+=2;
                    HitProbability unit=measured[0]; unit.confidence=1;
                    double ut=scoring.probabilityFromSingleCell(unit,double(q_true[0]));
                    double uw=scoring.probabilityFromSingleCell(unit,double(q_wrong[0]));
                    double dt=scoring.probabilitySingleFrequency(measured[0].probability(),.6);
                    double dw=scoring.probabilitySingleFrequency(measured[0].probability(),.9);
                    auto write=[&](std::ostream& stream) {
                        stream << n << ',' << k << ',' << (order==0?"hit_first":"miss_first")
                          << ',' << step << ',' << int(hit) << ',' << measured[0].logOdds
                          << ',' << measured[0].probability() << ',' << measured[0].omega
                          << ',' << measured[0].confidence << ',' << measured[0].auxWeight
                          << ',' << st << ',' << sw << ',' << ut << ',' << uw
                          << ',' << dt << ',' << dw << '\n';
                    };
                    if (order==0) write(steps);
                    if (step==n) write(finals);
                }
            }
        }
    }
    std::ofstream counters(out/"native_execution.json");
    counters << "{\"EstimateHitProbabilities_calls\":" << updates
      << ",\"sourceProbFromMaps_calls\":" << score_calls
      << ",\"candidate_forward_calls\":0,\"source_posterior_updates\":0,\"ROS_nodes\":0,\"GADEN_realizations\":0,\"n_values\":[5,10,20,50,100,200]}\n";
    std::cout << "NATIVE_SINGLE_CELL_ANCHOR_COMPLETE\n";
}
