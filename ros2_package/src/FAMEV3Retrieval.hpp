#pragma once

#include "FAMEV3Core.hpp"
#include <cstddef>
#include <vector>

namespace GSL::FAMEV3 {

struct Mode { int id = 0; std::vector<std::size_t> cells; double mass = 0.0; };
struct EvidenceEpisode { std::vector<double> predictive; bool event = false; int mode_id = 0; double signed_contrast = 0.0; };
struct MemoryLeaf { int id = 0; std::vector<EvidenceEpisode> episodes; double distortion = 0.0; };
struct Action { int id = 0; int leaf_id = 0; double duration = 1.0; double x = 0.0; double y = 0.0; double z = 0.0; double q_hv = 0.0; double predicted_delta_r = 0.0; double risk_utility = 0.0; };
struct RetrievalResult { std::vector<int> leaves; std::vector<int> actions; double risk_recall = 0.0; };

class PosteriorModePartition final {
public:
    std::vector<Mode> partition(const JointState& state, const std::vector<Candidate>& candidates,
                                const std::vector<std::vector<std::size_t>>& adjacency) const;
    static double modePredictive(const JointState&, const PredictiveField&, const Mode&);
    static double signedContrast(bool event, double q_alternative, double q_dominant);
};

class HAEMQTree final {
public:
    explicit HAEMQTree(std::size_t leaf_budget = 16) : leaf_budget_(leaf_budget) {}
    void append(std::size_t leaf_id, EvidenceEpisode episode);
    const std::vector<MemoryLeaf>& leaves() const noexcept { return leaves_; }
    void recomputeDistortion(const JointState& state, const PredictiveField& field);

private:
    std::size_t leaf_budget_;
    std::vector<MemoryLeaf> leaves_;
};

class CPHVQ final {
public:
    RetrievalResult retrieve(const std::vector<MemoryLeaf>& leaves, const std::vector<Action>& actions,
                             std::size_t k, double full_best_utility) const;
};

class HypothesisVerificationQuery final {
public:
    static double score(const std::vector<double>& mode_mass, const std::vector<double>& mode_q,
                        std::size_t dominant);
};

}  // namespace GSL::FAMEV3
