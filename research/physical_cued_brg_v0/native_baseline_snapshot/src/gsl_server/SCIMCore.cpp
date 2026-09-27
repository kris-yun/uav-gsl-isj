#include "SCIMCore.hpp"

#include <algorithm>
#include <numeric>
#include <stdexcept>

namespace GSL::SCIM {
namespace {

constexpr double kEps = OPGSLV3::kProbabilityEpsilon;

double clampProbability(double value) {
    return std::clamp(value, kEps, 1.0 - kEps);
}

double logSumExp(const std::vector<double>& values) {
    if (values.empty()) {
        return -std::numeric_limits<double>::infinity();
    }
    const double maximum = *std::max_element(values.begin(), values.end());
    if (!std::isfinite(maximum)) {
        return maximum;
    }
    double sum = 0.0;
    for (const double value : values) {
        sum += std::exp(value - maximum);
    }
    return maximum + std::log(sum);
}

}  // namespace

void DualPosterior::initialize(const OPGSLV3::GridSpec& spec,
                               std::vector<bool> valid_mask,
                               OPGSLV3::ObservationModelParameters model,
                               bool enable_ncl) {
    if (spec.nx <= 0 || spec.ny <= 0 || spec.nz <= 0 ||
        !(spec.x_max > spec.x_min) || !(spec.y_max > spec.y_min) ||
        (spec.nz > 1 && !(spec.z_max > spec.z_min))) {
        throw std::invalid_argument("SCIM invalid source grid");
    }
    model_ = model;
    spec_ = spec;
    dx_ = (spec.x_max - spec.x_min) / static_cast<double>(spec.nx);
    dy_ = (spec.y_max - spec.y_min) / static_cast<double>(spec.ny);
    dz_ = spec.nz > 1 ? (spec.z_max - spec.z_min) / static_cast<double>(spec.nz) : 0.0;
    const std::size_t full_size = static_cast<std::size_t>(spec.nx) *
                                  static_cast<std::size_t>(spec.ny) *
                                  static_cast<std::size_t>(spec.nz);
    if (valid_mask.empty()) {
        valid_mask.assign(full_size, true);
    }
    if (valid_mask.size() != full_size) {
        throw std::invalid_argument("SCIM source mask size mismatch");
    }
    sources_.clear();
    for (int i = 0; i < spec.nx; ++i) {
        for (int j = 0; j < spec.ny; ++j) {
            for (int k = 0; k < spec.nz; ++k) {
                const std::size_t index =
                    (static_cast<std::size_t>(i) * static_cast<std::size_t>(spec.ny) +
                     static_cast<std::size_t>(j)) * static_cast<std::size_t>(spec.nz) +
                    static_cast<std::size_t>(k);
                if (!valid_mask[index]) {
                    continue;
                }
                sources_.push_back({
                    spec.x_min + (static_cast<double>(i) + 0.5) * dx_,
                    spec.y_min + (static_cast<double>(j) + 0.5) * dy_,
                    spec.nz > 1 ? spec.z_min + (static_cast<double>(k) + 0.5) * dz_
                                : 0.5 * (spec.z_min + spec.z_max)});
            }
        }
    }
    if (sources_.empty()) {
        throw std::invalid_argument("SCIM source mask has no valid cells");
    }
    const double prior = -std::log(static_cast<double>(sources_.size()));
    log_map_.assign(sources_.size(), prior);
    log_conf_ = log_map_;
    ncl_enabled_ = enable_ncl;
    if (ncl_enabled_) {
        const std::size_t count = sources_.size() * ncl_alpha_.size() * ncl_beta_.size();
        ncl_log_joint_.assign(count, -std::log(static_cast<double>(count)));
    } else ncl_log_joint_.clear();
    refreshProbabilities();
    initialized_ = true;
}

double DualPosterior::predictiveHitProbability(
    const OPGSLV3::ObservationContext& observation) const {
    if (!initialized_) {
        throw std::logic_error("SCIM posterior is not initialized");
    }
    if (ncl_enabled_) {
        const auto g = nclG(observation); double result = 0.0;
        for (std::size_t s=0;s<sources_.size();++s) for (std::size_t a=0;a<ncl_alpha_.size();++a) for (std::size_t b=0;b<ncl_beta_.size();++b)
            result += std::exp(ncl_log_joint_[nclIndex(s,a,b)]) * nclProbability(s,a,b,g);
        return clampProbability(result);
    }
    double result = 0.0;
    // Compute per-candidate p_d if adaptive mode enabled
    std::vector<double> pd_vals(sources_.size(), 1.0);
    if (use_adaptive_pd) {
        std::vector<double> cx(sources_.size()), cy(sources_.size());
        for (std::size_t j = 0; j < sources_.size(); ++j) { cx[j] = sources_[j].x; cy[j] = sources_[j].y; }
        pd_estimator.compute(cx.data(), cy.data(), (int)sources_.size(), pd_vals.data());
    }
    for (std::size_t i = 0; i < sources_.size(); ++i) {
        result += map_p_[i] * OPGSLV3::ObservationModelEnsemble::hitProbability(
            model_, sources_[i], observation);
    }
    return clampProbability(result);
}

PosteriorDiagnostics DualPosterior::update(
    const OPGSLV3::ObservationContext& observation, bool detected, double omega) {
    if (!initialized_) {
        throw std::logic_error("SCIM posterior is not initialized");
    }
    PosteriorDiagnostics diagnostics;
    diagnostics.predictive_hit_probability = predictiveHitProbability(observation);
    diagnostics.map_entropy = mapSummary(0.90).entropy;
    diagnostics.confidence_entropy = confidenceSummary(0.90).entropy;
    diagnostics.omega = std::clamp(omega, 0.0, 1.0);
    if (ncl_enabled_) {
        const auto g=nclG(observation);
        for (std::size_t s=0;s<sources_.size();++s) for (std::size_t a=0;a<ncl_alpha_.size();++a) for (std::size_t b=0;b<ncl_beta_.size();++b) {
            const double q=nclProbability(s,a,b,g); ncl_log_joint_[nclIndex(s,a,b)] += detected?std::log(q):std::log1p(-q);
        }
        normalize(ncl_log_joint_); std::fill(log_map_.begin(),log_map_.end(),-std::numeric_limits<double>::infinity());
        for (std::size_t s=0;s<sources_.size();++s) { double p=0.0; for(std::size_t a=0;a<ncl_alpha_.size();++a) for(std::size_t b=0;b<ncl_beta_.size();++b) p+=std::exp(ncl_log_joint_[nclIndex(s,a,b)]); log_map_[s]=std::log(std::max(p,kEps)); }
        log_conf_=log_map_; refreshProbabilities(); diagnostics.map_entropy=mapSummary(0.90).entropy; diagnostics.confidence_entropy=diagnostics.map_entropy; return diagnostics;
    }
    for (std::size_t i = 0; i < sources_.size(); ++i) {
        const double q = (i < (int)precomputed_q.size()) ? precomputed_q[i] : clampProbability(
            OPGSLV3::ObservationModelEnsemble::hitProbability(model_, sources_[i], observation));
        const double ell = detected ? std::log(q) : (use_adaptive_pd ? pd_vals[i] : miss_weight) * std::log1p(-q);
        log_map_[i] += ell;
        log_conf_[i] += diagnostics.omega * ell;
    }
    normalize(log_map_);
    normalize(log_conf_);
    refreshProbabilities();
    diagnostics.map_entropy = mapSummary(0.90).entropy;
    diagnostics.confidence_entropy = confidenceSummary(0.90).entropy;
    return diagnostics;
}

void DualPosterior::normalize(std::vector<double>& log_values) {
    const double normalizer = logSumExp(log_values);
    if (!std::isfinite(normalizer)) {
        throw std::runtime_error("SCIM posterior normalization failed");
    }
    for (double& value : log_values) {
        value -= normalizer;
    }
}

std::vector<double> DualPosterior::probabilities(
    const std::vector<double>& log_values) {
    std::vector<double> result(log_values.size(), 0.0);
    for (std::size_t i = 0; i < log_values.size(); ++i) {
        result[i] = std::exp(log_values[i]);
    }
    return result;
}

void DualPosterior::refreshProbabilities() {
    map_p_ = probabilities(log_map_);
    confidence_p_ = probabilities(log_conf_);
}

std::size_t DualPosterior::nclIndex(std::size_t s,std::size_t a,std::size_t b) const { return (s*ncl_alpha_.size()+a)*ncl_beta_.size()+b; }
std::vector<double> DualPosterior::nclG(const OPGSLV3::ObservationContext& o) const { std::vector<double> g(sources_.size()),d(sources_.size()); double mu=0.0; for(std::size_t s=0;s<sources_.size();++s){const auto&x=sources_[s];const double dx=o.sensor_x-x.x,dy=o.sensor_y-x.y,dz=o.sensor_z-x.z;d[s]=std::sqrt(dx*dx+dy*dy+dz*dz);mu+=map_p_[s]*d[s];}double v=0.0;for(std::size_t s=0;s<sources_.size();++s)v+=map_p_[s]*(d[s]-mu)*(d[s]-mu);const double sd=std::sqrt(std::max(0.0,v));for(std::size_t s=0;s<sources_.size();++s)g[s]=(mu-d[s])/(sd+kEps);return g; }
double DualPosterior::nclProbability(std::size_t s,std::size_t a,std::size_t b,const std::vector<double>&g) const { return clampProbability(1.0/(1.0+std::exp(-(ncl_alpha_[a]+ncl_beta_[b]*g[s])))); }

OPGSLV3::SourcePoint DualPosterior::sourceAtValidIndex(std::size_t index) const {
    if (index >= sources_.size()) {
        throw std::out_of_range("SCIM source index out of range");
    }
    return sources_[index];
}

OPGSLV3::PosteriorSummary DualPosterior::mapSummary(double credible_mass) const {
    return summarize(map_p_, credible_mass);
}

OPGSLV3::PosteriorSummary DualPosterior::confidenceSummary(double credible_mass) const {
    return summarize(confidence_p_, credible_mass);
}

OPGSLV3::PosteriorSummary DualPosterior::summarize(
    const std::vector<double>& probabilities, double credible_mass) const {
    if (!(credible_mass > 0.0 && credible_mass < 1.0)) {
        throw std::invalid_argument("SCIM credible mass must lie in (0,1)");
    }
    OPGSLV3::PosteriorSummary result;
    result.credible_mass = credible_mass;
    result.valid_source_count = sources_.size();
    std::size_t map_index = 0;
    double max_probability = -1.0;
    std::vector<std::pair<double, double>> radius_mass;
    radius_mass.reserve(sources_.size());
    for (std::size_t i = 0; i < sources_.size(); ++i) {
        const auto& source = sources_[i];
        const double p = probabilities[i];
        result.mean.x += p * source.x;
        result.mean.y += p * source.y;
        result.mean.z += p * source.z;
        if (p > 0.0) {
            result.entropy -= p * std::log(p);
        }
        if (p > max_probability) {
            max_probability = p;
            map_index = i;
        }
    }
    result.map = sources_[map_index];
    result.map_probability = max_probability;
    double sum_sq = 0.0;
    for (std::size_t i = 0; i < sources_.size(); ++i) {
        const auto& source = sources_[i];
        const double dx = source.x - result.mean.x;
        const double dy = source.y - result.mean.y;
        const double dz = source.z - result.mean.z;
        const double radius = std::sqrt(dx * dx + dy * dy + dz * dz);
        result.variance += probabilities[i] * radius * radius;
        sum_sq += probabilities[i] * probabilities[i];
        radius_mass.emplace_back(radius, probabilities[i]);
    }
    result.effective_source_cells = sum_sq > 0.0 ? 1.0 / sum_sq : 0.0;
    std::sort(radius_mass.begin(), radius_mass.end());
    double cumulative = 0.0;
    for (const auto& item : radius_mass) {
        cumulative += item.second;
        if (cumulative >= credible_mass) {
            result.credible_radius = item.first;
            break;
        }
    }
    result.model_marginal = {1.0};
    return result;
}

void SpatialInformationPlanner::initialize(double x_min, double x_max,
                                           double y_min, double y_max,
                                           double cell_size,
                                           std::size_t min_history,
                                           std::size_t candidate_cap) {
    if (!(x_max > x_min && y_max > y_min && std::isfinite(cell_size) && cell_size > 0.0)) {
        throw std::invalid_argument("SCIM invalid spatial memory bounds");
    }
    x_min_ = x_min; x_max_ = x_max; y_min_ = y_min; y_max_ = y_max;
    cell_size_ = cell_size;
    min_history_ = std::max<std::size_t>(2, min_history);
    candidate_cap_ = std::max<std::size_t>(2, candidate_cap);
    effective_hits_ = 0.0;
    spatial_memory_inactive_ = false;
    cells_.clear();
}

std::int64_t SpatialInformationPlanner::key(double x, double y) const {
    const auto ix = static_cast<std::int64_t>(std::floor((x - x_min_) / cell_size_));
    const auto iy = static_cast<std::int64_t>(std::floor((y - y_min_) / cell_size_));
    return (ix << 32) ^ (iy & 0xffffffffLL);
}

SpatialInformationPlanner::Cell& SpatialInformationPlanner::getOrCreate(double x, double y) {
    const auto cell_id = key(x, y);
    auto [it, inserted] = cells_.try_emplace(cell_id);
    if (inserted) {
        it->second.state.cell_id = cell_id;
    }
    return it->second;
}

double SpatialInformationPlanner::integratedAutocorrelation(
    const std::deque<double>& values) {
    if (values.size() < 2) {
        return 1.0;
    }
    const double mean = std::accumulate(values.begin(), values.end(), 0.0) /
                        static_cast<double>(values.size());
    double variance = 0.0;
    for (const double value : values) {
        variance += (value - mean) * (value - mean);
    }
    if (!(variance > 1e-15)) {
        return 1.0;
    }
    double tau = 1.0;
    for (std::size_t lag = 1; lag < values.size(); ++lag) {
        double covariance = 0.0;
        for (std::size_t i = lag; i < values.size(); ++i) {
            covariance += (values[i] - mean) * (values[i - lag] - mean);
        }
        const double rho = covariance / variance;
        if (!(rho > 0.0)) {
            break;
        }
        tau += 2.0 * rho;
    }
    return std::max(1.0, tau);
}

double SpatialInformationPlanner::omegaAt(double x, double y) const {
    const auto it = cells_.find(key(x, y));
    if (it == cells_.end() || it->second.contrast_sequence.size() < min_history_) {
        return 1.0;
    }
    return std::clamp(1.0 / it->second.state.contrast_iact, 0.0, 1.0);
}

MemoryCellSnapshot SpatialInformationPlanner::snapshotAt(double x, double y) const {
    const auto it = cells_.find(key(x, y));
    if (it == cells_.end()) {
        MemoryCellSnapshot result;
        result.cell_id = key(x, y);
        result.correlation_estimable = false;
        return result;
    }
    return it->second.state;
}

std::vector<MemoryCellSnapshot> SpatialInformationPlanner::snapshots() const {
    std::vector<MemoryCellSnapshot> result;
    result.reserve(cells_.size());
    for (const auto& item : cells_) {
        result.push_back(item.second.state);
    }
    return result;
}

double SpatialInformationPlanner::jsDivergence(double q_i, double q_j) {
    q_i = clampProbability(q_i);
    q_j = clampProbability(q_j);
    const double m = 0.5 * (q_i + q_j);
    const auto kl = [m](double q) {
        return q * std::log(q / m) + (1.0 - q) * std::log((1.0 - q) / (1.0 - m));
    };
    return std::clamp(0.5 * (kl(q_i) + kl(q_j)), 0.0, OPGSLV3::kLogTwo);
}

double SpatialInformationPlanner::safeLog1pRatio(double numerator, double denominator) {
    return std::log1p(std::max(0.0, numerator) / (1.0 + std::max(0.0, denominator)));
}

double SpatialInformationPlanner::discrimination(
    const OPGSLV3::ObservationContext& action,
    const DualPosterior& posterior,
    const OPGSLV3::ObservationModelParameters& model) const {
    const auto& probabilities = posterior.mapProbabilities();
    std::vector<std::size_t> order(probabilities.size());
    std::iota(order.begin(), order.end(), 0U);
    std::stable_sort(order.begin(), order.end(), [&probabilities](auto lhs, auto rhs) {
        return probabilities[lhs] > probabilities[rhs];
    });
    double mass = 0.0;
    if (order.size() > candidate_cap_) {
        order.resize(candidate_cap_);
    }
    std::vector<double> q;
    std::vector<double> weights;
    for (const auto index : order) {
        q.push_back(clampProbability(OPGSLV3::ObservationModelEnsemble::hitProbability(
            model, posterior.sourceAtValidIndex(index), action)));
        weights.push_back(probabilities[index]);
        mass += probabilities[index];
        if (mass >= 0.90 && q.size() >= 2) break;
    }
    double pair_weight = 0.0;
    double pair_sum = 0.0;
    for (std::size_t i = 0; i < q.size(); ++i) {
        for (std::size_t j = i + 1; j < q.size(); ++j) {
            const double weight = weights[i] * weights[j];
            pair_weight += weight;
            pair_sum += weight * jsDivergence(q[i], q[j]);
        }
    }
    return pair_weight > 0.0 ? pair_sum / pair_weight : 0.0;
}

void SpatialInformationPlanner::recordExecuted(
    const OPGSLV3::ObservationContext& action, bool detected,
    double discrimination_value, double sim_time) {
    Cell& cell = getOrCreate(action.sensor_x, action.sensor_y);
    const double prior_omega = omegaAt(action.sensor_x, action.sensor_y);
    cell.contrast_sequence.push_back(discrimination_value);
    if (cell.contrast_sequence.size() > 32) {
        cell.contrast_sequence.pop_front();
    }
    cell.state.visit_episodes += 1;
    cell.state.last_visit_time = sim_time;
    cell.state.contrast_iact = integratedAutocorrelation(cell.contrast_sequence);
    cell.state.correlation_estimable = cell.contrast_sequence.size() >= min_history_;
    cell.state.omega = cell.state.correlation_estimable
        ? std::clamp(1.0 / cell.state.contrast_iact, 0.0, 1.0) : 1.0;
    cell.state.accumulated_discrimination += prior_omega * discrimination_value;
    cell.state.acquisition_exposure += prior_omega;
    effective_hits_ += prior_omega * (detected ? 1.0 : 0.0);
}

PlannerDecision SpatialInformationPlanner::choose(
    const std::vector<OPGSLV3::FeasibleAction>& actions,
    double current_x, double current_y, double current_z,
    const OPGSLV3::ObservationContext& current_context,
    const DualPosterior& posterior,
    const OPGSLV3::ObservationModelParameters& model,
    double horizontal_speed_mps, double vertical_speed_mps,
    double measurement_dwell_seconds) const {
    PlannerDecision decision;
    decision.effective_hits = effective_hits_;
    decision.mode = effective_hits_ < 1.0 ? "acquisition" : "localization";
    const auto& probabilities = posterior.mapProbabilities();
    std::vector<std::size_t> order(probabilities.size());
    std::iota(order.begin(), order.end(), 0U);
    std::stable_sort(order.begin(), order.end(), [&probabilities](auto lhs, auto rhs) {
        return probabilities[lhs] > probabilities[rhs];
    });
    if (order.size() > candidate_cap_) order.resize(candidate_cap_);
    double selected_mass = 0.0;
    std::vector<std::size_t> candidates;
    for (const auto index : order) {
        candidates.push_back(index);
        selected_mass += probabilities[index];
        if (selected_mass >= 0.90 && candidates.size() >= 2) break;
    }
    for (const auto& action : actions) {
        ActionScore score;
        score.action = action;
        score.target_cell = key(action.x, action.y);
        const auto memory = snapshotAt(action.x, action.y);
        score.j_cell = memory.accumulated_discrimination;
        score.a_cell = memory.acquisition_exposure;
        score.omega_cell = memory.correlation_estimable ? memory.omega : 1.0;
        score.cycle_time = std::hypot(action.x - current_x, action.y - current_y) /
            std::max(horizontal_speed_mps, 1e-6) +
            std::abs(action.z - current_z) / std::max(vertical_speed_mps, 1e-6) +
            measurement_dwell_seconds;
        OPGSLV3::ObservationContext context = current_context;
        context.sensor_x = action.x; context.sensor_y = action.y; context.sensor_z = action.z;
        double pair_weight = 0.0;
        double pair_sum = 0.0;
        double qbar = 0.0;
        std::vector<double> qs;
        for (const auto index : candidates) {
            const double q = clampProbability(OPGSLV3::ObservationModelEnsemble::hitProbability(
                model, posterior.sourceAtValidIndex(index), context));
            qs.push_back(q);
            qbar += probabilities[index] * q;
        }
        for (std::size_t i = 0; i < candidates.size(); ++i) {
            for (std::size_t j = i + 1; j < candidates.size(); ++j) {
                const double weight = probabilities[candidates[i]] * probabilities[candidates[j]];
                pair_weight += weight;
                pair_sum += weight * jsDivergence(qs[i], qs[j]);
            }
        }
        score.qbar = clampProbability(qbar);
        score.discrimination = pair_weight > 0.0 ? pair_sum / pair_weight : 0.0;
        score.delta_a = safeLog1pRatio(score.qbar, score.a_cell);
        score.delta_i = safeLog1pRatio(score.discrimination, score.j_cell);
        const double numerator = effective_hits_ < 1.0 ? score.delta_a : score.delta_i;
        score.utility = score.cycle_time > 0.0 ? numerator / score.cycle_time : 0.0;
        decision.ranked.push_back(score);
    }
    std::stable_sort(decision.ranked.begin(), decision.ranked.end(),
        [](const ActionScore& lhs, const ActionScore& rhs) {
            if (std::abs(lhs.utility - rhs.utility) > 1e-12) return lhs.utility > rhs.utility;
            if (lhs.action.visit_count != rhs.action.visit_count) return lhs.action.visit_count < rhs.action.visit_count;
            return lhs.cycle_time < rhs.cycle_time;
        });
    if (!decision.ranked.empty()) {
        decision.selected = decision.ranked.front();
        decision.selected->selected = true;
        decision.reason = "scim_spatial_contrast_memory";
        std::size_t unique_cells = 0;
        std::int64_t last_cell = std::numeric_limits<std::int64_t>::min();
        for (const auto& score : decision.ranked) {
            if (score.target_cell != last_cell) { ++unique_cells; last_cell = score.target_cell; }
        }
        decision.spatial_memory_active = unique_cells >= 2;
        decision.spatial_contrast_active = false;
        for (std::size_t i = 1; i < decision.ranked.size(); ++i) {
            if (std::abs(decision.ranked[i].discrimination - decision.ranked[0].discrimination) > 1e-10) {
                decision.spatial_contrast_active = true; break;
            }
        }
        // A merged single-cell memory is an explicit engineering failure even
        // when the instantaneous JS contrast is nonzero: it cannot represent
        // spatial exposure or revisit state.
        decision.inactive_warning = !decision.spatial_memory_active ||
                                    !decision.spatial_contrast_active;
        if (decision.inactive_warning) {
            spatial_memory_inactive_ = true;
            decision.reason = "PLANNER_SPATIAL_MEMORY_INACTIVE";
        }
    }
    return decision;
}

double SpatialInformationPlanner::actionDifferenceRate(
    const PlannerDecision& baseline, const PlannerDecision& candidate) const {
    if (!baseline.selected.has_value() || !candidate.selected.has_value()) return 0.0;
    return baseline.selected->target_cell == candidate.selected->target_cell ? 0.0 : 1.0;
}

}  // namespace GSL::SCIM
