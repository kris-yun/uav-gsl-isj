#include "gsl_server/algorithms/Common/Utils/RosUtils.hpp"
#include "gsl_server/core/Logging.hpp"
#include "gsl_server/core/Navigation.hpp"
#include "gsl_server/core/Profiling.hpp"
#include "gsl_server/core/VectorsImpl/vmath_DDACustomVec.hpp"
#include <algorithm>
#include <angles/angles.h>
#include <gsl_server/algorithms/Common/Grid2D.hpp>
#include <gsl_server/algorithms/Common/Utils/Math.hpp>
#include <gsl_server/algorithms/PMFS/MovingStatePMFS.hpp>
#include <gsl_server/algorithms/PMFS/PMFS.hpp>
#include <gsl_server/algorithms/PMFS/internal/HitProbability.hpp>
#include <numeric>
#include <limits>
#include <iomanip>
#include <std_msgs/msg/detail/color_rgba__struct.hpp>

namespace GSL
{
    MovingStatePMFS::MovingStatePMFS(Algorithm* _algorithm)
        : MovingState(_algorithm)
    {
        pmfs = dynamic_cast<PMFS*>(_algorithm);

        publishers.explorationValue = pmfs->node->create_publisher<Marker>("explorationValue", 1);
        publishers.varianceHit = pmfs->node->create_publisher<Marker>("varianceHit", 1);
        publishers.movementSets = pmfs->node->create_publisher<Marker>("movementSets", 1);
    }

