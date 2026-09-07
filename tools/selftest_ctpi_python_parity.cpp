#include "CTPIOnlineCoreV2.hpp"
#include <iomanip>
#include <iostream>
#include <vector>

int main() {
    using namespace GSL::ctpi_v2;
    std::vector<unsigned char> free(3, 1);
    Transport transport(3, 1, 1.0, 0.1, free);
    std::vector<double> field(3, 0.0), u(3, 0.5), v(3, 0.0);
    std::cout << std::setprecision(17);
    transport.advance(field, u, v, 0.2, 0, 1.0);
    for (double value : field) std::cout << value << ' ';
    std::cout << '\n';
    transport.advance(field, u, v, 0.2, 0, 0.0);
    for (double value : field) std::cout << value << ' ';
    std::cout << '\n';
    return 0;
}
