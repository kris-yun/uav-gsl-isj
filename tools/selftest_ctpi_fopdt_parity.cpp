#include "CTPIOnlineCoreV2.hpp"
#include <iomanip>
#include <iostream>
int main() {
    GSL::ctpi_v2::Fopdt sensor;
    double dt, input;
    std::cout << std::setprecision(17);
    while (std::cin >> dt >> input) std::cout << sensor.step(input, dt) << '\n';
}