    void MovingStatePMFS::chooseGoalAndMove()
    {
        // ScopedStopwatch watch("movement");

        if (movesCounter > pmfs->settings.movement.initialExplorationMoves)
            currentMovement = MovingStatePMFS::MovementType::Search;
        else
            currentMovement = MovingStatePMFS::MovementType::Exploration;

        auto& gridMetadata = pmfs->gridMetadata;

        // Add nearby cells to the open set
        {
            int i = pmfs->gridMetadata.coordinatesToIndices(pmfs->currentRobotPose.pose.pose).x;
            int j = pmfs->gridMetadata.coordinatesToIndices(pmfs->currentRobotPose.pose.pose).y;

            int openMoveSetExpasion = pmfs->settings.movement.openMoveSetExpasion;
            int oC = std::max(0, i - openMoveSetExpasion);
            int fC = std::min((int)gridMetadata.dimensions.x - 1, i + openMoveSetExpasion);
            int oR = std::max(0, j - openMoveSetExpasion);
            int fR = std::min((int)gridMetadata.dimensions.y - 1, j + openMoveSetExpasion);

            for (int col = oC; col <= fC; col++)
            {
                for (int row = oR; row <= fR; row++)
                {
                    Vector2Int p(col, row);
                    if (closedMoveSet.find(p) == closedMoveSet.end() && pmfs->visibilityMap->isVisible({i, j}, p) == Visibility::Visible)
                        openMoveSet.insert(p);
                }
            }
        }

        // remove this cell from the open set
        openMoveSet.erase(pmfs->gridMetadata.coordinatesToIndices(pmfs->currentRobotPose.pose.pose));

        // Find the cell with the highest estimated information value
        //------------------------------------------------------
        calculateMutualInformationGas();
        NavigateToPose::Goal goal;

        // We have a small random chance of using the explorationValue instead of the proper information value even in the second phase
        // because it is beneficial to have at least some measurements spanning a large area of the map
        float explorationC = Utils::uniformRandom(0, 1);

        struct PositionEval
        {
            Vector2Int indices;
            double evaluation;
        };

        auto compareEval = [](const PositionEval& a, const PositionEval& b)
        {
            if (a.evaluation != b.evaluation)
                return a.evaluation > b.evaluation;
            if (a.indices.x != b.indices.x)
                return a.indices.x < b.indices.x;
            return a.indices.y < b.indices.y;
        };
        std::set<PositionEval, decltype(compareEval)> evaluations;
        std::set<PositionEval, decltype(compareEval)> nativeEvaluations;

        double maxPosterior = 0.0;
        double posteriorSqSum = 0.0;
        size_t freeCellCount = 0;
        if ((pmfs->tadmEnabled && pmfs->posteriorGuidanceWeight > 0.0) || pmfs->cpirEnabled)
        {
            for (size_t i = 0; i < pmfs->sourceProbability.size(); ++i)
            {
                if (pmfs->occupancy[i] != Occupancy::Free)
                    continue;
                const double p = pmfs->sourceProbability[i];
                if (std::isfinite(p) && p >= 0.0)
                {
                    maxPosterior = std::max(maxPosterior, p);
                    posteriorSqSum += p * p;
                }
                ++freeCellCount;
            }
        }
        // Do not let a diffuse or stale posterior erase PMFS information gain.
        // The gate is based on absolute concentration relative to the uniform
        // prior and effective sample size; it is not a guidance-weight sweep.
        const double posteriorESS = posteriorSqSum > 0.0 ? 1.0 / posteriorSqSum : 0.0;
        const bool posteriorTrusted = freeCellCount > 0 &&
                                      std::isfinite(maxPosterior) &&
                                      maxPosterior > 2.0 / static_cast<double>(freeCellCount) &&
                                      posteriorESS < 0.5 * static_cast<double>(freeCellCount);
        const double effectiveGuidanceWeight = posteriorTrusted
                                                   ? std::min(pmfs->posteriorGuidanceWeight, 0.25)
                                                   : 0.0;

        for (size_t i = 0; i < pmfs->sourceProbability.size(); i++)
        {
            if (pmfs->occupancy[i] != Occupancy::Free)
                continue;
            Vector2Int indices = gridMetadata.indices2D(i);
            double explorationTerm = explorationValue(indices.x, indices.y);

            double interest = currentMovement == MovementType::Exploration || explorationC < pmfs->settings.movement.explorationProbability
                                  ? explorationTerm
                                  : informationValue(indices.x, indices.y);

            const double nativeInterest = interest;
            double guidedInterest = nativeInterest;

            // PFDI's posterior must reach the controller.  Keep the frozen
            // baseline unchanged when the weight is zero; for the protected
            // path, blend normalized posterior mass into the existing PMFS
            // information score rather than adding a new stopping rule.
            if (effectiveGuidanceWeight > 0.0 && maxPosterior > 0.0)
            {
                const double posteriorMass = pmfs->sourceProbability[i] / maxPosterior;
                // Keep PMFS information/exploration utility in its native
                // units.  Posterior guidance is a bounded relative
                // modulation, not a convex replacement by a unit-scaled
                // posterior peak (which erased exploration on transfer
                // Houses).  The factor is clipped positive for finite mass.
                const double modulation = std::max(0.25, 1.0 + effectiveGuidanceWeight * (posteriorMass - 1.0));
                guidedInterest *= modulation;
            }

            // this is to include the navigation distance in the evaluation
            const double navigationCost = std::pow(pmfs->hitProbability[i].distanceFromRobot + 0.1f, pmfs->settings.movement.distanceWeight);
            const double nativeEvaluation = nativeInterest / navigationCost;
            const double evaluation = guidedInterest / navigationCost;

            // Use the navigation-cost-adjusted score that was computed above.
            // Inserting `interest` here silently discarded distanceWeight and
            // made the controller chase posterior peaks irrespective of cost.
            nativeEvaluations.insert({.indices = indices, .evaluation = nativeEvaluation});
            evaluations.insert({.indices = indices, .evaluation = evaluation});
        }

        NavigateToPose::Goal nativeGoal;
        NavigateToPose::Goal guidedGoal;
        bool nativeGoalFound = false;
        bool guidedGoalFound = false;
        for (const PositionEval& eval : nativeEvaluations)
        {
            NavigateToPose::Goal tempGoal = indexToGoal(eval.indices.x, eval.indices.y);
            if (checkGoal(tempGoal))
            {
                nativeGoal = tempGoal;
                nativeGoalFound = true;
                break;
            }
        }
        for (const PositionEval& eval : evaluations)
        {
            NavigateToPose::Goal tempGoal = indexToGoal(eval.indices.x, eval.indices.y);
            if (checkGoal(tempGoal))
            {
                guidedGoal = tempGoal;
                guidedGoalFound = true;
                break;
            }
        }

        // CTPI M3 fast-track: use the existing PMFS open-move set as the
        // action domain, then re-rank those actions by posterior-weighted
        // predictive information. F10 uses raw finite-8 reachability and F11
        // uses the frozen TSDC committor. No localization truth enters here.
        if (pmfs->ctpiPlannerEnabled)
        {
            std::vector<Vector2Int> ctpiIndices;
            std::vector<size_t> ctpiCells;
            std::vector<double> ctpiTravel;
            for (const auto& indices : openMoveSet)
            {
                if (!gridMetadata.indicesInBounds(indices))
                    continue;
                const size_t nativeCell = gridMetadata.indexOf(indices);
                if (pmfs->occupancy[nativeCell] != Occupancy::Free)
                    continue;
                const double travel = pmfs->hitProbability[nativeCell].distanceFromRobot;
                if (!(std::isfinite(travel) && travel >= 0.0))
                    continue;
                ctpiIndices.push_back(indices);
                ctpiCells.push_back(nativeCell);
                ctpiTravel.push_back(travel);
            }
            // Always include the native PMFS goal in the M3 action domain.
            // This makes the action Gate exact: M3 can only replace the native
            // action when its predicted information is at least as large.
            size_t nativeCandidate = std::numeric_limits<size_t>::max();
            if (nativeGoalFound)
            {
                const Vector2Int nativeIndices = gridMetadata.coordinatesToIndices(nativeGoal.pose.pose);
                if (gridMetadata.indicesInBounds(nativeIndices))
                {
                    const size_t nativeCell = gridMetadata.indexOf(nativeIndices);
                    auto existing = std::find(ctpiCells.begin(), ctpiCells.end(), nativeCell);
                    if (existing == ctpiCells.end())
                    {
                        if (pmfs->occupancy[nativeCell] == Occupancy::Free)
                        {
                            nativeCandidate = ctpiCells.size();
                            ctpiIndices.push_back(nativeIndices);
                            ctpiCells.push_back(nativeCell);
                            ctpiTravel.push_back(pmfs->hitProbability[nativeCell].distanceFromRobot);
                        }
                    }
                    else
                        nativeCandidate = static_cast<size_t>(std::distance(ctpiCells.begin(), existing));
                }
            }
            if (ctpiCells.empty())
                throw std::runtime_error("CTPI_M3_EMPTY_ACTION_SET");
            const auto ctpiScores = pmfs->evaluateCTPIActionInformation(ctpiCells, ctpiTravel);
            std::vector<size_t> order(ctpiCells.size());
            std::iota(order.begin(), order.end(), 0);
            std::stable_sort(order.begin(), order.end(), [&](size_t left, size_t right)
            {
                const double sl = ctpiScores[left];
                const double sr = ctpiScores[right];
                if (std::abs(sl - sr) > 1.0e-12)
                    return sl > sr;
                if (std::abs(ctpiTravel[left] - ctpiTravel[right]) > 1.0e-12)
                    return ctpiTravel[left] < ctpiTravel[right];
                if (ctpiIndices[left].x != ctpiIndices[right].x)
                    return ctpiIndices[left].x < ctpiIndices[right].x;
                return ctpiIndices[left].y < ctpiIndices[right].y;
            });
            bool found = false;
            size_t chosen = 0;
            NavigateToPose::Goal ctpiGoal;
            for (const size_t candidate : order)
            {
                if (!std::isfinite(ctpiScores[candidate]))
                    continue;
                NavigateToPose::Goal tempGoal = indexToGoal(ctpiIndices[candidate].x, ctpiIndices[candidate].y);
                if (checkGoal(tempGoal))
                {
                    ctpiGoal = tempGoal;
                    chosen = candidate;
                    found = true;
                    break;
                }
            }
            if (!found)
                throw std::runtime_error("CTPI_M3_NO_REACHABLE_INFORMATION_ACTION");
            goal = ctpiGoal;
            ++pmfs->ctpiActionDecisionId;
            const double simTime = (pmfs->node->now() - pmfs->startTime).seconds();
            const int travelSamples = static_cast<int>(std::ceil(
                ctpiTravel[chosen] / pmfs->ctpiHorizontalSpeedMps / 0.2));
            const int predictionStart = pmfs->cpirLastTimeIndex + 1 + travelSamples;
            if (pmfs->ctpiM3Audit)
            {
                const double nativeInfo = nativeCandidate < ctpiScores.size()
                    ? ctpiScores[nativeCandidate]
                    : std::numeric_limits<double>::quiet_NaN();
                const bool changed = nativeGoalFound &&
                    (std::hypot(goal.pose.pose.position.x - nativeGoal.pose.pose.position.x,
                                goal.pose.pose.position.y - nativeGoal.pose.pose.position.y) > 1.0e-9);
                pmfs->ctpiM3Audit << pmfs->ctpiActionDecisionId << ',' << std::setprecision(17) << simTime << ','
                    << pmfs->pfdiMode << ',' << pmfs->ctpiDecisionSensorStatePpm << ',' << ctpiCells.size() << ','
                    << (nativeGoalFound ? nativeGoal.pose.pose.position.x : std::numeric_limits<double>::quiet_NaN()) << ','
                    << (nativeGoalFound ? nativeGoal.pose.pose.position.y : std::numeric_limits<double>::quiet_NaN()) << ','
                    << nativeInfo << ',' << goal.pose.pose.position.x << ',' << goal.pose.pose.position.y << ','
                    << ctpiScores[chosen] << ',' << ctpiTravel[chosen] << ',' << predictionStart << ',' << (changed ? 1 : 0) << '\n';
                pmfs->ctpiM3Audit.flush();
            }
            GSL_INFO("CTPI M3 {} decision {}: candidates={}, info={:.6f}, travel={:.3f}, sensor_state={:.6f}",
                     pmfs->pfdiMode, pmfs->ctpiActionDecisionId, ctpiCells.size(), ctpiScores[chosen],
                     ctpiTravel[chosen], pmfs->ctpiDecisionSensorStatePpm);
        }

        // Active-perception safety contract: posterior guidance may change a
        // goal only when it reduces posterior-expected source distance versus
        // the native information-gain goal.  This is truth-blind and keeps a
        // stale/overconfident likelihood from steering the UAV away from its
        // own information policy.
        if (!pmfs->ctpiPlannerEnabled)
            goal = nativeGoalFound ? nativeGoal : guidedGoal;
        // G2-M1 v2b: M1 load-bearing source-seeking.  In search phase
        // (after warmup) with a trusted posterior, track the posterior MAP
        // inside the open move set so the Gaussian-plume posterior actually
        // steers the UAV toward the inferred source.  Warmup keeps native
        // PMFS exploration.
        if (pmfs->cpirEnabled && !pmfs->ctpiPlannerEnabled &&
            currentMovement == MovementType::Search && posteriorTrusted)
        {
            size_t bestCell = std::numeric_limits<size_t>::max();
            double bestProb = -1.0;
            for (const Vector2Int& idx : openMoveSet)
            {
                const size_t cell = gridMetadata.indexOf(idx);
                if (pmfs->occupancy[cell] != Occupancy::Free)
                    continue;
                if (pmfs->sourceProbability[cell] > bestProb)
                {
                    bestProb = pmfs->sourceProbability[cell];
                    bestCell = cell;
                }
            }
            if (bestCell != std::numeric_limits<size_t>::max())
            {
                const Vector2Int mi = gridMetadata.indices2D(bestCell);
                NavigateToPose::Goal mapGoal = indexToGoal(mi.x, mi.y);
                if (checkGoal(mapGoal))
                    goal = mapGoal;
            }
        }
        if (!pmfs->ctpiPlannerEnabled && effectiveGuidanceWeight > 0.0 && nativeGoalFound && guidedGoalFound)
        {
            const auto posteriorExpectedDistance = [&](const NavigateToPose::Goal& candidateGoal)
            {
                double weightedDistance = 0.0;
                double totalProbability = 0.0;
                for (size_t i = 0; i < pmfs->sourceProbability.size(); ++i)
                {
                    if (pmfs->occupancy[i] != Occupancy::Free)
                        continue;
                    const double probability = pmfs->sourceProbability[i];
                    if (!(std::isfinite(probability) && probability > 0.0))
                        continue;
                    const Vector2 sourceCoordinate = gridMetadata.indicesToCoordinates(gridMetadata.indices2D(i));
                    const double dx = static_cast<double>(sourceCoordinate.x) - candidateGoal.pose.pose.position.x;
                    const double dy = static_cast<double>(sourceCoordinate.y) - candidateGoal.pose.pose.position.y;
                    weightedDistance += probability * std::hypot(dx, dy);
                    totalProbability += probability;
                }
                return totalProbability > 0.0 ? weightedDistance / totalProbability : std::numeric_limits<double>::infinity();
            };
            if (posteriorExpectedDistance(guidedGoal) < posteriorExpectedDistance(nativeGoal))
                goal = guidedGoal;
        }

        if (closedMoveSet.find(pmfs->gridMetadata.coordinatesToIndices(pmfs->currentRobotPose.pose.pose)) == closedMoveSet.end())
            openMoveSet.insert(pmfs->gridMetadata.coordinatesToIndices(pmfs->currentRobotPose.pose.pose));

        movesCounter++;
        publishMarkers();

        sendGoal(goal);
    }

