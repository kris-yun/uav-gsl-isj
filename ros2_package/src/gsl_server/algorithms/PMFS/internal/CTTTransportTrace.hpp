#pragma once

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <vector>

namespace GSL::PMFS_internal::ctt_v13
{
    inline constexpr std::int32_t kNeverReached = -1;

    // Truth-free sufficient statistics recorded from one keyed forward
    // transport realization. Bins are the native simulator recording steps.
    struct TransportTrace
    {
        std::uint64_t timesteps = 0;
        std::uint64_t cellCount = 0;
        std::uint64_t wordsPerStep = 0;
        std::vector<std::uint64_t> occupancyWords;
        std::vector<std::uint32_t> activeFilamentCounts;
        std::vector<std::int32_t> firstHitBins;

        void reset(std::size_t stepCount, std::size_t cells)
        {
            if (stepCount == 0 || cells == 0)
                throw std::invalid_argument("CTT trace dimensions must be positive");
            if (cells > std::numeric_limits<std::uint64_t>::max() - 63)
                throw std::overflow_error("CTT trace cell count overflow");
            timesteps = static_cast<std::uint64_t>(stepCount);
            cellCount = static_cast<std::uint64_t>(cells);
            wordsPerStep = (cellCount + 63U) / 64U;
            if (timesteps > std::numeric_limits<std::size_t>::max() / wordsPerStep)
                throw std::overflow_error("CTT trace allocation overflow");
            occupancyWords.assign(static_cast<std::size_t>(timesteps * wordsPerStep), 0U);
            activeFilamentCounts.assign(stepCount, 0U);
            firstHitBins.assign(cells, kNeverReached);
        }

        void setActiveFilamentCount(std::size_t step, std::size_t count)
        {
            requireStep(step);
            if (count > std::numeric_limits<std::uint32_t>::max())
                throw std::overflow_error("CTT active-filament count overflow");
            activeFilamentCounts[step] = static_cast<std::uint32_t>(count);
        }

        void markOccupied(std::size_t step, std::size_t cell)
        {
            requireStep(step);
            if (cell >= cellCount)
                throw std::out_of_range("CTT trace cell out of range");
            occupancyWords[step * static_cast<std::size_t>(wordsPerStep) + cell / 64U] |=
                std::uint64_t{1} << (cell % 64U);
            if (firstHitBins[cell] == kNeverReached)
                firstHitBins[cell] = static_cast<std::int32_t>(step);
        }

        [[nodiscard]] bool occupied(std::size_t step, std::size_t cell) const
        {
            requireStep(step);
            if (cell >= cellCount)
                throw std::out_of_range("CTT trace cell out of range");
            return (occupancyWords[
                step * static_cast<std::size_t>(wordsPerStep) + cell / 64U] &
                (std::uint64_t{1} << (cell % 64U))) != 0U;
        }

        [[nodiscard]] std::vector<float> reconstructFrequencies() const
        {
            validate();
            std::vector<float> result(static_cast<std::size_t>(cellCount), 0.0F);
            for (std::size_t step = 0; step < timesteps; ++step)
                for (std::size_t cell = 0; cell < cellCount; ++cell)
                    if (occupied(step, cell))
                        result[cell] += 1.0F;
            const float denominator = static_cast<float>(timesteps);
            for (float& value : result)
                value /= denominator;
            return result;
        }

        void validate() const
        {
            if (timesteps == 0 || cellCount == 0 ||
                wordsPerStep != (cellCount + 63U) / 64U ||
                occupancyWords.size() != timesteps * wordsPerStep ||
                activeFilamentCounts.size() != timesteps ||
                firstHitBins.size() != cellCount)
                throw std::runtime_error("CTT trace shape invalid");

            for (std::size_t cell = 0; cell < cellCount; ++cell)
            {
                std::int32_t observedFirst = kNeverReached;
                for (std::size_t step = 0; step < timesteps; ++step)
                    if (occupied(step, cell))
                    {
                        observedFirst = static_cast<std::int32_t>(step);
                        break;
                    }
                if (firstHitBins[cell] != observedFirst)
                    throw std::runtime_error("CTT first-hit/occupancy inconsistency");
            }

            const std::size_t remainder = static_cast<std::size_t>(cellCount % 64U);
            if (remainder != 0U)
            {
                const std::uint64_t validMask = (std::uint64_t{1} << remainder) - 1U;
                for (std::size_t step = 0; step < timesteps; ++step)
                    if ((occupancyWords[(step + 1U) * wordsPerStep - 1U] & ~validMask) != 0U)
                        throw std::runtime_error("CTT trace has set padding bits");
            }
        }

    private:
        void requireStep(std::size_t step) const
        {
            if (step >= timesteps)
                throw std::out_of_range("CTT trace step out of range");
        }
    };
}

