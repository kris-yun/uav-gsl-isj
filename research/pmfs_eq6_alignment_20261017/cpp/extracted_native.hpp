// Extracted source components. Minimal data containers replace ROS/grid storage only.
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#define ZoneScoped
#define GSL_ASSERT(x) do {if(!(x))throw std::runtime_error("native assertion");}while(0)
namespace GSL {
enum class Occupancy {Obstacle=0,Free=1};
struct HitProbability {double logOdds=0,omega=0,confidence=0;};
struct HitProbabilitySettings {double confidenceMeasurementWeight=1;};
template<class T> struct Grid2D {std::vector<T>data;std::vector<Occupancy>occupancy;};
namespace Utils {
double lerp(double start, double end, double proportion)
    {
        if (proportion < 0 || std::isnan(proportion))
            return start;

        return start + (end - start) * std::min(1.0, proportion);
    }
double evaluate1DGaussian(double distance, double sigma)
    {
        return exp(-0.5 * (std::pow(distance, 2) / std::pow(sigma, 2))) / (sigma * std::sqrt(2 * M_PI));
    }
double logOddsToProbability(double lo)
    {
        return 1.0 - 1.0 / (1 + std::exp(lo));
    }
}
namespace native {
void updateConfidence(HitProbability& cell, const HitProbabilitySettings& settings) {
    double exponent = -cell.omega / std::pow(settings.confidenceMeasurementWeight, 2);
    cell.confidence = 1 - std::exp(exponent);
}
}
namespace eq6 {
void updateConfidence(HitProbability& cell, const HitProbabilitySettings& settings) {
    double exponent = -(cell.omega * cell.omega) / std::pow(settings.confidenceMeasurementWeight, 2);
    cell.confidence = 1 - std::exp(exponent);
}
}
namespace PMFS_internal {
struct Simulations {struct Settings {double sourceDiscriminationPower=1;}settings;
double sourceProbFromMaps(const Grid2D<HitProbability>&,const std::vector<float>&)const;};
double Simulations::sourceProbFromMaps(const Grid2D<HitProbability>& measuredHitProb, const std::vector<float>& hitMap) const
    {
        ZoneScoped;
        double total = 1;
        for (int i = 0; i < measuredHitProb.data.size(); i++)
        {
            if (measuredHitProb.occupancy[i] != Occupancy::Free)
                continue;
            double measured = Utils::logOddsToProbability(measuredHitProb.data[i].logOdds);
            const double& simulated = hitMap[i];
            double val =
                Utils::lerp(1, (1 - std::abs(measured - simulated) * settings.sourceDiscriminationPower), measuredHitProb.data[i].confidence);
            total *= val;
            GSL_ASSERT(!std::isnan(total));
        }
        return total;
    }
}
}
