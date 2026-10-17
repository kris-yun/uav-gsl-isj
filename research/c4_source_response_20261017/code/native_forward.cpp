#include "support.hpp"
namespace GSL::PMFS_internal {
thread_local Utils::PrecalculatedGaussian<2500> gaussian;
    long double Simulations::sourceProbFromMaps(const Grid2D<HitProbability>& measuredHitProb, const std::vector<float>& hitMap) const
    {
        ZoneScoped;
        long double total = 1;
        for (int i = 0; i < measuredHitProb.data.size(); i++)
        {
            if (measuredHitProb.occupancy[i] != Occupancy::Free)
                continue;

            const double& simulated = hitMap[i];
            double sourceGivenThisCell = probabilityFromSingleCell(measuredHitProb.data[i], simulated);
            total *= sourceGivenThisCell;
            GSL_ASSERT(!std::isnan(total));
        }
        return total;
    }
    double Simulations::probabilityFromSingleCell(HitProbability hitProb, double simulated) const
    {
#define FREQUENCY_DISTRIBUTION_METHOD 0
#if FREQUENCY_DISTRIBUTION_METHOD
        auto frequencyDistribution = hitProb.frequencyDistribution();
        double result = 0;
        for (int freqIndex = 0; freqIndex < frequencyDistribution.size(); freqIndex++)
        {
            float measured = HitProbability::frequencyOfBucket(freqIndex);
            result += frequencyDistribution[freqIndex] * probabilitySingleFrequency(measured, simulated);
            GSL_ASSERT(!std::isnan(result));
        }
        return result;
#else
        return Utils::lerp(1, probabilitySingleFrequency(hitProb.probability(), simulated), hitProb.confidence);
#endif
    }
    double Simulations::probabilitySingleFrequency(double measured, double simulated) const
    {
        return 1 - std::abs(measured - simulated) * settings.sourceDiscriminationPower;
    }
    void Simulations::moveFilament(Filament& filament, Vector2Int& indices, float deltaTime, float noiseSTDev) const
    { ++diag::moves;
        Vector2 velocity = wind.dataAt(indices.x, indices.y) + Vector2(gaussian.nextValue(0, noiseSTDev), gaussian.nextValue(0, noiseSTDev));

        Vector2 newPos = filament.position + deltaTime * velocity;
        moveAlongPath(filament.position, newPos);
    }
    bool Simulations::filamentIsOutside(const Filament& filament) const
    {
        Vector2Int newIndices = measuredHitProb.metadata.coordinatesToIndices(filament.position.x, filament.position.y);
        return !measuredHitProb.metadata.indicesInBounds(newIndices);
    }
    void Simulations::simulateSourceInPosition(const SimulationSource& source, std::vector<float>& hitMap, bool warmup,
                                               int timesteps, float deltaTime, float noiseSTDev) const
    {
        constexpr int numFilamentsIteration = 5;
        size_t max_filaments = settings.maxWarmupIterations * numFilamentsIteration + timesteps * numFilamentsIteration;

        // To avoid having to delete filaments from the middle of the vector, which is quite slow, we will ping-pong the active filaments between two vectors
        // at the start of any iteration, one vector (active) will contain all the released filaments and the other one will be empty
        // after each filament has been moved, if it is still active, it will be copied to the other vector
        // then, the active vector changes and the old one is cleared
        std::vector<Filament> filaments1;
        std::vector<Filament> filaments2;
        filaments1.reserve(max_filaments);
        filaments2.reserve(max_filaments);
        std::vector<Filament>* activeFilamentVec = &filaments1;
        std::vector<Filament>* otherFilamentVec = &filaments2;

        std::vector<uint16_t> updated(hitMap.size(), 0); // index of the last iteration in which this cell was updated, to avoid double-counting

        // warm-up: we don't want to start recording frequency of hits until the shape of the plume has stabilized. Wait until a filament exits the
        // environment through an outlet, or a maximum number of steps
        {
            ZoneScopedN("Warmup");

            bool stable = false;
            int iterationCount = 0;
            while (iterationCount < settings.minWarmupIterations || (!stable && iterationCount < settings.maxWarmupIterations))
            {
                for (size_t i = 0; i < numFilamentsIteration; i++)
                {
                    activeFilamentVec->emplace_back();
                    activeFilamentVec->back().position = source.getPoint();
                }

                for (Filament& filament : *activeFilamentVec)
                {
                    auto indices = measuredHitProb.metadata.coordinatesToIndices(filament.position.x, filament.position.y);

                    // move active filaments
                    moveFilament(filament, indices, deltaTime * 2, noiseSTDev);

                    // remove filaments
                    if (filamentIsOutside(filament))
                        stable = true;
                    else
                        otherFilamentVec->push_back(filament);
                }
                iterationCount++;

                // "other" now contains the list of all the filaments that are still available, so swap the vectors and remove the old list
                activeFilamentVec->clear();
                std::swap(activeFilamentVec, otherFilamentVec);
            }
        }

        ZoneScopedN("Recording");
        // now, we do the thing
        for (int t = 1; t < timesteps + 1; t++)
        {
            for (int i = 0; i < numFilamentsIteration; i++)
            {
                activeFilamentVec->emplace_back();
                activeFilamentVec->back().position = source.getPoint();
            }

            for (Filament& filament : *activeFilamentVec)
            {
                // update map
                auto indices = measuredHitProb.metadata.coordinatesToIndices(filament.position.x, filament.position.y);
                size_t index = measuredHitProb.metadata.indexOf(indices);
                GSL_ASSERT(measuredHitProb.metadata.indicesInBounds(indices));
                // mark as updated so it doesn't count multiple filaments in the same timestep
                if (updated[index] < t)
                {
                    hitMap[index]++;
                    updated[index] = t;
                }

                // move active filaments
                moveFilament(filament, indices, deltaTime, noiseSTDev);

                // remove filaments
                if (!filamentIsOutside(filament))
                    otherFilamentVec->push_back(filament);
            }
            activeFilamentVec->clear();
            std::swap(activeFilamentVec, otherFilamentVec);
        }

        // convert the total hit count into relative frequency
        for (int i = 0; i < measuredHitProb.data.size(); i++)
        {
            if (measuredHitProb.occupancy[i] == Occupancy::Free)
                hitMap[i] = hitMap[i] / timesteps;
        }
    }
    Vector2 SimulationSource::getPoint() const
    {
        if (mode == Mode::Point)
            return point;

        Vector2 start = metadata.indicesToCoordinates(nqaNode->origin.x, nqaNode->origin.y, false);
        Vector2 end = metadata.indicesToCoordinates(nqaNode->origin.x + nqaNode->size.x, nqaNode->origin.y + nqaNode->size.y, false);

        Vector2 randP(Utils::uniformRandomF(start.x, end.x), Utils::uniformRandomF(start.y, end.y));
        GSL_ASSERT(randP.x >= start.x && randP.x < end.x && randP.y >= start.y && randP.y < end.y);
        ++diag::releases; return diag::source_point(randP);
    }
    bool Simulations::moveAlongPath(Vector2& currentPosition, const Vector2& end) const
    {
        Vector2Int indexEnd = measuredHitProb.metadata.coordinatesToIndices(end.x, end.y);
        Vector2Int indexOrigin = measuredHitProb.metadata.coordinatesToIndices(currentPosition.x, currentPosition.y);

        if (!measuredHitProb.freeAt(indexOrigin.x, indexOrigin.y))
        {
            return false;
        }

        // try to avoid doing the raycast by looking at the pre-computed visibilityMap
        if (indexOrigin == indexEnd || (measuredHitProb.metadata.indicesInBounds(indexEnd) && measuredHitProb.freeAt(indexEnd.x, indexEnd.y) &&
                                        visibilityMap->isVisible(indexOrigin, indexEnd) == Visibility::Visible))
        {
            currentPosition = end;
            return true;
        }

#define USE_DDA 0
#if USE_DDA
        Vector2 movement = end - currentPosition;
        DDA::_2D::RayCastInfo raycastInfo =
            DDA::_2D::castRay<GSL::Occupancy>(currentPosition, movement, vmath::length(movement),
                                              DDA::_2D::Map<GSL::Occupancy>(measuredHitProb.occupancy, measuredHitProb.metadata.origin,
                                                                            measuredHitProb.metadata.cellSize, measuredHitProb.metadata.dimensions),
                                              [](const GSL::Occupancy& occ)
                                              {
                                                  return occ == GSL::Occupancy::Free;
                                              });
        // This is a completely hacky arbitrary value to try and stop filaments from getting stuck right next to a wall
        // ideally, we should implement a "deflection" instead so they move along the wall a bit rather than stopping dead
        constexpr float wallStoppingProportion = 0.7;
        currentPosition += movement * raycastInfo.distance * wallStoppingProportion;

        return true;
#else
        const auto& metadata = measuredHitProb.metadata;
        bool pathIsFree = true;

        Vector2 vector = end - currentPosition;
        float travelDistance = vmath::length(vector);
        float stepSize = std::min(travelDistance, metadata.cellSize * 0.5f);
        Vector2 increment = vmath::normalized(vector) * stepSize;
        int steps = travelDistance / stepSize;

        int index = 0;
        while (index < steps && pathIsFree)
        {
            currentPosition += increment;
            index++;
            Vector2Int pair = metadata.coordinatesToIndices(currentPosition.x, currentPosition.y);
            pathIsFree = !metadata.indicesInBounds(pair) || measuredHitProb.freeAt(pair.x, pair.y);
            if (!pathIsFree)
                currentPosition -= increment;
        }
        return pathIsFree;
#endif
    }
    void Simulations::blurHitMap(cv::Mat& asImage) const
    {
        cv::GaussianBlur(asImage, asImage, cv::Size(0, 0), settings.blurSigmaX, settings.blurSigmaY);
        // divide by the blurred mask to correct the edges always getting lower
        // TODO measure performance of doing this repeatedly. Is it worth it to pre-compute and only redo it if the blur sigma has changed?
        cv::Mat blurredMask;
        cv::GaussianBlur(freeSpaceMask, blurredMask, cv::Size(0, 0), settings.blurSigmaX, settings.blurSigmaY);

        for (int i = 0; i < measuredHitProb.metadata.dimensions.y; i++)
            for (int j = 0; j < measuredHitProb.metadata.dimensions.x; j++)
                if (blurredMask.at<float>(i, j) != 0)
                    asImage.at<float>(i, j) = Utils::clamp(asImage.at<float>(i, j) / blurredMask.at<float>(i, j), 0, 1);
    }
}
