#include "gaden/internal/MathUtils.hpp"
#include <iomanip>
#include <iostream>
int main() {
    std::cout << std::setprecision(17);
    for (int i=0;i<16;++i) std::cout << gaden::uniformRandom(0.0f,1.0f) << " " << gaden::GaussianRandom(0.0f,1.0f) << "\n";
}
