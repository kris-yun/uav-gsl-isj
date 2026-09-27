#include "FAMEV3Retrieval.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <numeric>

namespace GSL::FAMEV3 {
namespace { double clamp(double v) { return std::clamp(v, 1e-15, 1.0 - 1e-15); }
double kl(double p, double q) { p=clamp(p); q=clamp(q); return p*std::log(p/q)+(1-p)*std::log((1-p)/(1-q)); } }

std::vector<Mode> PosteriorModePartition::partition(const JointState& state,
        const std::vector<Candidate>& candidates, const std::vector<std::vector<std::size_t>>& adjacency) const {
    (void)candidates;
    const std::size_t n = candidates.size(); std::vector<double> pi(n, 0.0);
    for (std::size_t i=0; i<n; ++i) pi[i] = state.xi_m0[i] + state.xi_m1[i];
    std::vector<std::size_t> peak(n); for (std::size_t i=0;i<n;++i) peak[i]=i;
    for (std::size_t i=0;i<n;++i) for (std::size_t j: adjacency[i]) if (pi[j] > pi[peak[i]]) peak[i]=j;
    std::vector<int> root(n, -1); int next=0;
    for (std::size_t i=0;i<n;++i) { std::size_t p=i; while (peak[p] != p) p=peak[p]; if (root[p]<0) root[p]=next++; }
    std::vector<Mode> out(static_cast<std::size_t>(next)); for (int i=0;i<next;++i) out[i].id=i;
    for (std::size_t i=0;i<n;++i) { std::size_t p=i; while (peak[p] != p) p=peak[p]; out[static_cast<std::size_t>(root[p])].cells.push_back(i); }
    for (Mode& m:out) for (std::size_t i:m.cells) m.mass += pi[i];
    return out;
}

double PosteriorModePartition::modePredictive(const JointState& state, const PredictiveField& field,
                                              const Mode& mode) {
    double mass = 0.0, value = 0.0;
    for (const std::size_t i : mode.cells) {
        const double joint = state.xi_m0[i] + state.xi_m1[i];
        mass += joint;
        value += state.xi_m0[i] * field.q_m0 + state.xi_m1[i] * field.q_m1[i];
    }
    return clamp(value / std::max(mass, 1e-15));
}

double PosteriorModePartition::signedContrast(bool event, double q_alternative, double q_dominant) {
    q_alternative = clamp(q_alternative); q_dominant = clamp(q_dominant);
    return event ? std::log(q_alternative / q_dominant)
                 : std::log((1.0 - q_alternative) / (1.0 - q_dominant));
}

void HAEMQTree::append(std::size_t leaf_id, EvidenceEpisode episode) {
    if (leaf_id >= leaf_budget_) return;
    while (leaves_.size() <= leaf_id) leaves_.push_back(MemoryLeaf{static_cast<int>(leaves_.size()), {}, 0.0});
    leaves_[leaf_id].episodes.push_back(std::move(episode));
}

void HAEMQTree::recomputeDistortion(const JointState& state, const PredictiveField& field) {
    for (MemoryLeaf& leaf: leaves_) {
        if (leaf.episodes.empty()) { leaf.distortion=0.0; continue; }
        double d=0.0;
        for (const EvidenceEpisode& e:leaf.episodes) {
            const std::size_t n=std::min(e.predictive.size(), field.q_m1.size());
            for (std::size_t i=0;i<n;++i) d += (state.xi_m0[i]+state.xi_m1[i])*kl(e.predictive[i], field.q_m1[i]);
        }
        leaf.distortion=d/static_cast<double>(leaf.episodes.size());
    }
}

RetrievalResult CPHVQ::retrieve(const std::vector<MemoryLeaf>& leaves, const std::vector<Action>& actions,
                                std::size_t k, double full_best_utility) const {
    std::vector<std::pair<double,int>> ranked;
    for (const MemoryLeaf& leaf:leaves) { double best=-std::numeric_limits<double>::infinity(); for (const Action& a:actions) if (a.leaf_id==leaf.id) best=std::max(best,a.q_hv/a.duration); ranked.push_back({best,leaf.id}); }
    std::sort(ranked.begin(),ranked.end(),[](auto a,auto b){return a.first>b.first;});
    RetrievalResult out; const double target=0.95*full_best_utility;
    for (std::size_t take=0; take<ranked.size() && take<std::max<std::size_t>(1,k); ++take) out.leaves.push_back(ranked[take].second);
    auto collect=[&](){ for(const Action&a:actions) if(std::find(out.leaves.begin(),out.leaves.end(),a.leaf_id)!=out.leaves.end()) out.actions.push_back(a.id); };
    collect(); double best=-std::numeric_limits<double>::infinity(); for(const Action&a:actions) if(std::find(out.actions.begin(),out.actions.end(),a.id)!=out.actions.end()) best=std::max(best,a.risk_utility);
    while (best < target && out.leaves.size() < ranked.size()) { out.leaves.push_back(ranked[out.leaves.size()].second); out.actions.clear(); collect(); best=-std::numeric_limits<double>::infinity(); for(const Action&a:actions) if(std::find(out.actions.begin(),out.actions.end(),a.id)!=out.actions.end()) best=std::max(best,a.risk_utility); }
    out.risk_recall = full_best_utility > 0.0 ? best/full_best_utility : 1.0;
    return out;
}

double HypothesisVerificationQuery::score(const std::vector<double>& mode_mass,
                                           const std::vector<double>& mode_q,
                                           std::size_t dominant) {
    if (mode_mass.size() != mode_q.size() || mode_mass.empty() || dominant >= mode_mass.size()) return 0.0;
    double entropy = 0.0; for (double p : mode_mass) if (p > 0.0) entropy -= p * std::log(p);
    const double total = std::accumulate(mode_mass.begin(), mode_mass.end(), 0.0);
    const double safe_total = std::max(total, 1e-15);
    double mean_q = 0.0, conditional_entropy = 0.0;
    for (std::size_t j=0;j<mode_mass.size();++j) { const double p=mode_mass[j]/safe_total; mean_q += p*mode_q[j]; conditional_entropy += p * (-(clamp(mode_q[j])*std::log(clamp(mode_q[j])) + (1-clamp(mode_q[j]))*std::log(1-clamp(mode_q[j])))); }
    const double hmean = -(clamp(mean_q)*std::log(clamp(mean_q)) + (1-clamp(mean_q))*std::log(1-clamp(mean_q)));
    const double information = hmean - conditional_entropy;
    double falsification = 0.0; const double alt_mass = std::max(safe_total - mode_mass[dominant], 1e-15);
    for (std::size_t j=0;j<mode_mass.size();++j) if (j != dominant) falsification += (mode_mass[j]/alt_mass) * kl(mode_q[j], mode_q[dominant]);
    const double gamma = mode_mass.size() >= 2 ? std::clamp(1.0 - entropy/std::log(static_cast<double>(mode_mass.size())), 0.0, 1.0) : 0.0;
    return (1.0-gamma)*information + gamma*falsification;
}
}  // namespace GSL::FAMEV3
