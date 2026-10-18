#include "support.hpp"
namespace GSL::Utils {
static thread_local std::minstd_rand0 RNGengine;
    double lerp(double start, double end, double proportion)
    {
        if (proportion < 0 || std::isnan(proportion))
            return start;

        return start + (end - start) * std::min(1.0, proportion);
    }
    double clamp(double val, double min, double max)
    {
        return std::max(min, std::min(val, max));
    }
    double logOddsToProbability(double lo)
    {
        return 1.0 - 1.0 / (1 + std::exp(lo));
    }
    double randomFromGaussian(double mean, double stdev)
    {
        static thread_local std::normal_distribution<> dist{0, stdev};
        static thread_local double previousStdev = stdev;

        if (stdev != previousStdev)
        {
            dist = std::normal_distribution<>{0, stdev};
            previousStdev = stdev;
        }

        return mean + dist(RNGengine);
    }
    template <typename T> T uniformRandomT(T min, T max)
    {
        static thread_local std::uniform_real_distribution<T> distribution{0.0, 0.999};
        return min + distribution(RNGengine) * (max - min);
    }
    float uniformRandomF(float min, float max)
    {
        return uniformRandomT(min, max);
    }
    double uniformRandom(double min, double max)
    {
        return uniformRandomT(min, max);
    }
void restore_rng(const std::string&s){std::istringstream(s)>>RNGengine;}
std::string rng_state(){std::ostringstream s;s<<RNGengine;return s.str();}
}
