#pragma once
// RAIOM-GSL-R: Graph Reduced-Order Transport Model (GRTOM-U) v2
// Fixes: matrix direction, Bresenham edges, solver reuse, logging

#include <Eigen/Sparse>
#include <Eigen/SparseLU>
#include <vector>
#include <cmath>
#include <algorithm>
#include <queue>
#include <chrono>
#include <cstdint>
#include <array>
#include <limits>
#include <functional>
#include "SNOEDPlanner.hpp"

namespace raiom {

struct TransportNode {
    int id;
    double cx, cy;
    double area;
    int grid_x;
    int grid_y;
};

struct TransportEdge {
    int from, to;
    double length;
    double dir_x, dir_y;
    double permeability;
};

struct PhysicsParams {
    double D = 0.5;        // diffusion rate
    double lam = 0.1;      // decay rate
    double Q_source = 1.0; // source emission
    double a_sensor = 0.0; // logistic intercept
    double b_sensor = 1.0; // logistic slope
};

struct SolverDiagnostics {
    bool success = false;
    double residual = 0.0;
    double runtime_ms = 0.0;
    int n_nodes = 0;
    int n_edges = 0;
    int n_negative = 0;
};

class TransportGraph {
public:
    std::vector<TransportNode> nodes;
    std::vector<TransportEdge> edges;
    int n_nodes = 0;
    int grid_nx = 0;
    int grid_ny = 0;
    double grid_origin_x = 0.0;
    double grid_origin_y = 0.0;
    double grid_cell_size = 1.0;
    std::vector<int8_t> occupancy;

    void buildFromGrid(const int8_t* grid, int nx, int ny,
                       double ox, double oy, double cs, int spacing = 5) {
        nodes.clear(); edges.clear(); occupancy.clear();
        grid_nx = nx; grid_ny = ny; grid_origin_x = ox; grid_origin_y = oy; grid_cell_size = cs;
        if (grid == nullptr || nx <= 0 || ny <= 0 || cs <= 0.0 || spacing <= 0) {
            n_nodes = 0;
            grid_nx = grid_ny = 0;
            return;
        }
        occupancy.assign(grid, grid + static_cast<std::size_t>(nx) * static_cast<std::size_t>(ny));
        std::vector<int> node_grid(nx * ny, -1);
        const auto gridIndex = [nx](int gx, int gy) { return gy * nx + gx; };

        // nav_msgs/OccupancyGrid is row-major: data[y * width + x].  The
        // previous implementation used x*height+y, silently transposing every
        // non-square map and rotating obstacle topology even on square maps.
        for (int gx = 0; gx < nx; gx += spacing) {
            for (int gy = 0; gy < ny; gy += spacing) {
                if (grid[gridIndex(gx, gy)] == 0) {
                    const int nid = static_cast<int>(nodes.size());
                    const double coarse = static_cast<double>(spacing) * cs;
                    nodes.push_back({nid, ox + (gx + 0.5) * cs, oy + (gy + 0.5) * cs,
                                     coarse * coarse, gx, gy});
                    node_grid[gridIndex(gx, gy)] = nid;
                }
            }
        }
        n_nodes = (int)nodes.size();

        // Build edges with full Bresenham raycasting
        const int ddx[] = {-1,-1,-1,0,0,1,1,1};
        const int ddy[] = {-1,0,1,-1,1,-1,0,1};
        for (int gi = 0; gi < nx; gi += spacing) {
            for (int gj = 0; gj < ny; gj += spacing) {
                const int idx = gridIndex(gi, gj);
                if (node_grid[idx] < 0) continue;
                const int from_id = node_grid[idx];
                for (int d = 0; d < 8; ++d) {
                    int ni = gi + ddx[d] * spacing;
                    int nj = gj + ddy[d] * spacing;
                    if (ni < 0 || ni >= nx || nj < 0 || nj >= ny) continue;
                    const int nidx = gridIndex(ni, nj);
                    if (node_grid[nidx] < 0) continue;
                    int to_id = node_grid[nidx];
                    if (to_id <= from_id) continue;

                    // Full Bresenham raycast — reject if ANY cell is occupied
                    bool blocked = false;
                    int steps = std::max(abs(ddx[d]*spacing), abs(ddy[d]*spacing));
                    for (int s = 0; s <= steps; ++s) {
                        int ci = gi + ddx[d] * s * spacing / std::max(steps, 1);
                        int cj = gj + ddy[d] * s * spacing / std::max(steps, 1);
                        if (ci >= 0 && ci < nx && cj >= 0 && cj < ny) {
                            if (grid[gridIndex(ci, cj)] == 1) { blocked = true; break; }
                        }
                    }
                    if (blocked) continue;

                    // Check corner-cutting for diagonal edges
                    if (ddx[d] != 0 && ddy[d] != 0) {
                        int mi1 = gi + ddx[d] * spacing;
                        int mj1 = gj;
                        int mi2 = gi;
                        int mj2 = gj + ddy[d] * spacing;
                        bool corner_blocked = false;
                        if (mi1 >= 0 && mi1 < nx && mj1 >= 0 && mj1 < ny)
                            if (grid[gridIndex(mi1, mj1)] == 1) corner_blocked = true;
                        if (mi2 >= 0 && mi2 < nx && mj2 >= 0 && mj2 < ny)
                            if (grid[gridIndex(mi2, mj2)] == 1) corner_blocked = true;
                        if (corner_blocked) continue;
                    }

                    double dx = ddx[d] * spacing * cs;
                    double dy = ddy[d] * spacing * cs;
                    double len = std::sqrt(dx*dx + dy*dy);
                    edges.push_back({from_id, to_id, len, dx/len, dy/len, 1.0});
                }
            }
        }
    }