    // Calculating this is a bit complex, specially if you want to do it in a reasonable amount of time
    // The main idea is to evaluate how much information about the source a specific cell gives by considering the case in which you know its hit frequency perfectly (confidence of 1)
    // You calculate the source prob distribution in that hypothetical case, and take the change in entropy with respect to the current entropy
    // The thing is, you can set the confidence to 1, but with what hit frequency?
    // Well, we can calculate a probability distribution for the hit frequency from the *current* confidence, and use that to then calculate the expected value of the entropy reduction
    // And that's what this does. There is some additional complexity in making it run fast (explained below), where we avoid re-comparing entire maps after modifying a single cell

    // Also, for speed reasons we are currently using the result of the coarsest simulation level instead of the final source distribution.
    // Could probably be changed without it becoming too slow. Probably.
    void MovingStatePMFS::calculateMutualInformationGas()
    {
        ScopedStopwatch watch("MutualInformation");
        ZoneScopedN("MutualInformation");

        // normalize the current source probs
        {
            double sum = 0;
            for (const auto& simResult : pmfs->simulations.resultsFirstLevel)
            {
                if (!simResult.valid)
                    continue;
                sum += simResult.sourceProb;
            }
            for (auto& simResult : pmfs->simulations.resultsFirstLevel)
                simResult.sourceProb /= sum;
        }

        // get the probability of each hit frequency in each cell, according to the current p(h_i) and the confidence value
        constexpr size_t discretizationLevels = PMFS_internal::HitProbability::numBuckets;
        std::vector<std::array<double, discretizationLevels>> probF(pmfs->hitProbability.size());
        for (size_t i = 0; i < probF.size(); i++)
            probF[i] = pmfs->hitProbability[i].frequencyDistribution();

        // use the hit frequency probabilities to calculate the conditional entropy
        std::vector<double> conditionalEntropy(pmfs->sourceProbability.size(), 0.0);
        {
            ZoneScopedN("ConditionalEntropy");

            // The cell index needs to be the outer loop, because we need to normalize the source probabilities given knowledge of this cell
#pragma omp parallel for
            for (size_t i = 0; i < conditionalEntropy.size(); i++)
            {
                if (pmfs->occupancy[i] != Occupancy::Free)
                    continue;

                // iterate over the list of possible hit frequency values for this one cell
                for (size_t bucket = 0; bucket < discretizationLevels; bucket++)
                {
                    double probabilityOfFreq = probF[i][bucket];
                    double freq = (bucket + 0.5) * (1. / discretizationLevels);

                    // We need to normalize the source probabilities before calculating the entropy
                    //-----------------------------------------------------

                    // store the source probs for later normalization
                    std::vector<long double> sourceProbs(pmfs->simulations.resultsFirstLevel.size(), 0.0);
                    long double sum = 0; // for normalizing

                    for (size_t simulationIndex = 0; simulationIndex < pmfs->simulations.resultsFirstLevel.size(); simulationIndex++)
                    {
                        const auto& simResult = pmfs->simulations.resultsFirstLevel[simulationIndex];
                        if (!simResult.valid)
                            continue;

                        // instead of calculating the source probability by comparing the two maps (the simulated one, and the measured one with a single cell modified),
                        // we use the already calculated source prob. If we divide p(s_k | f) by the current p(s_k | f_i) and then multiply by the modified p(s_k | f_i*),
                        // we get the same result but avoid re-comparing all the untouched cells

                        // current p(s_k | f_i)
                        double probGivenThisCell = pmfs->simulations.probabilityFromSingleCell(pmfs->hitProbability[i], simResult.hitMap[i]);

                        PMFS_internal::HitProbability localCopy = pmfs->hitProbability[i];
                        localCopy.setProbability(freq);
                        localCopy.confidence = 1;
                        double probWithNewFreq = pmfs->simulations.probabilityFromSingleCell(localCopy, simResult.hitMap[i]);

                        // source prob after modifying this cell in the map
                        // we store it in a vector because we need to normalize before calculating the entropy
                        sourceProbs[simulationIndex] = (simResult.sourceProb / probGivenThisCell) * probWithNewFreq;
                        sum += sourceProbs[simulationIndex];
                    }

                    // calculate the entropy for this particular conditional
                    double entropyThisFreq = 0;
                    for (size_t simulationIndex = 0; simulationIndex < pmfs->simulations.resultsFirstLevel.size(); simulationIndex++)
                    {
                        const auto& simResult = pmfs->simulations.resultsFirstLevel[simulationIndex];
                        if (!simResult.valid)
                            continue;

                        long double sourceProbWithFreq = sourceProbs[simulationIndex] / sum;
                        entropyThisFreq -= sourceProbWithFreq * std::log(sourceProbWithFreq);
                    }

                    // the conditional entropy is an expected value, so multiply by the probability of this frequency and add to a running total
                    conditionalEntropy[i] += probabilityOfFreq * entropyThisFreq;
                }
            }
        }

        // calculate the mutual information: H(S) - H(S|F)
        {
            mutualInformationGas.clear();
            mutualInformationGas.resize(pmfs->sourceProbability.size(), 0.0);
            double entropyS = 0;
            for (size_t i = 0; i < pmfs->sourceProbability.size(); i++)
            {
                if (pmfs->occupancy[i] != Occupancy::Free)
                    continue;
                double p = pmfs->sourceProbability[i];
                entropyS -= p * std::log(p);
            }

            for (size_t i = 0; i < conditionalEntropy.size(); i++)
            {
                if (pmfs->occupancy[i] != Occupancy::Free)
                    continue;
                mutualInformationGas[i] = entropyS - conditionalEntropy[i];
            }
        }

        // visualization with rviz markers
        {
            double min = DBL_MAX;
            for (size_t i = 0; i < mutualInformationGas.size(); i++)
            {
                if (pmfs->occupancy[i] != Occupancy::Free)
                    continue;
                min = std::min(min, mutualInformationGas[i]);
            }

            auto maxVal = *std::max_element(mutualInformationGas.begin(), mutualInformationGas.end());
            GSL_INFO("Max mutual info: {:.3f}", maxVal);

            std::vector<std_msgs::msg::ColorRGBA> colors(mutualInformationGas.size());
            for (size_t i = 0; i < mutualInformationGas.size(); i++)
                colors[i] = Utils::valueToColor(mutualInformationGas[i], min, maxVal, Utils::valueColorMode::Linear);

            Utils::publishDebugMarkers(
                Grid2D<std_msgs::msg::ColorRGBA>(colors, pmfs->occupancy, pmfs->gridMetadata),
                "MutualInformation");
        }
    }

