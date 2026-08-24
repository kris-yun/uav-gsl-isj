#pragma once
// Geodesic distance via Dijkstra on occupancy grid.
// Replaces Euclidean distance for wall-aware observation model.

#include <vector>
#include <queue>
#include <limits>
#include <cmath>
#include <cstdint>

namespace opgsl_geo {

struct GridConfig {
    int nx = 0, ny = 0;
    double origin_x = 0.0, origin_y = 0.0;
    double cell_size = 0.1;
};

class GeodesicDistanceMap {
public:
    void setGrid(const std::vector<int8_t>& grid, const GridConfig& cfg) {
        grid_ = grid; config_ = cfg;
        cs_ = cfg.cell_size; diag_ = cs_ * std::sqrt(2.0);
    }

    bool computeFromSensor(double sx, double sy) {
        int gx = int(std::floor((sx - config_.origin_x) / cs_));
        int gy = int(std::floor((sy - config_.origin_y) / cs_));
        if (gx < 0 || gx >= config_.nx || gy < 0 || gy >= config_.ny) return false;
        if (grid_[gx * config_.ny + gy] == 1) return false;

        const int N = config_.nx * config_.ny;
        dist_.assign(N, 1e18);
        dist_[gx * config_.ny + gy] = 0.0;

        const int ddx[] = {-1,-1,-1,0,0,1,1,1};
        const int ddy[] = {-1,0,1,-1,1,-1,0,1};
        const double ed[] = {diag_,cs_,diag_,cs_,cs_,diag_,cs_,diag_};

        using E = std::pair<double,int>;
        std::priority_queue<E, std::vector<E>, std::greater<E>> h;
        h.push({0.0, gx * config_.ny + gy});

        while (!h.empty()) {
            auto [d, idx] = h.top(); h.pop();
            if (d > dist_[idx]) continue;
            int cx = idx / config_.ny, cy = idx % config_.ny;
            for (int i = 0; i < 8; ++i) {
                int nx = cx + ddx[i], ny = cy + ddy[i];
                if (nx < 0 || nx >= config_.nx || ny < 0 || ny >= config_.ny) continue;
                int ni = nx * config_.ny + ny;
                if (grid_[ni] == 1) continue;
                double nd = d + ed[i];
                if (nd < dist_[ni]) { dist_[ni] = nd; h.push({nd, ni}); }
            }
        }
        return true;
    }

    double getDistance(double tx, double ty) const {
        int gx = int(std::floor((tx - config_.origin_x) / cs_));
        int gy = int(std::floor((ty - config_.origin_y) / cs_));
        if (gx < 0 || gx >= config_.nx || gy < 0 || gy >= config_.ny) return 1e18;
        return dist_[gx * config_.ny + gy];
    }

    bool isInitialized() const { return !dist_.empty(); }

private:
    std::vector<int8_t> grid_;
    std::vector<double> dist_;
    GridConfig config_;
    double cs_ = 0.1, diag_ = 0.141421356;
};

} // namespace opgsl_geo