    // Build Metzler matrix: correct direction
    // dc_i/dt = Σ_j k_ji * c_j - Σ_j k_ij * c_i - λ*c_i + Q*1[i=s]
    // A[j][i] = k_ji (flow FROM i TO j)
    // A[i][i] = -Σ_j k_ij - λ
    Eigen::SparseMatrix<double> buildMatrix(const PhysicsParams& params,
                                             double wind_x, double wind_y) const {
        Eigen::SparseMatrix<double> A(n_nodes, n_nodes);
        std::vector<Eigen::Triplet<double>> trips;

        for (const auto& e : edges) {
            int i = e.from, j = e.to;
            double L = std::max(e.length, 1e-6);

            // k_ij: flow from i to j
            double wind_dot_ij = wind_x * e.dir_x + wind_y * e.dir_y;
            double k_ij = e.permeability * (params.D/(L*L) + std::max(0.0, wind_dot_ij)/L);

            // k_ji: flow from j to i
            double wind_dot_ji = -wind_dot_ij;
            double k_ji = e.permeability * (params.D/(L*L) + std::max(0.0, wind_dot_ji)/L);

            // Off-diagonal: inflow
            trips.push_back({j, i, k_ij});  // k_ij flows INTO j FROM i → A[j][i]
            trips.push_back({i, j, k_ji});  // k_ji flows INTO i FROM j → A[i][j]

            // Diagonal: outflow
            trips.push_back({i, i, -k_ij});
            trips.push_back({j, j, -k_ji});
        }

        // Decay
        for (int i = 0; i < n_nodes; ++i)
            trips.push_back({i, i, -params.lam});

        A.setFromTriplets(trips.begin(), trips.end());
        return A;
    }

