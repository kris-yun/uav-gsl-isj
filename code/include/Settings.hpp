#pragma once
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
        // DBF: Delay-and-sum Beamforming Fusion (acoustic beamforming / signal processing)
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
        // SPC: Sparse Source Prior (compressed sensing / iterative hard thresholding)
        bool spc_enabled = false;
        double spc_sparsity_ratio = 0.10;
        double spc_decay_factor = 0.01;
        double spc_min_prob_floor = 1e-8;
        // FSSP: Frequency-domain Source Sharpening (Wiener deconvolution / PET imaging)
        bool fssp_enabled = false;
        double fssp_wiener_nsr = 0.01;
        double fssp_psf_sigma_x = 2.0;
        double fssp_psf_sigma_y = 2.0;
        // SDR: Richardson-Lucy Deconvolution Refinement (medical CT reconstruction)
        bool sdr_enabled = false;
        int sdr_rl_iterations = 10;
        int sdr_psf_size = 7;
        double sdr_blob_radius = 4.5;
        // Proximity-weighted scoring: boost candidates near hit centroid
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
        // ADC: Adaptive Dwell Control (medical CT adaptive exposure)
        bool adc_enabled = false;
        double adc_low_threshold = 0.3;
        double adc_mid_threshold = 0.6;
        double adc_low_speed_factor = 0.5;
        double adc_mid_speed_factor = 0.75;
        // SET: Sequential Evidence Testing (clinical trials SPRT)
        bool set_enabled = false;
        int set_min_evidence_count = 10;
        double set_confidence_threshold = 0.4;
        int set_consecutive_hits_required = 3;
        // FRG: Fault-Reactive Guard (spacecraft fault-tolerant control)
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

    struct Settings
    {
        DeclarationSettings declaration;
        MovementSettings movement;
        HitProbabilitySettings hitProbability;
        SimulationSettings simulation;
        VisualizationSettings visualization;
    
        // PWC: Plume Wind Correction
        struct PwcSettings {
            bool enabled{false};
            double beta{0.5};
            double max_correction{5.0};
            double min_wind{0.005};
            bool use_adaptive{true};
            double plume_scale_factor{1.0};
            std::string log_file{"/tmp/pwc_log.csv"};
        } pwc;

        // TDC: Temporal Deconvolution Correction (medical CT Richardson-Lucy)
        struct TdcSettings {
            bool enabled{false};
            int iterations{5};
            double tau{15.0};
            double damping{0.8};
            double sharpen_strength{0.5};
        } tdc;

        // MAC: Multi-Altitude Constraint (meteorological sounding profile)
        struct MacSettings {
            bool enabled{false};
            double flight_height{1.0};
            double source_height{0.0};
            int stability_class{3};
            double max_distance_weight{3.0};
            double distance_sigma{2.0};
        } mac;
};

} // namespace GSL::PMFS_internal
