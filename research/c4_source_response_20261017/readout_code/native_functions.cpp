#include "native_support.hpp"
namespace GSL {
    void PMFSLib::EstimateHitProbabilities(Grid2D<HitProbability>& hitProb, const VisibilityMap& visibilityMap,
                                           PMFS_internal::HitProbabilitySettings& settings, bool hit, double downwindDirection, double windSpeed,
                                           Vector2Int robotPosition)
    {
        // receiving propagation this step. Can still be modified by better estimations.
        HashSet openPropagationSet;
        // causing propagation this step. No longer modifiable
        HashSet activePropagationSet;
        // old news
        HashSet closedPropagationSet;

        double kernel_rotation_wind = -angles::normalize_angle(downwindDirection + M_PI / 2);
        HitProbKernel kernel =
            {
                .angle = kernel_rotation_wind,
                .sigma = Vector2(
                    settings.kernelSigma / (1 + settings.kernelStretchConstant * windSpeed / settings.kernelSigma), // semi-minor ellipse axis
                    settings.kernelSigma + settings.kernelStretchConstant * windSpeed                               // semi-major axis
                    ),
                .valueAt1 = (hit ? 0.6f : 0.1f)};

        GSL_ASSERT(hitProb.metadata.indicesInBounds(robotPosition));
        size_t oC = std::max(0, robotPosition.x - settings.localEstimationWindowSize);
        size_t fC = std::min(hitProb.metadata.dimensions.x - 1, robotPosition.x + settings.localEstimationWindowSize);
        size_t oR = std::max(0, robotPosition.y - settings.localEstimationWindowSize);
        size_t fR = std::min(hitProb.metadata.dimensions.y - 1, robotPosition.y + settings.localEstimationWindowSize);
        for (size_t row = oR; row <= fR; row++)
        {
            for (size_t col = oC; col <= fC; col++)
            {
                Vector2Int rc(col, row);
                if (visibilityMap.isVisible(robotPosition, rc) != Visibility::Visible)
                    continue;

                if (rc == robotPosition)
                    closedPropagationSet.insert(rc);
                else
                    activePropagationSet.insert(rc);

                // TODO should probably use the coordinates rather than the cell indices, but it would require adjusting all the parameters in the launch file, so...
                // TODO good news is once we've done this the parameters become cell-size-independent
                // Vector2 offset = hitProb.metadata.indicesToCoordinates(rc) - hitProb.metadata.indicesToCoordinates(robotPosition);
                Vector2 offset = Vector2(rc - robotPosition);
                hitProb.dataAt(col, row).distanceFromRobot = vmath::length(offset);
                hitProb.dataAt(col, row).originalPropagationDirection = vmath::normalized(offset);
                hitProb.dataAt(col, row).auxWeight = applyFalloffLogOdds(offset, kernel, settings);
            }
        }

        // propagate these short-range estimations to the entire environment using the navigation map
        // also calculate the distance field
        PropagateProbabilities(hitProb, settings, openPropagationSet, closedPropagationSet, activePropagationSet, kernel);

        double logOddsPrior = std::log(settings.prior / (1 - settings.prior));
        for (size_t i = 0; i < hitProb.data.size(); i++)
        {
            if (hitProb.occupancy[i] != Occupancy::Free)
                continue;

            HitProbability& cell = hitProb.data[i];
            // BAYESIAN BINARY FILTER. this is the important part
            cell.logOdds += cell.auxWeight - logOddsPrior;
            GSL_ASSERT(!std::isnan(cell.logOdds));

            // confidence
            cell.omega += Utils::evaluate1DGaussian(cell.distanceFromRobot, settings.confidenceSigmaSpatial);
            double exponent = -cell.omega / std::pow(settings.confidenceMeasurementWeight, 2);
            cell.confidence = 1 - std::exp(exponent);
        }
    }
    double PMFSLib::PropagateProbabilities(Grid2D<HitProbability>& hitProb, const PMFS_internal::HitProbabilitySettings& settings,
                                           HashSet& openPropagationSet, HashSet& closedPropagationSet, HashSet& activePropagationSet,
                                           const HitProbKernel& kernel)
    {
        double total = 0;

        auto calculateNewAuxWeight = [&openPropagationSet, &closedPropagationSet, &activePropagationSet, &kernel, &settings,
                                      &hitProb](int i, int j, Vector2Int previousCellIndices)
        {
            HitProbability& previousCell = hitProb.dataAt(previousCellIndices.x, previousCellIndices.y);
            HitProbability& currentCell = hitProb.dataAt(i, j);
            Vector2Int ij(i, j);

            float newDistance = previousCell.distanceFromRobot +
                                ((i == previousCellIndices.x || j == previousCellIndices.y) ? 1 : sqrt(2)); // distance of this new path to the cell
            float newWeight = applyFalloffLogOdds(previousCell.originalPropagationDirection * newDistance, kernel, settings);

            // if the cell can still receive propagation
            if (closedPropagationSet.find(ij) == closedPropagationSet.end() && activePropagationSet.find(ij) == activePropagationSet.end())
            {
                // if there already was a path to this cell
                if (openPropagationSet.find(ij) != openPropagationSet.end())
                {
                    // if the distance is the same, keep the best probability!
                    if (std::abs(newDistance - currentCell.distanceFromRobot) < 0.001 && newWeight > currentCell.auxWeight)
                    {
                        currentCell.auxWeight = newWeight;
                        currentCell.originalPropagationDirection = previousCell.originalPropagationDirection;
                    }
                    // else, keep the shortest path
                    else if (newDistance < currentCell.distanceFromRobot)
                    {
                        currentCell.auxWeight = newWeight;
                        currentCell.distanceFromRobot = newDistance;
                        currentCell.originalPropagationDirection = previousCell.originalPropagationDirection;
                    }
                }
                // if this is the first time we reach this cell
                else
                {
                    currentCell.auxWeight = newWeight;
                    currentCell.distanceFromRobot = newDistance;
                    currentCell.originalPropagationDirection = previousCell.originalPropagationDirection;
                    openPropagationSet.insert(ij);
                }
            }
        };

        while (!activePropagationSet.empty())
        {
            while (!activePropagationSet.empty())
            {
                Vector2Int p = *activePropagationSet.begin();

                if (hitProb.freeAt(p.x, p.y))
                    total += hitProb.dataAt(p.x, p.y).auxWeight;

                activePropagationSet.erase(activePropagationSet.begin());
                closedPropagationSet.insert(p);

                int oR = std::max(0, p.x - 1);
                int fR = std::min((int)hitProb.metadata.dimensions.x - 1, p.x + 1);
                int oC = std::max(0, p.y - 1);
                int fC = std::min((int)hitProb.metadata.dimensions.y - 1, p.y + 1);

                // 8-neighbour propagation
                for (int i = oR; i <= fR; i++)
                {
                    for (int j = oC; j <= fC; j++)
                    {
                        if (hitProb.freeAt(i, j))
                            calculateNewAuxWeight(i, j, p);
                    }
                }
            }

            activePropagationSet.clear();
            // the cells that were in the open set now are removed from it and can no longer receive propagation
            // therefore, the probabilities for these cells are now locked, and we can update the logodds
            for (const auto& par : openPropagationSet)
            {
                activePropagationSet.insert(par);
            }

            openPropagationSet.clear();
        }
        return total;
    }
    double PMFSLib::applyFalloffLogOdds(Vector2 originalVectorScaled, const HitProbKernel& kernel,
                                        const PMFS_internal::HitProbabilitySettings& settings)
    {
        double sampleGaussian = Utils::evaluate2DGaussian(originalVectorScaled, kernel.sigma, kernel.angle);
        double maxPossible = Utils::evaluate2DGaussian({0, 0}, kernel.sigma, kernel.angle);
        float prob = Utils::clamp(Utils::lerp(settings.prior, kernel.valueAt1, sampleGaussian / maxPossible), 0.001, 0.999);
        return std::log(prob / (1 - prob));
    }
}
namespace GSL::Utils {
    double lerp(double start, double end, double proportion)
    {
        if (proportion < 0 || std::isnan(proportion))
            return start;

        return start + (end - start) * std::min(1.0, proportion);
    }
    double clamp(double val, double min, double max)
    {
        return std::max(min, std::min(val, max));
    }
    double evaluate1DGaussian(double distance, double sigma)
    {
        return exp(-0.5 * (std::pow(distance, 2) / std::pow(sigma, 2))) / (sigma * std::sqrt(2 * M_PI));
    }
    double evaluate2DGaussian(const Vector2& sampleOffset, const Vector2& sigma, float distributionRotation)
    {
        // we rotate the vector instead of the gaussian because keeping the distribution axis-aligned removes several terms from the PDF equation
        Vector2 v = vmath::rotate(sampleOffset, distributionRotation);

        return std::exp(-0.5 * (std::pow(v.x / sigma.x, 2) + std::pow(v.y / sigma.y, 2))) / (2 * M_PI * sigma.x * sigma.y);
    }
    Vector2 ExpectedValue(const Grid2D<double> grid, double proportionBest)
    {
        struct CellData
        {
            Vector2Int indices;
            double probability;
            CellData(Vector2Int ind, double prob)
            {
                indices = ind;
                probability = prob;
            }
        };
        std::vector<CellData> data;
        for (int y = 0; y < grid.metadata.dimensions.y; y++)
        {
            for (int x = 0; x < grid.metadata.dimensions.x; x++)
            {
                if (grid.occupancy[grid.metadata.indexOf({x, y})] == Occupancy::Free)
                {
                    CellData cd(Vector2Int(x, y), grid.data[grid.metadata.indexOf({x, y})]);
                    data.push_back(cd);
                }
            }
        }

        std::sort(data.begin(), data.end(), [](const CellData& a, const CellData& b)
                  {
                      return a.probability > b.probability;
                  });

        double averageX = 0, averageY = 0;
        double sum = 0;

        for (int i = 0; i < data.size() * proportionBest; i++)
        {
            CellData& cd = data[i];
            Vector2 coord = grid.metadata.indicesToCoordinates(cd.indices.x, cd.indices.y);
            averageX += cd.probability * coord.x;
            averageY += cd.probability * coord.y;
            sum += cd.probability;
        }
        return Vector2(averageX / sum, averageY / sum);
    }
    double Variance(const Grid2D<double> grid)
    {
        Vector2 expected = ExpectedValue(grid, 1);
        double x = 0, y = 0;
        for (int row = 0; row < grid.metadata.dimensions.y; row++)
        {
            for (int col = 0; col < grid.metadata.dimensions.x; col++)
            {
                if (grid.occupancy[grid.metadata.indexOf({col, row})] == Occupancy::Free)
                {
                    Vector2 coords = grid.metadata.indicesToCoordinates(col, row);
                    double p = grid.data[grid.metadata.indexOf({col, row})];
                    x += pow(coords.x - expected.x, 2) * p;
                    y += pow(coords.y - expected.y, 2) * p;
                }
            }
        }
        return x + y;
    }
}
