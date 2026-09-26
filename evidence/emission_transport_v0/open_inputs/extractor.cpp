// rmfe_filament_extractor.cpp
// Faithful RMFE replica-bank extractor.
//
// For ONE candidate source we already have a GADEN filament simulation
// (preCalculateConcentrations=false -> compact iteration_*.dat files holding
// only active filaments).  This tool loads each requested iteration file with
// gaden_core's official PlaybackSimulation and evaluates the OFFICIAL gas
// concentration at every PMFS reduced (coarse) free-cell CENTER, using the
// exact same cutoff + line-of-sight math the simulator itself uses
// (Simulation::SampleConcentration).  Output:
//   <outNpy>    float32 npy, shape (nF, gx, gy), C-contiguous
//   <outMeta>   json with iters/gx/gy/coarse/coarse_cell/min_x/min_y/flight_z
//
// We deliberately link gaden_core instead of re-implementing the formula, so
// the bank values are byte-faithful to GADEN (no analytical Gaussian proxy).
//
// Usage:
//   rmfe_filament_extractor <rawDir> <envDir> <outNpy> <outMeta>
//        <min_x> <min_y> <cell> <coarse> <flight_z> <gx> <gy>
//        <iter0> <iter1> ... <iterN-1>

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>
#include <filesystem>

#include <gaden/PlaybackSimulation.hpp>
#include <gaden/EnvironmentConfiguration.hpp>

static void write_npy(const std::string& path, const std::vector<float>& data,
                      int nF, int gx, int gy) {
    std::string dict = "{'descr': '<f4', 'fortran_order': False, 'shape': (";
    dict += std::to_string(nF) + ", " + std::to_string(gx) + ", " +
            std::to_string(gy) + "), }";
    // pad so that (10 + header_len) is a multiple of 64
    size_t total_after_prefix = dict.size();
    size_t pad = (64 - ((10 + total_after_prefix) % 64)) % 64;
    dict.append(pad, ' ');

    uint8_t magic[8] = {0x93, 'N', 'U', 'M', 'P', 'Y', 1, 0};
    uint16_t hlen = static_cast<uint16_t>(dict.size());

    std::ofstream f(path, std::ios::binary);
    if (!f) {
        std::fprintf(stderr, "NPE_OPEN_FAIL %s\n", path.c_str());
        std::exit(4);
    }
    f.write(reinterpret_cast<char*>(magic), 8);
    f.write(reinterpret_cast<char*>(&hlen), 2);
    f.write(dict.data(), static_cast<std::streamsize>(dict.size()));
    f.write(reinterpret_cast<const char*>(data.data()),
            static_cast<std::streamsize>(data.size() * sizeof(float)));
    f.close();
}

int main(int argc, char** argv) {
    if (argc < 14) {
        std::fprintf(stderr,
            "USAGE: %s <rawDir> <envDir> <outNpy> <outMeta> "
            "<min_x> <min_y> <cell> <coarse> <flight_z> <gx> <gy> <iter0>..\n",
            argv[0]);
        return 2;
    }
    std::string rawDir = argv[1];
    std::string envDir = argv[2];
    std::string outNpy = argv[3];
    std::string outMeta = argv[4];
    float min_x = static_cast<float>(atof(argv[5]));
    float min_y = static_cast<float>(atof(argv[6]));
    float cell = static_cast<float>(atof(argv[7]));
    int coarse = atoi(argv[8]);
    float flight_z = static_cast<float>(atof(argv[9]));
    int gx = atoi(argv[10]);
    int gy = atoi(argv[11]);

    std::vector<int> iters;
    for (int i = 12; i < argc; i++) iters.push_back(atoi(argv[i]));
    int nF = static_cast<int>(iters.size());
    if (nF <= 0) {
        std::fprintf(stderr, "NO_ITERS\n");
        return 2;
    }

    auto config = gaden::EnvironmentConfiguration::ReadDirectory(envDir);
    if (!config) {
        std::fprintf(stderr, "ENV_READ_FAILED %s\n", envDir.c_str());
        return 3;
    }

    gaden::LoopConfig loop{false, 0, 0};
    gaden::PlaybackSimulation::Parameters params;
    params.startIteration = 0;
    params.resultsDirectory = rawDir;
    gaden::PlaybackSimulation sim(params, config, loop);

    float coarse_cell = static_cast<float>(coarse) * cell;
    std::vector<float> bank(static_cast<size_t>(nF) * gx * gy, 0.0f);

    for (int fi = 0; fi < nF; fi++) {
        int iter = iters[fi];
        bool ok = sim.LoadIteration(static_cast<size_t>(iter));
        if (!ok) {
            std::fprintf(stderr, "ITER_MISSING %d\n", iter);
            continue;
        }
        size_t base = static_cast<size_t>(fi) * gx * gy;
        // Each cell query is a read-only official SampleConcentration call
        // against the loaded PlaybackSimulation state.  Parallelize only
        // this independent spatial loop; frame loading and output ordering
        // remain serial, so the generated float32 bank is numerically
        // identical to the scalar extractor (apart from no reduction/order
        // operation being introduced).
#pragma omp parallel for collapse(2) schedule(static)
        for (int ix = 0; ix < gx; ix++) {
            for (int iy = 0; iy < gy; iy++) {
                float wx = min_x + (static_cast<float>(ix) + 0.5f) * coarse_cell;
                float wy = min_y + (static_cast<float>(iy) + 0.5f) * coarse_cell;
                float c = sim.SampleConcentration(
                    gaden::Vector3(wx, wy, flight_z));
                bank[base + static_cast<size_t>(ix) * gy + iy] = c;
            }
        }
        std::fprintf(stderr, "FRAME_DONE %d\n", iter);
        std::fflush(stderr);
    }

    write_npy(outNpy, bank, nF, gx, gy);

    {
        std::ofstream f(outMeta);
        f << "{\"iters\":[";
        for (int i = 0; i < nF; i++)
            f << (i ? "," : "") << iters[i];
        f << "],\"gx\":" << gx << ",\"gy\":" << gy << ",\"nF\":" << nF
          << ",\"coarse\":" << coarse << ",\"coarse_cell\":" << coarse_cell
          << ",\"min_x\":" << min_x << ",\"min_y\":" << min_y
          << ",\"flight_z\":" << flight_z << "}\n";
        f.close();
    }
    std::fprintf(stderr, "BANK_WRITTEN %s shape=(%d,%d,%d)\n", outNpy.c_str(),
                 nF, gx, gy);
    return 0;
}
