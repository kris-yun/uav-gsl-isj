#include <gsl_server/algorithms/OPGSLScientificV31/OPGSLScientificV31.hpp>

#include <cassert>
#include <iostream>

using namespace GSL::OPGSLV3;

static ObservationModelEnsemble makeModels(bool vertical_valid) {
    std::vector<ObservationModelParameters> models;
    for (int i = 0; i < 16; ++i) {
        ObservationModelParameters p;
        p.model_id = i;
        p.nominal = i == 0;
        p.isotropic_intercept = 1.0;
        p.isotropic_distance_decay = 0.8;
        p.wind_intercept = 2.0;
        p.downwind_distance_decay = 0.3;
        p.upstream_distance_decay = 2.0;
        p.crosswind_squared_decay = 0.4;
        p.vertical_squared_decay = 2.0 + 0.02 * i;
        p.wind_noise_speed_sigma = 0.1;
        models.push_back(p);
    }
    CalibrationMetadata meta;
    meta.scientific_valid = true;
    meta.vertical_feature_valid = vertical_valid;
    meta.calibration_id = "vertical_test";
    ObservationModelEnsemble ensemble;
    ensemble.setModels(models, meta);
    return ensemble;
}

int main() {
    GridSpec spec;
    spec.nx = 3;
    spec.ny = 3;
    spec.nz = 4;
    spec.x_min = -1.5;
    spec.x_max = 1.5;
    spec.y_min = -1.5;
    spec.y_max = 1.5;
    spec.z_min = -0.5;
    spec.z_max = 1.5;
    JointSourceModelPosterior posterior;
    posterior.initialize(spec, {}, makeModels(true).normalizedPriorWeights());

    ObservationContext context;
    context.wind_x = 0.4;
    context.wind_speed = 0.4;
    context.detection_threshold = 0.1;

    std::vector<FeasibleAction> actions = {
        {1.0, 0.0, 0.5, ActionType::PlanarTraverse, 0},
        {0.0, 0.0, 1.0, ActionType::VerticalProbe, 0},
    };
    PlannerConfig config;
    config.vertical_actions_requested = true;
    config.vertical_posterior_quantile = 0.05;
    InformationRatePlanner planner(config);

    const auto invalid = planner.choose(
        actions, 0.0, 0.0, 0.5, context, posterior, makeModels(false));
    assert(invalid.selected.has_value());
    assert(!invalid.vertical_gate_open);
    assert(invalid.reason == "vertical_model_not_validated");

    const auto valid = planner.choose(
        actions, 0.0, 0.0, 0.5, context, posterior, makeModels(true));
    assert(valid.selected.has_value());
    // Whether it opens depends on actual information-rate dominance, but the
    // decision must be based on the paired lower confidence bound.
    assert(valid.reason == "vertical_rate_advantage_supported" ||
           valid.reason == "vertical_rate_advantage_not_supported");

    std::cout << "OPGSL V3 vertical gate tests passed\n";
    return 0;
}