    double MovingStatePMFS::explorationValue(int i, int j)
    {
        // the exploration value is the sum of the uncertainty about the hit probability for all cells around (i,j)

        Vector2Int ij(i, j);
        auto range = pmfs->visibilityMap->at(ij);

        double sum = 0;
        for (const auto& p : range)
        {
            float distance = vmath::length(Vector2(ij - p)); // not the navigable distance, but we are close enough that it does not matter
            sum += (1 - pmfs->hitProbability[pmfs->gridMetadata.indexOf(p)].confidence) * std::exp(-distance);
            GSL_ASSERT(sum > 0);
        }
        return sum;
    }

    double MovingStatePMFS::informationValue(int i, int j)
    {
        auto& gridMetadata = pmfs->gridMetadata;
        Vector2Int ij(i, j);
        auto range = pmfs->visibilityMap->at(ij);

        double sum = 0;
        for (const auto& p : range)
        {
            // double varianceTerm = mutualInformationGas[gridMetadata.indexOf(indices)];
            double varianceTerm = pmfs->simulations.varianceOfHitProb[gridMetadata.indexOf(i, j)] * (1 - pmfs->hitProbability[gridMetadata.indexOf(i, j)].confidence);

            float distance = vmath::length(Vector2(ij - p)); // not the navigable distance, but we are close enough that it does not matter
            sum += varianceTerm * std::exp(-distance);
            GSL_ASSERT(sum > 0);
        }
        return sum;
    }

