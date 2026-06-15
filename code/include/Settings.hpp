#pragma once

#include <string>
#include <gsl_server/algorithms/Common/Utils/RosUtils.hpp>
#include <gsl_server/core/Vectors.hpp>

namespace GSL::PMFS_internal
{
    struct DeclarationSettings
    {
        double threshold = 1.0;
        int minExplorationIterations = 3;
        double minInformationGain = 0.01;
        bool useWCC = true;
        double wccThreshold = 0.001;
        bool useWRSD = true;
        enum DeclarationMode
        {
            Variance,
            Entropy
        } mode = Variance;
    };

    struct HitProbabilitySettings
    {
        int localEstimationWindowSize = 3;
        int maxUpdatesPerStop = 5;
        double prior = 0.3;
        double kernelSigma = 1.0;
        double kernelStretchConstant = 1.0;
        double confidenceSigmaSpatial = 1.0;
        double confidenceMeasurementWeight = 1.0;

        // Disabled-by-default research toggles. These must not contaminate the baseline.
        bool dbf_enabled = false;
        double dbf_gradient_weight = 0.6;
        double dbf_gradient_threshold = 0.01;
        int dbf_smoothing_passes = 2;
    };

    struct SimulationSettings
    {
        bool useWindGroundTruth = false;
        int maxRegionSize = 10;
        int stepsBetweenSourceUpdates = 3;
        double sourceDiscriminationPower = 0.2;
        double refineFraction = 0.25;
        int maxWarmupIterations = 500;
        int minWarmupIterations = 0;
        int iterationsToRecord = 100;
        double deltaTime = 0.1;
        double noiseSTDev = 0.2;
        double blurSigmaX = 0;
        double blurSigmaY = 0;

        // Disabled-by-default research toggles. Keep official baseline clean.
        bool spc_enabled = false;
        double spc_sparsity_ratio = 0.10;
        double spc_decay_factor = 0.01;
        double spc_min_prob_floor = 1e-8;
        bool fssp_enabled = false;
        double fssp_wiener_nsr = 0.01;
        double fssp_psf_sigma_x = 2.0;
        double fssp_psf_sigma_y = 2.0;

        // SDR: source probability map deconvolution refinement.
        bool sdr_enabled = false;
        int sdr_rl_iterations = 10;
        int sdr_psf_size = 7;
        double sdr_blob_radius = 4.5;
        int sdr_min_hits = 5;
        double sdr_min_peak_mass_ratio = 0.0;

        // BAPR: Boundary-Aware Probability Reshaping (medical image segmentation distance transform)
        bool bapr_enabled = false;
        double bapr_wall_penalty = 2.0;
        double bapr_wall_distance = 2.0;
        double bapr_sigmoid_steepness = 3.0;
        int bapr_dtf_radius = 10;

        // HSPB: Hough-Inspired Spatial Back-Projection (CV Hough Transform)
        bool hspb_enabled = false;
        int hspb_min_hits = 3;
        double hspb_distance_scale = 1.0;
        double hspb_angular_spread = 0.35;
        int hspb_kernel_radius = 3;

        double proximity_weight = 0.5;
        double proximity_sigma = 3.0;
    };

    struct MovementSettings
    {
        double explorationProbability = 0.05;
        int openMoveSetExpasion = 5;
        int initialExplorationMoves = 3;
        double distanceWeight = 0;
        double frontierWeight = 0;
        double edeWeight = 0;

        bool adc_enabled = false;
        double adc_low_threshold = 0.3;
        double adc_mid_threshold = 0.6;
        double adc_low_speed_factor = 0.5;
        double adc_mid_speed_factor = 0.75;

        bool set_enabled = false;
        int set_min_evidence_count = 10;
        double set_confidence_threshold = 0.4;
        int set_consecutive_hits_required = 3;

        bool frg_enabled = false;
        int frg_plume_loss_threshold = 5;
        double frg_recovery_radius = 1.5;
        int frg_max_recovery_steps = 10;
        double frg_crosswind_step = 0.8;
    };

    struct VisualizationSettings
    {
        bool headless = false;
        Utils::valueColorMode hitMode = Utils::valueColorMode::Linear;
        Utils::valueColorMode sourceMode = Utils::valueColorMode::Logarithmic;
        Vector2 hitLimits = Vector2(0, 1);
        Vector2 sourceLimits = Vector2(0.00001, 0.1);
        double markers_height = 0;
    };

    struct MethodControlSettings
    {
        std::string method_id = "baseline";

        // All false by default. The baseline is clean unless a launch file explicitly enables a module.
        bool bwe_enabled = false;
        bool pgpt_enabled = false;
        bool hce_enabled = false;
        bool psde_online_enabled = false;
        bool psde_final_enabled = false;

        // HCE/PGPT collection threshold. This is deliberately independent from thresholdGas so that
        // sensitivity can be audited explicitly.
        double hce_min_concentration = 0.001;

        // BWE is an EMA wind smoother, not a Bayesian estimator. It is optional and must be ablated.
        double bwe_alpha = 0.15;
        double bwe_alpha_fast = 0.40;
        double bwe_min_speed = 0.01;

        // Keep GT diagnostics out of inference logs by default. Final metrics are computed only after
        // the source estimate has been fixed.
        bool gt_debug_logging = false;
        bool verbose_debug = false;
    };

    struct Settings
    {
        DeclarationSettings declaration;
        MovementSettings movement;
        HitProbabilitySettings hitProbability;
        SimulationSettings simulation;
        VisualizationSettings visualization;
        MethodControlSettings method;

        // PWC: Plume Wind Correction. This is a post-processing source-estimate correction.
        struct PwcSettings {
            bool enabled{false};
            double beta{0.5};
            double max_correction{5.0};
            double min_wind{0.01};
            bool use_adaptive{true};
            double plume_scale_factor{1.0};
            bool wind_vector_is_flow_to{true};
            std::string log_file{""};
        } pwc;

        // TDC: Temporal Deconvolution Correction. Disabled unless separately validated.
        struct TdcSettings {
            bool enabled{false};
            int iterations{5};
            double tau{15.0};
            double damping{0.8};
            double sharpen_strength{0.5};
        } tdc;

        // PSDE: Plume Spatial Dispersion Estimator. Legacy launch name may still use mac_*.
        struct MacSettings {
            bool enabled{false};
            double flight_height{1.0};
            double source_height{0.0};
            int stability_class{3};
            double min_distance{0.5};
            double max_distance_weight{6.0};
            double distance_sigma{2.0};
            double sigma_z_max{3.0};
            int min_hits{5};
            int online_update_stride{3};
            double online_boost_weight{0.01};
            bool wind_vector_is_flow_to{true};
        } mac;
    };

} // namespace GSL::PMFS_internal
