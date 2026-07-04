
// ============================================================
// EDPA-GSL: Event-Driven Posterior-Adaptive GSL
// Added to OPGSL.hpp (inside class OPGSL, public section)
// ============================================================
// Layer 1: Event-driven observation model
void updatePosteriorEventDriven(float cx, float cy, float cz,
                                 bool detected, float concentration,
                                 float wind_x, float wind_y, float wind_speed);

// Layer 2: Posterior-adaptive EIG
struct AdaptiveEIGResult {
    float x, y, z;
    float eig_value;
    float gamma;  // search granularity
};
AdaptiveEIGResult computeAdaptiveEIG();
float computeEIGGlobal(float cx, float cy, float cz,
                        float wind_x, float wind_y, float wind_speed);
float computeEIGLocal(float cx, float cy, float cz,
                       float wind_x, float wind_y, float wind_speed);

// Layer 3: Anytime-valid stopping
struct CredibleRegionStopping {
    float epsilon = 1.5f;       // target accuracy (meters)
    float alpha = 0.10f;        // credible level
    float eta = 5.0f;           // e-value sensitivity
    float delta = 0.10f;        // false positive rate
    float e_process = 1.0f;     // accumulated e-process
    float prev_radius = 1e9f;   // previous credible region radius
    int warmup_steps = 5;
    bool fired = false;
    
    bool checkAndUpdate(float current_radius, int step);
    void reset();
};
CredibleRegionStopping cr_stopping_;

// EDPA-GSL parameters
bool use_edpa_ = false;  // enable EDPA-GSL mode
float detection_threshold_ = 0.01f;  // tau_det for binary detection
float arrival_rate_lambda0_ = 1.0f;  // source emission rate
float arrival_rate_ell_ = 2.0f;      // characteristic transport length
float arrival_rate_alphaw_ = 0.5f;   // wind anisotropy
float initial_entropy_ = 1.0f;       // H(pi_0) for gamma computation
bool entropy_initialized_ = false;