    NavigateToPose::Goal MovingStatePMFS::indexToGoal(int i, int j)
    {
        NavigateToPose::Goal goal;
        goal.pose.header.frame_id = "map";
        goal.pose.header.stamp = pmfs->node->now();

        Vector2 pos = pmfs->gridMetadata.indicesToCoordinates(i, j);
        Vector2 coordR(pmfs->currentRobotPose.pose.pose.position.x, pmfs->currentRobotPose.pose.pose.position.y);

        double move_angle = (std::atan2(pos.y - coordR.y, pos.x - coordR.x));
        goal.pose.pose.position.x = pos.x;
        goal.pose.pose.position.y = pos.y;
        goal.pose.pose.orientation = Utils::createQuaternionMsgFromYaw(angles::normalize_angle(move_angle));
#ifdef USE_NAV_ASSISTANT
        goal.turn_before_nav = true;
#endif
        return goal;
    }

    void MovingStatePMFS::debugMoveTo(int i, int j)
    {
        GSL_INFO("Sending a goal from UI. This is not part of the normal execution flow of the algorithm");
        currentGoal = std::nullopt;
        NavigateToPose::Goal goal = indexToGoal(i, j);
        sendGoal(goal);
    }

    void MovingStatePMFS::Fail()
    {
        // There is a somewhat inconsistent behaviour when a goal times out and is manually cancelled.
        // sometimes we get a callback notifying of the cancelation, sometimes not
        // when we do, Fail() gets called twice: once by us, once inside the callback
        // if this is the second time, we should not do anything
        if (!currentGoal.has_value())
            return;

        Vector2Int indicesGoal = pmfs->gridMetadata.coordinatesToIndices(currentGoal.value().pose.pose);
        openMoveSet.erase(indicesGoal);
        closedMoveSet.insert(indicesGoal);
        MovingState::Fail();
    }

