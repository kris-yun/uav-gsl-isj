#include <gaden/Environment.hpp>

#include <filesystem>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>

int main(int argc, char** argv)
{
    if (argc != 2) {
        std::cerr << "usage: gaden_native_occupancy_query OccupancyGrid3D.csv\n";
        return 2;
    }
    gaden::Environment environment;
    const auto status = environment.ReadFromFile(std::filesystem::path(argv[1]));
    if (status == gaden::ReadResult::NO_FILE || status == gaden::ReadResult::READING_FAILED) {
        std::cerr << "native occupancy load failed\n";
        return 3;
    }
    std::cout << std::setprecision(17);
    std::string line;
    while (std::getline(std::cin, line)) {
        if (line.empty()) continue;
        std::istringstream input(line);
        double x = 0.0, y = 0.0, z = 0.0;
        if (!(input >> x >> y >> z)) {
            std::cout << "ERR parse\n" << std::flush;
            continue;
        }
        const gaden::Vector3 point(static_cast<float>(x), static_cast<float>(y), static_cast<float>(z));
        const gaden::Vector3i index = environment.coordsToIndices(point);
        const auto state = environment.at(point);
        std::cout << "OK " << static_cast<int>(state) << ' '
                  << index.x << ' ' << index.y << ' ' << index.z << '\n' << std::flush;
    }
    return 0;
}