    // Solve steady state with diagnostics
    SolverDiagnostics solveSteadyState(const Eigen::SparseMatrix<double>& A,
                                        int source_node, double Q,
                                        std::vector<double>& result) const {
        SolverDiagnostics diag;
        diag.n_nodes = n_nodes;
        diag.n_edges = (int)edges.size();
        auto t0 = std::chrono::steady_clock::now();

        Eigen::VectorXd rhs = Eigen::VectorXd::Zero(n_nodes);
        rhs(source_node) = Q;

        Eigen::SparseMatrix<double> negA = -A;
        Eigen::SparseLU<Eigen::SparseMatrix<double>> solver;
        solver.analyzePattern(negA);
        solver.factorize(negA);

        if (solver.info() != Eigen::Success) {
            diag.success = false;
            return diag;
        }

        Eigen::VectorXd c = solver.solve(rhs);
        Eigen::VectorXd residual = negA * c - rhs;
        diag.residual = residual.norm() / (rhs.norm() + 1e-30);
        diag.success = (solver.info() == Eigen::Success) && std::isfinite(diag.residual) && (diag.residual < 1e-6);

        result.resize(n_nodes);
        diag.n_negative = 0;
        for (int i = 0; i < n_nodes; ++i) {
            result[i] = c(i);
            if (result[i] < -1e-10) diag.n_negative++;
            result[i] = std::max(0.0, result[i]);
        }

        auto t1 = std::chrono::steady_clock::now();
        diag.runtime_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
        return diag;
    }

    // GRTOM-C current-position batch: one M=-A factorization, all source RHS at once.
    // The corresponding action batch uses the adjoint M^T Z=H in the SNOED planner.
    SolverDiagnostics solveSteadyStateBatch(const Eigen::SparseMatrix<double>& A,
                                             const std::vector<int>& source_nodes,
                                             double Q, Eigen::MatrixXd& concentrations) const {
        SolverDiagnostics diag; diag.n_nodes = n_nodes; diag.n_edges = static_cast<int>(edges.size());
        const auto t0 = std::chrono::steady_clock::now();
        const Eigen::SparseMatrix<double> M = -A;
        Eigen::SparseLU<Eigen::SparseMatrix<double>> solver;
        solver.analyzePattern(M); solver.factorize(M);
        if (solver.info() != Eigen::Success) return diag;
        Eigen::MatrixXd rhs = Eigen::MatrixXd::Zero(n_nodes, static_cast<int>(source_nodes.size()));
        for (std::size_t k = 0; k < source_nodes.size(); ++k) rhs(source_nodes[k], static_cast<int>(k)) = Q;
        concentrations = solver.solve(rhs);
        const Eigen::MatrixXd residual = M * concentrations - rhs;
        diag.residual = residual.norm() / std::max(rhs.norm(), 1e-30);
        diag.success = solver.info() == Eigen::Success && diag.residual < 1e-8;
        diag.n_negative = static_cast<int>((concentrations.array() < -1e-10).count());
        const auto t1 = std::chrono::steady_clock::now();
        diag.runtime_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
        return diag;
    }

    // Exact transpose solve for one sensor query: c(sensor;s)=Q*z(source),
    // where M^T z=e_sensor. This replaces an unnecessarily dense all-source
    // forward RHS batch in the online posterior update without changing M,
    // source emission, or the observation transfer function.
    SolverDiagnostics solveSensorAdjoint(const Eigen::SparseMatrix<double>& A,
                                         int sensor_node,
                                         const std::vector<int>& source_nodes,
                                         double Q, std::vector<double>& concentrations) const {
        SolverDiagnostics diag; diag.n_nodes = n_nodes; diag.n_edges = static_cast<int>(edges.size());
        const auto t0 = std::chrono::steady_clock::now();
        const Eigen::SparseMatrix<double> M = -A;
        Eigen::SparseLU<Eigen::SparseMatrix<double>> solver;
        solver.analyzePattern(M.transpose()); solver.factorize(M.transpose());
        if (solver.info() != Eigen::Success) return diag;
        Eigen::VectorXd rhs = Eigen::VectorXd::Zero(n_nodes); rhs(sensor_node) = 1.0;
        const Eigen::VectorXd z = solver.solve(rhs);
        const Eigen::VectorXd residual = M.transpose() * z - rhs;
        diag.residual = residual.norm();
        if (solver.info() != Eigen::Success || !std::isfinite(diag.residual) || diag.residual >= 1e-8) return diag;
        concentrations.resize(source_nodes.size());
        diag.n_negative = 0;
        for (std::size_t k = 0; k < source_nodes.size(); ++k) {
            concentrations[k] = Q * z(source_nodes[k]);
            if (concentrations[k] < -1e-10) ++diag.n_negative;
            concentrations[k] = std::max(0.0, concentrations[k]);
        }
        diag.success = true;
        const auto t1 = std::chrono::steady_clock::now();
        diag.runtime_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
        return diag;
    }

