#pragma once
// Synchronous, wind-only producer. This is a conditional GMRF mean, NOT a
// calibrated joint transport posterior. Existing ROS backend is not modified.
#include <array>
#include <cstdint>
#include <stdexcept>
#include "gmrf_wind_core/gmrf_map.h"

namespace GSL::ctpi_v2
{
class GmrfWind
{
    gmrfw::CGMRF_map map_;
    double stamp_=0.;
    bool healthy_=true;
public:
    GmrfWind(const gmrfw::TOccupancyMap& occupancy,
             const gmrfw::CGMRF_map::Parameters& parameters)
        : map_(occupancy, parameters, false, false) {}

    void assimilate(double stamp, double x, double y, double u, double v)
    {
        if (!healthy_ || !std::isfinite(stamp) || std::abs(stamp-stamp_-.2)>1e-9 ||
            !std::isfinite(x) || !std::isfinite(y) || !std::isfinite(u) || !std::isfinite(v) ||
            !std::isfinite(std::hypot(u,v)))
            throw std::invalid_argument("CTPI_V2_WIND_SEQUENCE_OR_VALUE");
        // An unsuccessful solver cannot leave an apparently usable old snapshot.
        healthy_=false;
        if (!map_.insertObservation_GMRF(std::hypot(u,v), std::atan2(v,u), .001, .0001, x,y))
            throw std::runtime_error("CTPI_V2_GMRF_INSERT_REJECTED");
        map_.MAP_estimation_GMRF(1); // explicit completed update, same one-iteration backend rule
        const auto dims=map_.map_size();
        for(int i=0;i<dims.x()*dims.y();++i)
        {
            auto w=map_.getEstimation(i);
            if(!std::isfinite(w.x)||!std::isfinite(w.y))
                throw std::runtime_error("CTPI_V2_GMRF_NONFINITE_SNAPSHOT");
        }
        stamp_=stamp;
        healthy_=true;
    }

    gmrfw::WindVector predictAt(double nextStamp, double x, double y)
    {
        if(!healthy_ || stamp_<=0 || !std::isfinite(nextStamp) ||
           std::abs(nextStamp-stamp_-.2)>1e-9 || !std::isfinite(x)||!std::isfinite(y))
            throw std::invalid_argument("CTPI_V2_WIND_PREDICTION_NOT_READY");
        // Frozen current spatial mean is the explicitly chosen one-step forecast.
        // The target pose is supplied; no gas or target-time wind is used.
        return map_.getEstimation(x,y);
    }

    double stamp() const { return stamp_; }
    const gmrfw::CGMRF_map& geometry() const { return map_; }
    gmrfw::WindVector fieldAt(int i)
    {
        if(!healthy_ || stamp_<=0) throw std::runtime_error("CTPI_V2_NO_WIND_SNAPSHOT");
        return map_.getEstimation(i);
    }
};
}
