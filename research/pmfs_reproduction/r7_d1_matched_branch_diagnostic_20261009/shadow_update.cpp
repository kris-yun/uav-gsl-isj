#include "Fixture.hpp"
#include <omp.h>

namespace GSL::PMFS_internal {
void r4_set_gaussian(const std::array<float,2500>&, uint16_t);
uint16_t r4_gaussian_index();
}
using namespace R4;

int main(int argc, char** argv) {
    try {
        if (argc != 3) throw std::runtime_error("SHADOW INPUT OUTPUT");
        fs::path input = argv[1], out = argv[2];
        if (fs::exists(out)) throw std::runtime_error("diagnostic output already exists");
        if (omp_get_max_threads() != 1) throw std::runtime_error("OMP threads must equal 1");
        fs::create_directories(out);
        Fixture f(input);
        f.meta.scale = 25;
        f.sim.iterationsToRecord = 300;
        f.sim.minWarmupIterations = 200;
        f.sim.maxWarmupIterations = 800;
        auto original = csv(input / "input.csv");
        auto events = csv(input / "measurement_events.csv");
        auto candidates = csv(input / "candidates.csv");
        if (events.size() != 40 || candidates.size() != 106)
            throw std::runtime_error("R7 evidence dimensions");
        std::ofstream blocks(out / "measurement_reconstruction.csv");
        blocks << std::setprecision(17) << "event_index,stamp_ns,iteration_counter,hit,grid_i,grid_j\n";
        double maxLogOdds = 0, maxOmega = 0, maxConfidence = 0;
        for (size_t e = 0; e < 35; ++e) {
            const auto& row = events[e];
            auto ij = f.meta.coordinatesToIndices(float(d(row,"robot_x")),float(d(row,"robot_y")));
            bool hit = d(row,"concentration") > .1;
            f.measurement(hit,d(row,"wind_direction"),d(row,"wind_speed"),ij);
            blocks << e << ',' << row.at("stamp_ns") << ',' << row.at("iteration_counter") << ',' << hit << ',' << ij.x << ',' << ij.y << '\n';
            if (e == 34) {
                f.dumpHit(out / "hit_at_native_boundary_35.csv");
                for (size_t i=0; i<f.hit.size(); ++i) {
                    if (f.occupancy[i] != Occupancy::Free) continue;
                    maxLogOdds = std::max(maxLogOdds,std::abs(f.hit[i].logOdds-d(original[i],"logOdds")));
                    maxOmega = std::max(maxOmega,std::abs(f.hit[i].omega-d(original[i],"omega")));
                    maxConfidence = std::max(maxConfidence,std::abs(f.hit[i].confidence-d(original[i],"confidence")));
                }
                std::ofstream gate(out / "MEASUREMENT_GATE.json");
                gate << std::setprecision(17) << "{\"free_cells\":518,\"max_logOdds_abs\":" << maxLogOdds
                     << ",\"max_omega_abs\":" << maxOmega << ",\"max_confidence_abs\":" << maxConfidence << '}';
                gate.close();
                if (maxLogOdds > 1e-12 || maxOmega > 1e-12 || maxConfidence > 1e-12)
                    throw std::runtime_error("MEASUREMENT_RECONSTRUCTION_GATE_HOLD; no source update executed");
            }
            if (e >= 35) f.dumpHit(out / ("hit_after_event_"+std::to_string(e)+".csv"));
        }
        std::ifstream saved(input / "posterior.f64",std::ios::binary);
        saved.read(reinterpret_cast<char*>(f.posterior.data()),f.posterior.size()*sizeof(double));
        if (!saved) throw std::runtime_error("posterior read");
        auto sim = f.simulation();
        f.restoreCapturedTree(*sim,input);
        std::array<float,2500> table;
        std::ifstream cache(input / "gaussian_cache.f32",std::ios::binary);
        cache.read(reinterpret_cast<char*>(table.data()),sizeof(table));
        if (!cache) throw std::runtime_error("noise cache read");
        auto& last = candidates.back();
        uint16_t noiseIndex = integer(last,"gaussian_index_after");
        r4_set_gaussian(table,noiseIndex);
        Utils::r4_rng_restore(last.at("rng_after"));
        // Exactly one common RNG use by the already executed k=6 native movement.
        // k=7 movement is after this counterfactual source update and is not run.
        double actualMovementDraw = Utils::uniformRandom(0,1);
        std::ofstream rng(out / "CONTINUATION_RNG.json");
        rng << std::setprecision(17) << "{\"rng_at_last_simulation_end\":\"" << last.at("rng_after")
            << "\",\"movement_uniform_calls\":1,\"movement_draw\":" << actualMovementDraw
            << ",\"rng_before_shadow\":\"" << Utils::r4_rng_state() << "\",\"gaussian_index_before_shadow\":" << noiseIndex << '}';
        rng.close();
        R4Audit::initialize(out / "shadow_update");
        R4Audit::tree(sim->QTleaves,"coarse_tree.csv");
        R4Audit::gaussian(table,noiseIndex);
        std::ofstream snap(out / "shadow_update/input.csv");
        snap << std::setprecision(17) << "cell_index,grid_i,grid_j,occupancy,logOdds,omega,confidence,u,v,prior_posterior\n";
        for (size_t i=0; i<f.hit.size(); ++i)
            snap << i << ',' << i%f.meta.dimensions.x << ',' << i/f.meta.dimensions.x << ',' << int(f.occupancy[i])
                 << ',' << f.hit[i].logOdds << ',' << f.hit[i].omega << ',' << f.hit[i].confidence
                 << ',' << f.wind[i].x << ',' << f.wind[i].y << ',' << f.posterior[i] << '\n';
        snap.close();
        std::ofstream(out / "SOURCE_UPDATE_STARTED.json") << "{\"shadow_source_updates\":1,\"native_goals\":0}";
        sim->updateSourceProbability(f.sim.refineFraction);
        R4Audit::finish(f.posterior);
        R4Audit::binary(out / "shadow_update/variance_of_hit_probability.f64",sim->varianceOfHitProb);
        auto post = Grid2D<double>(f.posterior,f.occupancy,f.meta);
        auto mean = Utils::ExpectedValue(post,1);
        double var = Utils::Variance(post);
        std::ofstream complete(out / "COMPLETE.json");
        complete << std::setprecision(17) << "{\"classification\":\"COUNTERFACTUAL_DIAGNOSTIC_NOT_NATIVE_RUN\",\"shadow_source_updates\":1,\"native_goals\":0,\"new_gas_generations\":0,\"observations\":35,\"appended_observations\":0,\"native_variance_formula\":" << var
                 << ",\"native_mean_x\":" << mean.x << ",\"native_mean_y\":" << mean.y
                 << ",\"rng_after_shadow\":\"" << Utils::r4_rng_state() << "\",\"gaussian_index_after_shadow\":" << r4_gaussian_index() << '}';
        complete.close();
        std::cout << "D0_COMPLETE_ONE_SHADOW_UPDATE\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "D0_ERROR: " << e.what() << '\n';
        return 1;
    }
}