    // Active GRTOM-C action provider. For a fixed map and source candidate
    // set it solves every source RHS in batch for the nominal wind and two
    // physical wind-coordinate perturbations. Queries at the proposed action
    // nodes then yield q[action][candidate][theta], dq/ds, and dq/dnu without
    // reading posterior scores, planner state, or source truth.
    SolverDiagnostics buildActionPredictionCube(
        const std::vector<std::array<double, 2>>& actions,
        const std::vector<int>& source_nodes,
        const PhysicsParams& params, double wind_x, double wind_y,
        ActionPredictionCube& cube, double spatial_step = 0.25,
        double nuisance_step = 0.05) const {
        SolverDiagnostics out; out.n_nodes = n_nodes; out.n_edges = static_cast<int>(edges.size());
        cube.q.assign(actions.size(), Eigen::MatrixXd());
        cube.dq_ds.assign(actions.size(), Eigen::MatrixXd());
        cube.dq_dnu.assign(actions.size(), Eigen::MatrixXd());
        if (actions.empty() || source_nodes.empty() || n_nodes <= 0) return out;
        const auto t0 = std::chrono::steady_clock::now();
        const int nc = static_cast<int>(source_nodes.size());
        std::array<Eigen::MatrixXd, 3> fields;
        // theta[1] is a shared log-amplitude perturbation; theta[2] is a
        // shared log-Peclet/transport perturbation (wind scale). Neither is
        // selected separately for an individual source hypothesis.
        std::array<PhysicsParams, 3> theta_params{{params, params, params}};
        theta_params[1].Q_source *= std::exp(nuisance_step);
        const double pe_scale = std::exp(nuisance_step);
        std::array<std::pair<double, double>, 3> theta{{
            {wind_x, wind_y}, {wind_x, wind_y}, {pe_scale * wind_x, pe_scale * wind_y}}};
        double worst_residual = 0.0;
        for (int t = 0; t < 3; ++t) {
            const Eigen::SparseMatrix<double> M = -buildMatrix(theta_params[t], theta[t].first, theta[t].second);
            Eigen::SparseLU<Eigen::SparseMatrix<double>> solver;
            solver.analyzePattern(M); solver.factorize(M);
            if (solver.info() != Eigen::Success) return out;
            Eigen::MatrixXd rhs = Eigen::MatrixXd::Zero(n_nodes, nc);
            for (int c = 0; c < nc; ++c) rhs(source_nodes[c], c) = theta_params[t].Q_source;
            fields[t] = solver.solve(rhs);
            const Eigen::MatrixXd residual = M * fields[t] - rhs;
            worst_residual = std::max(worst_residual, residual.norm() / std::max(rhs.norm(), 1e-30));
            if (solver.info() != Eigen::Success || !std::isfinite(worst_residual)) return out;
        }
        const auto qAt = [&](const Eigen::MatrixXd& field, double x, double y, int c) {
            const int node = nearestVisibleNode(x, y);
            if (node < 0) return 1e-6;
            const double log_c = std::log(std::max(0.0, field(node, c)) + 1e-6);
            const double logit = std::clamp(params.a_sensor + params.b_sensor * log_c, -500.0, 500.0);
            return std::clamp(1.0 / (1.0 + std::exp(-logit)), 1e-6, 1.0 - 1e-6);
        };
        for (std::size_t a = 0; a < actions.size(); ++a) {
            cube.q[a] = Eigen::MatrixXd::Zero(nc, 3);
            cube.dq_ds[a] = Eigen::MatrixXd::Zero(nc, 6);
            cube.dq_dnu[a] = Eigen::MatrixXd::Zero(nc, 2);
            for (int c = 0; c < nc; ++c) {
                for (int t = 0; t < 3; ++t) cube.q[a](c, t) = qAt(fields[t], actions[a][0], actions[a][1], c);
                for (int t = 0; t < 3; ++t) {
                    const double xp = qAt(fields[t], actions[a][0] + spatial_step, actions[a][1], c);
                    const double xm = qAt(fields[t], actions[a][0] - spatial_step, actions[a][1], c);
                    const double yp = qAt(fields[t], actions[a][0], actions[a][1] + spatial_step, c);
                    const double ym = qAt(fields[t], actions[a][0], actions[a][1] - spatial_step, c);
                    cube.dq_ds[a](c, 2 * t) = (xp - xm) / (2.0 * spatial_step);
                    cube.dq_ds[a](c, 2 * t + 1) = (yp - ym) / (2.0 * spatial_step);
                }
                cube.dq_dnu[a](c, 0) = (cube.q[a](c, 1) - cube.q[a](c, 0)) / nuisance_step;
                cube.dq_dnu[a](c, 1) = (cube.q[a](c, 2) - cube.q[a](c, 0)) / nuisance_step;
            }
        }
        out.success = worst_residual < 1e-8;
        out.residual = worst_residual;
        out.n_negative = 0;
        const auto t1 = std::chrono::steady_clock::now();
        out.runtime_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
        return out;
    }

