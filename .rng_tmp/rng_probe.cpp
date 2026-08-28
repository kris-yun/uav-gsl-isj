#include "gaden/internal/MathUtils.hpp"
#include <iomanip>
#include <iostream>
int main(int argc, char** argv) {
    if (argc > 1) gaden::InitializeRandomEngines(static_cast<std::uint64_t>(std::stoull(argv[1])));
    std::cout << std::setprecision(17);
    for (int i=0;i<16;++i) std::cout << gaden::uniformRandom(0.0f,1.0f) << " " << gaden::GaussianRandom(0.0f,1.0f) << "\n";
}
