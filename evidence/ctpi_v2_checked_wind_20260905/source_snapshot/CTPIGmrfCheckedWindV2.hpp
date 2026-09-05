#pragma once
// Explicit numerical checks around the installed core; no global library edit.
// Neither convergence nor a last-cell observation policy certifies transport.
#include <array>
#include <cstdint>
#include <limits>
#include <map>
#include <stdexcept>
#include "gmrf_wind_core/gmrf_map.h"

namespace GSL::ctpi_v2
{
struct WindSolveAudit
{
    size_t iterations=0, observations=0;
    double relativeChange=0, backwardResidual=0, updateMismatch=0;
};

class CheckedGmrfCore : public gmrfw::CGMRF_map
{
public:
    using CGMRF_map::CGMRF_map;

    WindSolveAudit checkedSolve()
    {
        // Same G as installed source: every prior has target 0 and observation
        // factors select a cell's two Cartesian components. Preserve the source's
        // determinant floor; do not silently substitute a new noise model.
        Eigen::VectorXd rhs=Eigen::VectorXd::Zero(2*N);
        for(const auto& o:activeObs)
        {
            if(o.cell_idx>=N) throw std::runtime_error("GMRF_BAD_OBSERVATION_INDEX");
            const double det=std::max(1e-9,o.var_xx*o.var_yy-o.cov_xy*o.cov_xy);
            rhs[o.cell_idx]+=(o.var_yy*o.wind_x-o.cov_xy*o.wind_y)/det;
            rhs[o.cell_idx+N]+=(o.var_xx*o.wind_y-o.cov_xy*o.wind_x)/det;
        }
        WindSolveAudit audit;
        audit.observations=activeObs.size();
        for(size_t iteration=1;iteration<=100;++iteration)
        {
            Eigen::VectorXd before(2*N);
            for(size_t i=0;i<2*N;++i) before[i]=m_map[i].mean;
            // A swallowed early return must not reuse the preceding solution.
            m_MAP_sol=Eigen::VectorXd::Constant(2*N,std::numeric_limits<double>::quiet_NaN());
            MAP_estimation_GMRF(1);
            if(m_MAP_sol.size()!=static_cast<Eigen::Index>(2*N) || !m_MAP_sol.allFinite() ||
               !Hsparse.coeffs().allFinite() || solver.info()!=Eigen::Success)
                throw std::runtime_error("GMRF_LINEAR_SOLVE_FAILED_OR_EARLY_RETURN");
            const double backward=(Hsparse*m_MAP_sol-rhs).norm()/
                (Hsparse.norm()*m_MAP_sol.norm()+rhs.norm()+1e-30);
            Eigen::VectorXd after(2*N);
            for(size_t i=0;i<2*N;++i) after[i]=m_map[i].mean;
            const double mismatch=(after-(.5*m_MAP_sol+.5*before)).norm()/(after.norm()+1e-30);
            const double change=(after-before).norm()/(after.norm()+1e-9);
            if(!after.allFinite() || !std::isfinite(backward) || backward>1e-10 ||
               !std::isfinite(mismatch) || mismatch>1e-12 || !std::isfinite(change))
                throw std::runtime_error("GMRF_RESIDUAL_OR_UPDATE_CONTRACT_FAILED");
            audit.iterations=iteration; audit.relativeChange=change;
            audit.backwardResidual=std::max(audit.backwardResidual,backward);
            audit.updateMismatch=std::max(audit.updateMismatch,mismatch);
            if(iteration>=2 && change<picard_convergence_thr) return audit;
        }
        throw std::runtime_error("GMRF_FIXED_POINT_DID_NOT_CONVERGE_WITHIN_RESOURCE_LIMIT");
    }
};

class GmrfCheckedWind
{
    CheckedGmrfCore map_;
    bool latestCell_, healthy_=true;
    double stamp_=0.;
    std::map<size_t,gmrfw::TobservationGMRF> latest_;
    WindSolveAudit audit_;
public:
    GmrfCheckedWind(const gmrfw::TOccupancyMap& occupancy,
                   const gmrfw::CGMRF_map::Parameters& parameters, bool latestCell)
        :map_(occupancy,parameters,false,false),latestCell_(latestCell) {}

    void assimilate(double stamp,double x,double y,double u,double v)
    {
        if(!healthy_ || !std::isfinite(stamp) || std::abs(stamp-stamp_-.2)>1e-9 ||
           !std::isfinite(x)||!std::isfinite(y)||!std::isfinite(u)||!std::isfinite(v)||
           !std::isfinite(std::hypot(u,v))) throw std::invalid_argument("GMRF_BAD_INPUT_SEQUENCE");
        healthy_=false;
        if(!map_.insertObservation_GMRF(std::hypot(u,v),std::atan2(v,u),.001,.0001,x,y))
            throw std::runtime_error("GMRF_INSERT_REJECTED");
        if(latestCell_)
        {
            const auto observations=map_.getObservations_GMRF();
            const auto& newest=observations.back();
            latest_[newest.cell_idx]=newest;
            std::vector<gmrfw::TobservationGMRF> kept;
            for(const auto& entry:latest_) kept.push_back(entry.second);
            map_.setObservations_GMRF(kept);
        }
        audit_=map_.checkedSolve();
        stamp_=stamp; healthy_=true;
    }

    gmrfw::WindVector predictAt(double nextStamp,double x,double y)
    {
        if(!healthy_ || stamp_<=0 || !std::isfinite(nextStamp) || std::abs(nextStamp-stamp_-.2)>1e-9 ||
           !std::isfinite(x)||!std::isfinite(y)) throw std::invalid_argument("GMRF_NOT_READY");
        return map_.getEstimation(x,y);
    }
    double stamp() const { return stamp_; }
    const gmrfw::CGMRF_map& geometry() const { return map_; }
    const WindSolveAudit& solveAudit() const { return audit_; }
    gmrfw::WindVector fieldAt(int i)
    {
        if(!healthy_ || stamp_<=0) throw std::runtime_error("GMRF_NO_CHECKED_SNAPSHOT");
        return map_.getEstimation(i);
    }
};
}
