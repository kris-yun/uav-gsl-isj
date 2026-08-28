#include "gaden/internal/MathUtils.hpp"
#include <cstdint>

namespace gaden { void ResetPrecalculatedGaussian(); }

// Exported bridge ensures the caller initializes the TLS engines in the same
// shared library that performs native transport draws.
extern "C" void gaden_initialize_random_engines(std::uint64_t seed)
{
    gaden::InitializeRandomEngines(seed);
    gaden::ResetPrecalculatedGaussian();
}
