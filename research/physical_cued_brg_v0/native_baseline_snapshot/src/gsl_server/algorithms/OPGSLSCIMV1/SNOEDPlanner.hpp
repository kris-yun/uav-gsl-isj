#pragma once
#include <Eigen/Dense>
#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <vector>

namespace raiom {
struct ActionPredictionCube {
    // q[action][candidate][theta], Jacobians in x/y and nu1/nu2.
    std::vector<Eigen::MatrixXd> q, dq_ds, dq_dnu;
};
struct SNOEDDiagnostics { double gamma=0., nominal=0., residual=0., condition=0.; int rank=0; };
struct BundleDiagnostics { double utility=0., gamma=0., expected_cycle_seconds=0.; int candidate_count=0; };
class SparseNuisanceOrthogonalPlanner {
public:
    static SNOEDDiagnostics score(const Eigen::Vector3d& u, const Eigen::Matrix<double,3,2>& V) {
        SNOEDDiagnostics out; out.nominal=u.squaredNorm();
        const Eigen::JacobiSVD<Eigen::Matrix<double,3,2>> svd(V,Eigen::ComputeFullU|Eigen::ComputeFullV);
        const auto s=svd.singularValues(); const double tol=1e-10*std::max(1.0,s.size()?s(0):0.0);
        out.rank=static_cast<int>((s.array()>tol).count());
        out.condition=(out.rank>1)?s(0)/s(out.rank-1):std::numeric_limits<double>::infinity();
        Eigen::Vector3d projected=Eigen::Vector3d::Zero();
        if(out.rank) projected=svd.matrixU().leftCols(out.rank)*svd.matrixU().leftCols(out.rank).transpose()*u;
        out.residual=(u-projected).norm(); out.gamma=(u-projected).squaredNorm(); return out;
    }
    static double directionalInformation(double q, const Eigen::Vector2d& dqds, const Eigen::Vector2d& direction) {
        const double d=std::max(1e-12,q*(1.-q)); return direction.dot(dqds)/std::sqrt(d);
    }
    // The ordered FOPDT recursion is evaluated once for every candidate and
    // action in the bundle. It is intentionally independent of ground truth.
    static double fopdtAdvance(double state, double target, double dt,
                               double tau_seconds, double dead_time_seconds) {
        const double effective_dt = std::max(0.0, dt - dead_time_seconds);
        const double alpha = 1.0 - std::exp(-effective_dt / std::max(1e-6, tau_seconds));
        return state + alpha * (target - state);
    }
    static BundleDiagnostics scoreOrderedBundle(const ActionPredictionCube& cube,
                                                const std::array<int, 3>& actions,
                                                const Eigen::VectorXd& weights,
                                                const std::array<double, 3>& cycle_seconds,
                                                double tau_seconds, double dead_time_seconds) {
        BundleDiagnostics out;
        if (cube.q.empty() || weights.size() == 0) return out;
        const int nc = static_cast<int>(weights.size());
        Eigen::Vector3d mean = Eigen::Vector3d::Zero();
        for (int r = 0; r < 3; ++r) {
            const int a = actions[r];
            if (a < 0 || a >= static_cast<int>(cube.q.size()) || cube.q[a].rows() != nc) return out;
            mean(r) = weights.dot(cube.q[a].col(0));
            out.expected_cycle_seconds += cycle_seconds[r];
        }
        double aggregate = 0.0;
        for (int c = 0; c < nc; ++c) {
            Eigen::Vector3d u = Eigen::Vector3d::Zero();
            Eigen::Matrix<double,3,2> V = Eigen::Matrix<double,3,2>::Zero();
            double state = 0.0;
            double mean_state = 0.0;
            for (int r = 0; r < 3; ++r) {
                const int a = actions[r];
                state = fopdtAdvance(state, cube.q[a](c, 0), cycle_seconds[r], tau_seconds, dead_time_seconds);
                mean_state = fopdtAdvance(mean_state, mean(r), cycle_seconds[r], tau_seconds, dead_time_seconds);
                u(r) = state - mean_state;
                if (cube.dq_dnu[a].rows() == nc && cube.dq_dnu[a].cols() >= 2) {
                    V(r, 0) = cube.dq_dnu[a](c, 0);
                    V(r, 1) = cube.dq_dnu[a](c, 1);
                }
            }
            aggregate += std::max(0.0, weights(c)) * score(u, V).gamma;
        }
        out.gamma = aggregate;
        out.utility = aggregate / std::max(1e-6, out.expected_cycle_seconds);
        out.candidate_count = nc;
        return out;
    }
    static double coupledKL(const Eigen::MatrixXd& q, const Eigen::VectorXd& weights) {
        if (q.rows() != weights.size() || q.cols() == 0) return 0.0;
        double aggregate = 0.0;
        for (int i = 0; i < q.rows(); ++i) for (int j = i + 1; j < q.rows(); ++j) {
            double worst = std::numeric_limits<double>::infinity();
            for (int t = 0; t < q.cols(); ++t) {
                const double p = std::clamp(q(i, t), 1e-9, 1.0 - 1e-9);
                const double r = std::clamp(q(j, t), 1e-9, 1.0 - 1e-9);
                worst = std::min(worst, p * std::log(p / r) + (1.0 - p) * std::log((1.0 - p) / (1.0 - r)));
            }
            aggregate += 2.0 * std::max(0.0, weights(i)) * std::max(0.0, weights(j)) * worst;
        }
        return std::max(0.0, aggregate);
    }
    static double nominalFisher(const Eigen::MatrixXd& q, const Eigen::MatrixXd& dqds,
                                const Eigen::VectorXd& weights) {
        if (q.rows() != weights.size() || dqds.rows() != weights.size() || dqds.cols() < 2) return 0.0;
        double information = 0.0;
        for (int c = 0; c < q.rows(); ++c) {
            const double variance = std::max(1e-12, q(c, 0) * (1.0 - q(c, 0)));
            information += std::max(0.0, weights(c)) * dqds.row(c).head<2>().squaredNorm() / variance;
        }
        return information;
    }
};
} // namespace raiom
