#pragma once
// BAPR and HSPB module functions - shared between PMFS.cpp and PMFS_utils.cpp
#include <vector>
#include <deque>
#include <cmath>
#include <algorithm>
#include <gsl_server/algorithms/Common/Occupancy.hpp>
#include <gsl_server/algorithms/Common/Grid2D.hpp>
#include <gsl_server/algorithms/PMFS/internal/Settings.hpp>

namespace GSL
{
    inline std::vector<double> computeBoundaryDistanceField(
        const std::vector<Occupancy>& occ, const Grid2DMetadata& meta, int maxDist)
    {
        const int W = meta.dimensions.x;
        const int H = meta.dimensions.y;
        std::vector<double> dist(W * H, (double)maxDist);
        std::deque<std::pair<int,int>> queue;

        for (int j = 0; j < H; j++) {
            for (int i = 0; i < W; i++) {
                int idx = j * W + i;
                if (occ[idx] == Occupancy::Free) {
                    bool adj_wall = false;
                    for (int dj = -1; dj <= 1 && !adj_wall; dj++)
                        for (int di = -1; di <= 1 && !adj_wall; di++) {
                            if (di == 0 && dj == 0) continue;
                            int ni = i + di, nj = j + dj;
                            if (ni < 0 || ni >= W || nj < 0 || nj >= H) { adj_wall = true; continue; }
                            if (occ[nj * W + ni] != Occupancy::Free) adj_wall = true;
                        }
                    if (adj_wall) { dist[idx] = 0.0; queue.push_back({i, j}); }
                }
            }
        }

        const int dx4[] = {1, -1, 0, 0};
        const int dy4[] = {0, 0, 1, -1};
        while (!queue.empty()) {
            auto [cx, cy] = queue.front(); queue.pop_front();
            int cidx = cy * W + cx;
            for (int k = 0; k < 4; k++) {
                int nx = cx + dx4[k], ny = cy + dy4[k];
                if (nx < 0 || nx >= W || ny < 0 || ny >= H) continue;
                int nidx = ny * W + nx;
                if (occ[nidx] != Occupancy::Free) continue;
                double nd = dist[cidx] + 1.0;
                if (nd < dist[nidx]) { dist[nidx] = nd; queue.push_back({nx, ny}); }
            }
        }
        return dist;
    }

    inline void applyBAPR(std::vector<double>& sourceProb,
                          const std::vector<Occupancy>& occ,
                          const Grid2DMetadata& meta,
                          const PMFS_internal::SimulationSettings& simSettings,
                          std::vector<double>& distField,
                          bool& dtfComputed)
    {
        if (!simSettings.bapr_enabled) return;
        if (!dtfComputed) {
            distField = computeBoundaryDistanceField(occ, meta, simSettings.bapr_dtf_radius);
            dtfComputed = true;
        }
        const double steepness = simSettings.bapr_sigmoid_steepness;
        const double threshold = simSettings.bapr_wall_distance;
        const double exponent_scale = simSettings.bapr_wall_penalty;
        double total = 0.0;
        for (size_t i = 0; i < sourceProb.size(); i++) {
            if (occ[i] != Occupancy::Free) continue;
            double d = distField[i];
            double w = 1.0 / (1.0 + std::exp(-steepness * (d - threshold)));
            sourceProb[i] *= std::pow(w, exponent_scale);
            total += sourceProb[i];
        }
        if (total > 0.0)
            for (size_t i = 0; i < sourceProb.size(); i++)
                if (occ[i] == Occupancy::Free) sourceProb[i] /= total;
    }
}