    bool lineOfSightGrid(int x0, int y0, int x1, int y1) const {
        if (grid_nx <= 0 || grid_ny <= 0 || occupancy.empty()) return false;
        const auto inside = [&](int x, int y) {
            return x >= 0 && x < grid_nx && y >= 0 && y < grid_ny;
        };
        if (!inside(x0, y0) || !inside(x1, y1)) return false;
        int dx = std::abs(x1 - x0), sx = x0 < x1 ? 1 : -1;
        int dy = -std::abs(y1 - y0), sy = y0 < y1 ? 1 : -1;
        int error = dx + dy;
        while (true) {
            if (!inside(x0, y0) || occupancy[static_cast<std::size_t>(y0 * grid_nx + x0)] != 0) return false;
            if (x0 == x1 && y0 == y1) break;
            const int doubled = 2 * error;
            if (doubled >= dy) { error += dy; x0 += sx; }
            if (doubled <= dx) { error += dx; y0 += sy; }
        }
        return true;
    }

    int nearestVisibleNode(double wx, double wy) const {
        if (n_nodes <= 0) return -1;
        const int gx = static_cast<int>(std::floor((wx - grid_origin_x) / grid_cell_size));
        const int gy = static_cast<int>(std::floor((wy - grid_origin_y) / grid_cell_size));
        std::vector<std::pair<double, int>> order;
        order.reserve(nodes.size());
        for (const auto& node : nodes) {
            const double dx = node.cx - wx, dy = node.cy - wy;
            order.push_back({dx * dx + dy * dy, node.id});
        }
        std::stable_sort(order.begin(), order.end());
        for (const auto& [distance, id] : order) {
            (void)distance;
            const auto& node = nodes.at(static_cast<std::size_t>(id));
            if (lineOfSightGrid(gx, gy, node.grid_x, node.grid_y)) return id;
        }
        return order.front().second;
    }