    void MovingStatePMFS::publishMarkers()
    {
        Grid2DMetadata& gridMetadata = pmfs->gridMetadata;
        Grid2D<PMFS_internal::HitProbability> grid(pmfs->hitProbability, pmfs->occupancy, gridMetadata);

        Marker explorationMarker = Utils::emptyMarker({0.2, 0.2}, pmfs->node->get_clock());

        Marker varianceMarker = explorationMarker;

        Marker movementSetsMarker = explorationMarker;

        double maxExpl = -DBL_MAX;
        double maxVar = -DBL_MAX;
        double minExpl = DBL_MAX;
        double minVar = DBL_MAX;
        for (int b = 0; b < gridMetadata.dimensions.y; b++)
        {
            for (int a = 0; a < gridMetadata.dimensions.x; a++)
            {
                if (!grid.freeAt(a, b))
                    continue;
                maxExpl = std::max(maxExpl, explorationValue(a, b));
                maxVar = std::max(maxVar, pmfs->simulations.varianceOfHitProb[gridMetadata.indexOf({a, b})] * (1 - grid.dataAt(a, b).confidence));

                minExpl = std::min(minExpl, explorationValue(a, b));
                minVar = std::min(minVar, pmfs->simulations.varianceOfHitProb[gridMetadata.indexOf({a, b})] * (1 - grid.dataAt(a, b).confidence));
            }
        }

        for (int b = 0; b < gridMetadata.dimensions.y; b++)
        {
            for (int a = 0; a < gridMetadata.dimensions.x; a++)
            {
                if (!grid.freeAt(a, b))
                    continue;
                auto coords = gridMetadata.indicesToCoordinates(a, b);
                Point p;
                p.x = coords.x;
                p.y = coords.y;
                p.z = pmfs->settings.visualization.markers_height;

                std_msgs::msg::ColorRGBA explorationColor;
                std_msgs::msg::ColorRGBA varianceColor;

                if (openMoveSet.find(Vector2Int(a, b)) == openMoveSet.end())
                {
                    explorationColor.r = 0;
                    explorationColor.g = 0;
                    explorationColor.b = 0;
                    explorationColor.a = 1;
                }
                else
                {
                    explorationColor = Utils::valueToColor(explorationValue(a, b), minExpl, maxExpl, Utils::valueColorMode::Linear);
                }
                varianceColor =
                    Utils::valueToColor(pmfs->simulations.varianceOfHitProb[gridMetadata.indexOf({a, b})] * (1 - grid.dataAt(a, b).confidence),
                                        minVar, maxVar, Utils::valueColorMode::Linear);

                explorationMarker.points.push_back(p);
                explorationMarker.colors.push_back(explorationColor);

                p.z = pmfs->settings.visualization.markers_height - 0.1;
                varianceMarker.points.push_back(p);
                varianceMarker.colors.push_back(varianceColor);

                movementSetsMarker.points.push_back(p);
                if (openMoveSet.find({a, b}) != openMoveSet.end())
                    movementSetsMarker.colors.push_back(Utils::create_color(0, 1, 0, 1));
                else if (closedMoveSet.find(Vector2Int(a, b)) != closedMoveSet.end())
                    movementSetsMarker.colors.push_back(Utils::create_color(1, 0, 0, 1));
                else
                    movementSetsMarker.colors.push_back(Utils::create_color(0, 0, 1, 1));
            }
        }
        publishers.explorationValue->publish(explorationMarker);
        publishers.varianceHit->publish(varianceMarker);
        publishers.movementSets->publish(movementSetsMarker);
    }

} // namespace GSL
