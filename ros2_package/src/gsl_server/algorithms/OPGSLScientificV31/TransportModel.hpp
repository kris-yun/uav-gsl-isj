#pragma once
// RAIOM-GSL Module A: Graph Reduced-Order Transport Model (GRTOM-U)
//
// Builds a free-space graph from occupancy grid, constructs Metzler
// transport matrix with diffusion + advection, solves for steady-state
// concentration, and computes candidate-specific detection probabilities.
//
// dc/dt = A_θ(w)·c + Q·e_s
// c^∞ = -A^{-1} · Q·e_s
// q_s(a) = σ(a + b·log(h_a^T · c^∞_s + ε))

#include <Eigen/Sparse>
#include <Eigen/SparseLU>
#include <vector>
#include <cmath>
#include <algorithm>
#include <queue>

namespace raiom {

struct TransportNode {
    int id;
    double cx, cy;  // world center
    double area;
};

struct TransportEdge {
    int from, to;
    double length;
    double dir_x, dir_y;  // unit direction from->to
    double permeability;  // 0=wall, 1=open
};

struct PhysicsParams {
    double D = 0.5;        // diffusion rate
    double lambda = 0.1;   // decay rate
    double Q_source = 1.0; // source emission
    double a_sensor = 0.0; // logistic intercept
    double b_sensor = 1.0; // logistic slope
};

class TransportGraph {
public:
    std::vector<TransportNode> nodes;
    std::vector<TransportEdge> edges;
    int n_nodes = 0;

    void buildFromGrid(const int8_t* grid, int nx, int ny,
                       double ox, double oy, double cs, int spacing = 5) {
        nodes.clear();
        edges.clear();

        // Place nodes at regular grid points in free space
        std::vector<int> node_grid(nx * ny, -1);
        for (int gi = 0; gi < nx; gi += spacing) {
            for (int gj = 0; gj < ny; gj += spacing) {
                if (grid[gi * ny + gj] == 0) {  // free space
                    int nid = (int)nodes.size();
                    TransportNode nd;
                    nd.id = nid;
                    nd.cx = ox + (gi + 0.5) * cs;
                    nd.cy = oy + (gj + 0.5) * cs;
                    nd.area = cs * cs;
                    nodes.push_back(nd);
                    node_grid[gi * ny + gj] = nid;
                }
            }
        }
        n_nodes = (int)nodes.size();

        // Build edges (8-connectivity)
        const int ddx[] = {-1,-1,-1,0,0,1,1,1};
        const int ddy[] = {-1,0,1,-1,1,-1,0,1};
        for (int gi = 0; gi < nx; gi += spacing) {
            for (int gj = 0; gj < ny; gj += spacing) {
                int idx = gi * ny + gj;
                if (node_grid[idx] < 0) continue;
                int from_id = node_grid[idx];

                for (int d = 0; d < 8; ++d) {
                    int ni = gi + ddx[d] * spacing;
                    int nj = gj + ddy[d] * spacing;
                    if (ni < 0 || ni >= nx || nj < 0 || nj >= ny) continue;
                    int nidx = ni * ny + nj;
                    if (node_grid[nidx] < 0) continue;
                    int to_id = node_grid[nidx];
                    if (to_id <= from_id) continue; // avoid duplicates

                    // Check path is free (simple: check midpoint)
                    int mi = gi + ddx[d] * spacing / 2;
                    int mj = gj + ddy[d] * spacing / 2;
                    if (mi >= 0 && mi < nx && mj >= 0 && mj < ny) {
                        if (grid[mi * ny + mj] == 1) continue; // wall blocks
                    }

                    TransportEdge edge;
                    edge.from = from_id;
                    edge.to = to_id;
                    double dx = ddx[d] * spacing * cs;
                    double dy = ddy[d] * spacing * cs;
                    edge.length = std::sqrt(dx*dx + dy*dy);
                    edge.dir_x = dx / std::max(edge.length, 1e-10);
                    edge.dir_y = dy / std::max(edge.length, 1e-10);
                    edge.permeability = 1.0;
                    edges.push_back(edge);
                }
            }
        }
    }

    // Build Metzler matrix A for transport equation
    Eigen::SparseMatrix<double> buildMatrix(const PhysicsParams& params,
                                             double wind_x, double wind_y) const {
        Eigen::SparseMatrix<double> A(n_nodes, n_nodes);
        std::vector<Eigen::Triplet<double>> triplets;

        for (const auto& e : edges) {
            int i = e.from, j = e.to;
            double L = std::max(e.length, 1e-6);

            // k_ij = tau * [D/L² + (w·e_ij)+ / L]
            double wind_dot = wind_x * e.dir_x + wind_y * e.dir_y;
            double adv = std::max(0.0, wind_dot) / L;
            double diff = params.D / (L * L);
            double k_ij = e.permeability * (diff + adv);

            // Reverse direction
            double wind_dot_rev = -wind_dot;
            double adv_rev = std::max(0.0, wind_dot_rev) / L;
            double k_ji = e.permeability * (diff + adv_rev);

            // Off-diagonal: flow into node
            triplets.push_back({i, j, k_ij});
            triplets.push_back({j, i, k_ji});

            // Diagonal: outflow
            triplets.push_back({i, i, -k_ij});
            triplets.push_back({j, j, -k_ji});
        }

        // Decay on diagonal
        for (int i = 0; i < n_nodes; ++i) {
            triplets.push_back({i, i, -params.lambda});
        }

        A.setFromTriplets(triplets.begin(), triplets.end());
        return A;
    }

    // Solve steady state: c^∞ = -A^{-1} · Q·e_s
    std::vector<double> solveSteadyState(const Eigen::SparseMatrix<double>& A,
                                          int source_node, double Q) const {
        Eigen::VectorXd rhs = Eigen::VectorXd::Zero(n_nodes);
        rhs(source_node) = Q;

        // Solve -A · c = rhs (A is negative definite, so -A is positive definite)
        Eigen::SparseMatrix<double> negA = -A;
        Eigen::SparseLU<Eigen::SparseMatrix<double>> solver;
        solver.analyzePattern(negA);
        solver.factorize(negA);
        Eigen::VectorXd c = solver.solve(rhs);

        // Clip negative values
        std::vector<double> result(n_nodes);
        for (int i = 0; i < n_nodes; ++i) {
            result[i] = std::max(0.0, c(i));
        }
        return result;
    }

    // Find nearest node to a world position
    int nearestNode(double wx, double wy) const {
        int best = 0;
        double best_dist = 1e18;
        for (int i = 0; i < n_nodes; ++i) {
            double d = (nodes[i].cx - wx) * (nodes[i].cx - wx) +
                       (nodes[i].cy - wy) * (nodes[i].cy - wy);
            if (d < best_dist) { best_dist = d; best = i; }
        }
        return best;
    }
};

// Detection probability from concentration
inline double concentrationToQ(double conc, const PhysicsParams& params) {
    double log_c = std::log(conc + 1e-6);
    double logit = params.a_sensor + params.b_sensor * log_c;
    logit = std::max(-500.0, std::min(500.0, logit));
    double q = 1.0 / (1.0 + std::exp(-logit));
    return std::max(1e-6, std::min(1.0 - 1e-6, q));
}

} // namespace raiom