    std::vector<int> shortestPathNodes(double start_x, double start_y,
                                       double goal_x, double goal_y) const {
        std::vector<int> empty;
        if (n_nodes <= 0) return empty;
        const int start = nearestVisibleNode(start_x, start_y);
        const int goal = nearestVisibleNode(goal_x, goal_y);
        if (start < 0 || goal < 0) return empty;
        if (start == goal) return {start};

        std::vector<std::vector<std::pair<int, double>>> adjacency(static_cast<std::size_t>(n_nodes));
        for (const auto& edge : edges) {
            adjacency[static_cast<std::size_t>(edge.from)].push_back({edge.to, edge.length});
            adjacency[static_cast<std::size_t>(edge.to)].push_back({edge.from, edge.length});
        }
        const double infinity = std::numeric_limits<double>::infinity();
        std::vector<double> distance(static_cast<std::size_t>(n_nodes), infinity);
        std::vector<int> previous(static_cast<std::size_t>(n_nodes), -1);
        using QueueItem = std::pair<double, int>;
        std::priority_queue<QueueItem, std::vector<QueueItem>, std::greater<QueueItem>> queue;
        distance[static_cast<std::size_t>(start)] = 0.0;
        queue.push({0.0, start});
        while (!queue.empty()) {
            const auto [current_distance, node] = queue.top();
            queue.pop();
            if (current_distance > distance[static_cast<std::size_t>(node)] + 1e-12) continue;
            if (node == goal) break;
            for (const auto& [neighbor, length] : adjacency[static_cast<std::size_t>(node)]) {
                const double candidate = current_distance + length;
                if (candidate + 1e-12 < distance[static_cast<std::size_t>(neighbor)]) {
                    distance[static_cast<std::size_t>(neighbor)] = candidate;
                    previous[static_cast<std::size_t>(neighbor)] = node;
                    queue.push({candidate, neighbor});
                }
            }
        }
        if (!std::isfinite(distance[static_cast<std::size_t>(goal)])) return empty;
        std::vector<int> path;
        for (int node = goal; node >= 0; node = previous[static_cast<std::size_t>(node)]) {
            path.push_back(node);
            if (node == start) break;
        }
        if (path.empty() || path.back() != start) return empty;
        std::reverse(path.begin(), path.end());
        return path;
    }

    double pathLength(const std::vector<int>& path) const {
        double total = 0.0;
        for (std::size_t k = 1; k < path.size(); ++k) {
            const auto& left = nodes.at(static_cast<std::size_t>(path[k - 1]));
            const auto& right = nodes.at(static_cast<std::size_t>(path[k]));
            total += std::hypot(right.cx - left.cx, right.cy - left.cy);
        }
        return total;
    }

    int nearestNode(double wx, double wy) const {
        if (n_nodes <= 0) return -1;
        int best = 0; double best_d = 1e18;
        for (int i = 0; i < n_nodes; ++i) {
            double d = (nodes[i].cx-wx)*(nodes[i].cx-wx) + (nodes[i].cy-wy)*(nodes[i].cy-wy);
            if (d < best_d) { best_d = d; best = i; }
        }
        return best;
    }

    // Connected components
    int countComponents() const {
        std::vector<bool> visited(n_nodes, false);
        int count = 0;
        for (int i = 0; i < n_nodes; ++i) {
            if (visited[i]) continue;
            count++;
            std::queue<int> q;
            q.push(i); visited[i] = true;
            while (!q.empty()) {
                int n = q.front(); q.pop();
                for (const auto& e : edges) {
                    int nb = (e.from == n) ? e.to : (e.to == n) ? e.from : -1;
                    if (nb >= 0 && !visited[nb]) { visited[nb] = true; q.push(nb); }
                }
            }
        }
        return count;
    }
};

inline double concentrationToQ(double conc, const PhysicsParams& params) {
    double log_c = std::log(conc + 1e-6);
    double logit = params.a_sensor + params.b_sensor * log_c;
    logit = std::max(-500.0, std::min(500.0, logit));
    double q = 1.0 / (1.0 + std::exp(-logit));
    return std::max(1e-6, std::min(1.0 - 1e-6, q));
}

} // namespace raiom
