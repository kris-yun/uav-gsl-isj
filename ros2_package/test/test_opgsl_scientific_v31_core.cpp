#include <gsl_server/algorithms/OPGSLScientificV31/OPGSLScientificV31.hpp>

#include <cassert>
#include <cmath>
#include <iostream>

using namespace GSL::OPGSLV3;

static ObservationModelEnsemble ensemble(bool vertical_valid = true) {
    ObservationModelParameters nominal;
    nominal.nominal = true;
    nominal.isotropic_intercept = 2.0;
    nominal.isotropic_distance_decay = 1.0;
    nominal.wind_intercept = 3.0;
    nominal.downwind_distance_decay = 0.4;
    nominal.upstream_distance_decay = 2.0;
    nominal.crosswind_squared_decay = 0.6;
    nominal.vertical_squared_decay = 2.0;
    nominal.wind_noise_speed_sigma = 0.1;

    ObservationModelParameters bootstrap = nominal;
    bootstrap.model_id = 1;
    bootstrap.nominal = false;
    bootstrap.vertical_squared_decay = 1.8;

    CalibrationMetadata metadata;
    metadata.scientific_valid = true;
    metadata.vertical_feature_valid = vertical_valid;
    metadata.calibration_house_count = 2;
    metadata.calibration_run_count = 10;
    metadata.calibration_id = "unit_test";

    ObservationModelEnsemble output;
    output.setModels({nominal, bootstrap}, metadata);
    return output;
}

int main() {
    const auto models = ensemble();
    SourcePoint source{0.0, 0.0, 0.0};
    SourcePoint wrong{-3.0, 3.0, 1.0};
    ObservationContext observation;
    observation.sensor_x = 1.0;
    observation.sensor_y = 0.0;
    observation.sensor_z = 0.0;
    observation.wind_x = 0.5;
    observation.wind_y = 0.0;
    observation.wind_speed = 0.5;
    observation.detection_threshold = 0.1;

    const double q_source = models.hitProbability(0, source, observation);
    const double q_wrong = models.hitProbability(0, wrong, observation);
    assert(q_source > q_wrong);

    // Proper evidence has opposite candidate-odds polarity.
    const double hit_increment = std::log(q_source) - std::log(q_wrong);
    const double miss_increment = std::log(1.0 - q_source) -
                                  std::log(1.0 - q_wrong);
    assert(hit_increment > 0.0);
    assert(miss_increment < 0.0);

    GridSpec spec;
    spec.nx = 5;
    spec.ny = 5;
    spec.nz = 3;
    spec.x_min = -2.5;
    spec.x_max = 2.5;
    spec.y_min = -2.5;
    spec.y_max = 2.5;
    spec.z_min = -0.5;
    spec.z_max = 1.0;
    std::vector<bool> mask(75, true);
    // Exclude one complete x/y column across all z levels.
    mask[0] = mask[1] = mask[2] = false;
    JointSourceModelPosterior posterior;
    posterior.initialize(spec, mask, models.normalizedPriorWeights());
    assert(posterior.validSourceCount() == 72);

    const double eig = posterior.expectedSourceInformationGain(observation, models);
    assert(eig >= 0.0 && eig <= kLogTwo + 1e-12);

    observation.concentration = 1.0;
    const auto before = posterior.summary();
    const auto diagnostics = posterior.update(observation, models, EvidenceMode::ProperJoint);
    const auto after = posterior.summary();
    assert(diagnostics.normalization_error < 1e-10);
    assert(std::isfinite(after.entropy));
    assert(after.entropy <= before.entropy + 1e-8);

    PlannerConfig planner_config;
    planner_config.horizontal_speed_mps = 0.4;
    planner_config.vertical_speed_mps = 0.2;
    planner_config.measurement_dwell_seconds = 2.0;
    planner_config.vertical_actions_requested = true;
    planner_config.vertical_posterior_quantile = 0.05;
    InformationRatePlanner planner(planner_config);

    std::vector<FeasibleAction> actions = {
        {1.0, 0.0, 0.0, ActionType::PlanarTraverse, 3},
        {0.0, 0.0, 0.5, ActionType::VerticalProbe, 0},
        {-1.0, 0.0, 0.0, ActionType::PlanarTraverse, 0},
    };
    ObservationContext current = observation;
    current.sensor_x = 0.0;
    current.sensor_y = 0.0;
    current.sensor_z = 0.0;
    current.concentration = 0.0;
    const auto decision = planner.choose(
        actions, 0.0, 0.0, 0.0, current, posterior, models);
    assert(decision.selected.has_value());
    assert(decision.best_planar.has_value());
    assert(decision.best_vertical.has_value());
    for (const auto& score : decision.ranked) {
        assert(score.cycle_time_seconds >= 2.0);
        assert(score.expected_information_bits >= 0.0);
    }

    // The verifier cannot certify a spatially uninformative forecast.
    VerificationConfig verification_config;
    verification_config.target_credible_radius_m = 100.0;
    verification_config.alpha = 0.05;
    PrequentialSkillVerifier verifier(verification_config);
    for (int i = 0; i < 200; ++i) {
        const bool detected = (i % 5) == 0;
        verifier.observeBeforePosteriorUpdate(0.2, detected);
    }
    const auto neutral = verifier.evaluate(posterior.summary());
    assert(!neutral.skill_positive);
    assert(!neutral.verified);

    // A consistently better source forecast eventually obtains positive LCB.
    verifier.reset();
    for (int i = 0; i < 2000; ++i) {
        const bool detected = (i % 5) == 0;
        verifier.observeBeforePosteriorUpdate(detected ? 0.9 : 0.05, detected);
    }
    const auto valid = verifier.evaluate(posterior.summary());
    assert(valid.mean_brier_skill > 0.0);
    assert(valid.brier_skill_lcb > 0.0);
    assert(valid.verified);

    std::cout << "OPGSL V3 scientific core tests passed\n";
    return 0;
}
