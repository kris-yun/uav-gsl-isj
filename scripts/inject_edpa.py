#!/usr/bin/env python3
"""Inject EDPA-GSL code into OPGSL.cpp and OPGSL.hpp"""
import os, re, shutil

OPGSL_DIR = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL"

for f in ["OPGSL.cpp", "OPGSL.hpp"]:
    src = os.path.join(OPGSL_DIR, f)
    bak = src + ".pre_edpa"
    if not os.path.exists(bak):
        shutil.copy2(src, bak)
        print("Backed up " + f)

# Read current OPGSL.cpp
cpp_path = os.path.join(OPGSL_DIR, "OPGSL.cpp")
with open(cpp_path, "r") as f:
    cpp = f.read()

# Check if already patched
if "EDPA-GSL Layer 1" in cpp:
    print("Already patched, skipping")
else:
    # Step 1: Add parameter declarations
    old_param = '    use_sc_ = getParam<bool>("opgsl.modules.sc", false);'
    new_params = old_param + """
    use_edpa_ = getParam<bool>("opgsl.modules.edpa", false);
    detection_threshold_ = getParam<float>("opgsl.edpa.detection_threshold", 0.01f);
    arrival_rate_lambda0_ = getParam<float>("opgsl.edpa.lambda0", 1.0f);
    arrival_rate_ell_ = getParam<float>("opgsl.edpa.ell", 2.0f);
    arrival_rate_alphaw_ = getParam<float>("opgsl.edpa.alphaw", 0.5f);"""
    cpp = cpp.replace(old_param, new_params)
    print("Added EDPA parameters")

    # Step 2: Add EDPA mode check after posterior update
    old_posterior = '    posterior3d_.update(cx, cy, current_altitude_, std::max(latest_gas_, 0.0001f), wx, wy, ws);'
    edpa_block = old_posterior + """

    // ====== EDPA-GSL Mode ======
    if (use_edpa_) {
        bool detected = (latest_gas_ > detection_threshold_);
        updatePosteriorEventDriven(cx, cy, current_altitude_, detected,
                                    latest_gas_, wx, wy, ws);
        float R_t = computeCredibleRegionRadius();
        float H_t = posterior3d_.getEntropy();
        if (!entropy_initialized_) { initial_entropy_ = H_t; entropy_initialized_ = true; }
        float gamma = (initial_entropy_ > 1e-6f) ? (H_t / initial_entropy_) : 0.0f;
        gamma = std::clamp(gamma, 0.0f, 1.0f);
        
        // Layer 3: Check stopping
        float contraction = cr_stopping_.prev_radius - R_t;
        float e_val = 1.0f + cr_stopping_.eta * std::max(0.0f, contraction);
        cr_stopping_.e_process *= e_val;
        cr_stopping_.prev_radius = R_t;
        if (step_count_ > cr_stopping_.warmup_steps &&
            cr_stopping_.e_process >= 1.0f / cr_stopping_.delta && R_t <= cr_stopping_.epsilon) {
            float mx, my, mz;
            posterior3d_.getMAP(mx, my, mz);
            best_x = mx; best_y = my;
            clipToMapBounds(best_x, best_y);
            GSL_INFO("EDPA-STOP: R_t={:.2f} e={:.1f} MAP=({:.2f},{:.2f})", R_t, cr_stopping_.e_process, mx, my);
            return;
        }
        
        // Layer 2: Adaptive EIG
        auto eig_r = computeAdaptiveEIG();
        best_x = eig_r.x; best_y = eig_r.y;
        clipToMapBounds(best_x, best_y);
        GSL_INFO("EDPA-SEARCH: ({:.2f},{:.2f}) g={:.2f} eig={:.4f} R={:.2f} s={}",
                 best_x, best_y, gamma, eig_r.eig_value, R_t, step_count_);
        return;
    }
"""
    cpp = cpp.replace(old_posterior, edpa_block)
    print("Inserted EDPA mode check")

    # Step 3: Append implementation functions before last closing brace
    impl = """
// ====== EDPA-GSL Layer 1: Event-Driven Posterior ======
void OPGSL::updatePosteriorEventDriven(float cx, float cy, float cz,
                                        bool detected, float concentration,
                                        float wind_x, float wind_y, float wind_speed) {
    if (!posterior3d_.initialized_) return;
    float decay = 0.995f;
    for (int ii=0;ii<posterior3d_.nx_;ii++)
        for (int jj=0;jj<posterior3d_.ny_;jj++)
            for (int kk=0;kk<posterior3d_.nz_;kk++)
                posterior3d_.grid[ii][jj][kk] *= decay;
    float wind_dir = std::atan2(wind_y, wind_x);
    float max_log = -1e9f;
    for (int i=0;i<posterior3d_.nx_;i++)
        for (int j=0;j<posterior3d_.ny_;j++)
            for (int k=0;k<posterior3d_.nz_;k++) {
                float sx=posterior3d_.x_min_+(i+0.5f)*posterior3d_.dx_;
                float sy=posterior3d_.y_min_+(j+0.5f)*posterior3d_.dy_;
                float sz=posterior3d_.z_min_+(k+0.5f)*posterior3d_.dz_;
                float dx=cx-sx, dy=cy-sy, dz=cz-sz;
                float dist=std::sqrt(dx*dx+dy*dy+dz*dz);
                float dist_decay=std::exp(-dist/arrival_rate_ell_);
                float s_to_x=std::atan2(dy,dx);
                float angle_diff=s_to_x-wind_dir;
                float wind_mod=1.0f+arrival_rate_alphaw_*std::cos(angle_diff);
                wind_mod=std::max(wind_mod,0.1f);
                float lambda=arrival_rate_lambda0_*dist_decay*wind_mod;
                float p_det=1.0f-std::exp(-lambda*0.1f);
                float ll;
                if(detected) ll=std::log(std::max(p_det,1e-10f));
                else ll=std::log(std::max(1.0f-p_det,1e-10f));
                posterior3d_.grid[i][j][k]+=ll;
                if(posterior3d_.grid[i][j][k]>max_log) max_log=posterior3d_.grid[i][j][k];
            }
    float log_sum=-1e9f;
    for(int i=0;i<posterior3d_.nx_;i++)
        for(int j=0;j<posterior3d_.ny_;j++)
            for(int k=0;k<posterior3d_.nz_;k++){
                posterior3d_.grid[i][j][k]-=max_log;
                log_sum=std::log(std::exp(log_sum)+std::exp(posterior3d_.grid[i][j][k]));}
    for(int i=0;i<posterior3d_.nx_;i++)
        for(int j=0;j<posterior3d_.ny_;j++)
            for(int k=0;k<posterior3d_.nz_;k++)
                posterior3d_.grid[i][j][k]-=log_sum;
}

float OPGSL::computeEIGGlobal(float cx,float cy,float cz,
                                float wx,float wy,float ws){
    float mc=0,vc=0;
    for(int i=0;i<posterior3d_.nx_;i++)
        for(int j=0;j<posterior3d_.ny_;j++)
            for(int k=0;k<posterior3d_.nz_;k++){
                float p=std::exp(posterior3d_.grid[i][j][k]);
                float sx=posterior3d_.x_min_+(i+0.5f)*posterior3d_.dx_;
                float sy=posterior3d_.y_min_+(j+0.5f)*posterior3d_.dy_;
                float sz=posterior3d_.z_min_+(k+0.5f)*posterior3d_.dz_;
                float ll=posterior3d_.plumeLogLikelihood(sx,sy,sz,cx,cy,cz,wx,wy,ws);
                float cp=std::exp(ll);
                mc+=p*cp; vc+=p*cp*cp;}
    vc-=mc*mc;
    return std::max(vc,0.0f);
}

float OPGSL::computeEIGLocal(float cx,float cy,float cz,
                               float wx,float wy,float ws){
    float eig=computeEIGGlobal(cx,cy,cz,wx,wy,ws);
    float mx,my,mz;
    posterior3d_.getMAP(mx,my,mz);
    float dx=mx-cx,dy=my-cy;
    float dist=std::sqrt(dx*dx+dy*dy);
    if(dist>0.1f&&ws>0.05f){
        float wn=std::sqrt(wx*wx+wy*wy);
        float ux=-wx/wn,uy=-wy/wn;
        float align=(dx*ux+dy*uy)/dist;
        eig*=std::exp(1.0f*align);}
    return eig;
}

OPGSL::AdaptiveEIGResult OPGSL::computeAdaptiveEIG(){
    AdaptiveEIGResult r;
    float wx=latest_wind_x_,wy=latest_wind_y_,ws=latest_wind_speed_;
    float cx=currentRobotPosition.x,cy=currentRobotPosition.y;
    float Ht=posterior3d_.getEntropy();
    if(!entropy_initialized_){initial_entropy_=Ht;entropy_initialized_=true;}
    float gamma=(initial_entropy_>1e-6f)?(Ht/initial_entropy_):0.0f;
    gamma=std::clamp(gamma,0.0f,1.0f);
    float best_eig=-1e9f,best_x=cx,best_y=cy;
    int nc=12; float sr=2.0f;
    for(int a=0;a<nc;a++){
        float ang=2.0f*M_PI*a/nc;
        float cax=cx+sr*std::cos(ang),cay=cy+sr*std::sin(ang);
        clipToMapBounds(cax,cay);
        float eg=computeEIGGlobal(cax,cay,current_altitude_,wx,wy,ws);
        float el=computeEIGLocal(cax,cay,current_altitude_,wx,wy,ws);
        float egamma=(1.0f-gamma)*el+gamma*eg;
        if(egamma>best_eig){best_eig=egamma;best_x=cax;best_y=cay;}}
    r.x=best_x;r.y=best_y;r.z=current_altitude_;
    r.eig_value=best_eig;r.gamma=gamma;
    return r;
}

float OPGSL::computeCredibleRegionRadius(){
    float mx,my,mz;
    posterior3d_.getMAP(mx,my,mz);
    float target=1.0f-cr_stopping_.alpha;
    float acc=0;
    std::vector<std::pair<float,float>> dp;
    for(int i=0;i<posterior3d_.nx_;i++)
        for(int j=0;j<posterior3d_.ny_;j++)
            for(int k=0;k<posterior3d_.nz_;k++){
                float p=std::exp(posterior3d_.grid[i][j][k]);
                float sx=posterior3d_.x_min_+(i+0.5f)*posterior3d_.dx_;
                float sy=posterior3d_.y_min_+(j+0.5f)*posterior3d_.dy_;
                float sz=posterior3d_.z_min_+(k+0.5f)*posterior3d_.dz_;
                float d=std::sqrt((sx-mx)*(sx-mx)+(sy-my)*(sy-my)+(sz-mz)*(sz-mz));
                dp.push_back({d,p});}
    std::sort(dp.begin(),dp.end());
    for(auto&[d,p]:dp){acc+=p;if(acc>=target)return d;}
    return 100.0f;
}
"""
    last_brace = cpp.rfind("}")
    cpp = cpp[:last_brace] + impl + "\n" + cpp[last_brace:]
    print("Appended EDPA implementations")

    with open(cpp_path, "w") as f:
        f.write(cpp)
    print("OPGSL.cpp patched successfully!")

# Step 4: Patch OPGSL.hpp
hpp_path = os.path.join(OPGSL_DIR, "OPGSL.hpp")
with open(hpp_path, "r") as f:
    hpp = f.read()

if "EDPA-GSL" not in hpp:
    edpa_hpp = """
    // EDPA-GSL Layer 1
    void updatePosteriorEventDriven(float cx, float cy, float cz,
                                     bool detected, float concentration,
                                     float wind_x, float wind_y, float wind_speed);
    // EDPA-GSL Layer 2
    struct AdaptiveEIGResult { float x,y,z,eig_value,gamma; };
    AdaptiveEIGResult computeAdaptiveEIG();
    float computeEIGGlobal(float cx,float cy,float cz,float wx,float wy,float ws);
    float computeEIGLocal(float cx,float cy,float cz,float wx,float wy,float ws);
    // EDPA-GSL Layer 3
    struct CredibleRegionStopping {
        float epsilon=1.5f,alpha=0.10f,eta=5.0f,delta=0.10f;
        float e_process=1.0f,prev_radius=1e9f;
        int warmup_steps=5; bool fired=false;
    };
    CredibleRegionStopping cr_stopping_;
    float computeCredibleRegionRadius();
    bool use_edpa_=false;
    float detection_threshold_=0.01f;
    float arrival_rate_lambda0_=1.0f,arrival_rate_ell_=2.0f,arrival_rate_alphaw_=0.5f;
    float initial_entropy_=1.0f; bool entropy_initialized_=false;
"""
    last_brace = hpp.rfind("}")
    hpp = hpp[:last_brace] + edpa_hpp + "\n" + hpp[last_brace:]
    with open(hpp_path, "w") as f:
        f.write(hpp)
    print("OPGSL.hpp patched successfully!")
else:
    print("OPGSL.hpp already patched")

print("=== INJECTION COMPLETE ===")
