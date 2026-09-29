#pragma once

#include <cstdint>
#include <filesystem>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>

namespace GSL::PMFS_internal::rc_sd_tfei_v12
{
    struct ResponseBankMetadata
    {
        std::uint64_t dimensionsX = 0;
        std::uint64_t dimensionsY = 0;
        std::uint64_t cellCount = 0;
        std::uint64_t carrierCount = 0;
        std::uint64_t transportMembers = 0;
        std::uint64_t recordedTimesteps = 0;
        std::uint64_t methodSeed = 0;
        std::uint64_t transportSubstream = 0;
        double cellSize = 0.0;
        double originX = 0.0;
        double originY = 0.0;
        double deltaTime = 0.0;
        double noiseStandardDeviation = 0.0;
        double blurSigmaX = 0.0;
        double blurSigmaY = 0.0;
        std::vector<std::uint8_t> occupancy;
        std::vector<std::string> carrierIds;
        std::vector<double> carrierX;
        std::vector<double> carrierY;
        std::vector<std::uint64_t> carrierFreeCells;
    };

    namespace response_bank_detail
    {
        inline constexpr std::uint64_t kMagic = 0x31524b4e42323156ULL; // V12BNKR1
        inline constexpr std::uint64_t kVersion = 1;
        inline constexpr std::uint64_t kMaximumStringBytes = 4096;

        template <typename T>
        void writeScalar(std::ostream& output, const T& value)
        {
            static_assert(std::is_trivially_copyable_v<T>);
            output.write(reinterpret_cast<const char*>(&value), sizeof(T));
            if (!output)
                throw std::runtime_error("V12 response-bank write failed");
        }

        template <typename T>
        T readScalar(std::istream& input)
        {
            static_assert(std::is_trivially_copyable_v<T>);
            T value{};
            input.read(reinterpret_cast<char*>(&value), sizeof(T));
            if (!input)
                throw std::runtime_error("V12 response-bank truncated");
            return value;
        }

        inline void writeString(std::ostream& output, const std::string& value)
        {
            if (value.size() > kMaximumStringBytes)
                throw std::invalid_argument("V12 response-bank carrier id too long");
            writeScalar(output, static_cast<std::uint64_t>(value.size()));
            output.write(value.data(), static_cast<std::streamsize>(value.size()));
            if (!output)
                throw std::runtime_error("V12 response-bank string write failed");
        }

        inline std::string readString(std::istream& input)
        {
            const std::uint64_t size = readScalar<std::uint64_t>(input);
            if (size > kMaximumStringBytes)
                throw std::runtime_error("V12 response-bank string length invalid");
            std::string value(static_cast<std::size_t>(size), '\0');
            input.read(value.data(), static_cast<std::streamsize>(size));
            if (!input)
                throw std::runtime_error("V12 response-bank string truncated");
            return value;
        }

        inline void validateShape(const ResponseBankMetadata& metadata)
        {
            if (metadata.dimensionsX == 0 || metadata.dimensionsY == 0 ||
                metadata.cellCount == 0 || metadata.carrierCount == 0 ||
                metadata.transportMembers == 0 || metadata.recordedTimesteps == 0 ||
                metadata.dimensionsX > std::numeric_limits<std::uint64_t>::max() /
                    metadata.dimensionsY ||
                metadata.dimensionsX * metadata.dimensionsY != metadata.cellCount ||
                metadata.occupancy.size() != metadata.cellCount ||
                metadata.carrierIds.size() != metadata.carrierCount ||
                metadata.carrierX.size() != metadata.carrierCount ||
                metadata.carrierY.size() != metadata.carrierCount ||
                metadata.carrierFreeCells.size() != metadata.carrierCount)
                throw std::invalid_argument("V12 response-bank metadata shape invalid");
        }

        template <typename T>
        void requireEqual(const T& actual, const T& expected, const char* field)
        {
            if (actual != expected)
                throw std::runtime_error(std::string("V12 response-bank mismatch: ") + field);
        }
    }

    inline void writeResponseBankAtomic(
        const std::filesystem::path& path,
        const ResponseBankMetadata& metadata,
        const std::vector<std::vector<float>>& maps)
    {
        using namespace response_bank_detail;
        validateShape(metadata);
        const std::uint64_t expectedMaps = metadata.carrierCount *
            metadata.transportMembers;
        if (maps.size() != expectedMaps)
            throw std::invalid_argument("V12 response-bank map count invalid");
        for (const auto& map : maps)
            if (map.size() != metadata.cellCount)
                throw std::invalid_argument("V12 response-bank map shape invalid");
        if (!path.is_absolute())
            throw std::invalid_argument("V12 response-bank path must be absolute");
        if (std::filesystem::exists(path))
            throw std::runtime_error("V12 response-bank refuses to overwrite existing bank");
        const std::filesystem::path temporary(path.string() + ".tmp");
        if (std::filesystem::exists(temporary))
            throw std::runtime_error("V12 response-bank temporary path already exists");
        std::filesystem::create_directories(path.parent_path());
        std::ofstream output(temporary, std::ios::binary | std::ios::out);
        if (!output)
            throw std::runtime_error("V12 response-bank cannot create temporary file");
        writeScalar(output, kMagic);
        writeScalar(output, kVersion);
        writeScalar(output, metadata.dimensionsX);
        writeScalar(output, metadata.dimensionsY);
        writeScalar(output, metadata.cellCount);
        writeScalar(output, metadata.carrierCount);
        writeScalar(output, metadata.transportMembers);
        writeScalar(output, metadata.recordedTimesteps);
        writeScalar(output, metadata.methodSeed);
        writeScalar(output, metadata.transportSubstream);
        writeScalar(output, metadata.cellSize);
        writeScalar(output, metadata.originX);
        writeScalar(output, metadata.originY);
        writeScalar(output, metadata.deltaTime);
        writeScalar(output, metadata.noiseStandardDeviation);
        writeScalar(output, metadata.blurSigmaX);
        writeScalar(output, metadata.blurSigmaY);
        output.write(reinterpret_cast<const char*>(metadata.occupancy.data()),
                     static_cast<std::streamsize>(metadata.occupancy.size()));
        for (std::size_t carrier = 0; carrier < metadata.carrierCount; ++carrier)
        {
            writeString(output, metadata.carrierIds[carrier]);
            writeScalar(output, metadata.carrierX[carrier]);
            writeScalar(output, metadata.carrierY[carrier]);
            writeScalar(output, metadata.carrierFreeCells[carrier]);
        }
        for (const auto& map : maps)
            output.write(reinterpret_cast<const char*>(map.data()),
                         static_cast<std::streamsize>(map.size() * sizeof(float)));
        if (!output)
            throw std::runtime_error("V12 response-bank map write failed");
        output.close();
        if (!output)
            throw std::runtime_error("V12 response-bank close failed");
        std::filesystem::rename(temporary, path);
    }

    inline std::vector<std::vector<float>> readResponseBankValidated(
        const std::filesystem::path& path,
        const ResponseBankMetadata& expected)
    {
        using namespace response_bank_detail;
        validateShape(expected);
        if (!path.is_absolute())
            throw std::invalid_argument("V12 response-bank path must be absolute");
        std::ifstream input(path, std::ios::binary | std::ios::in);
        if (!input)
            throw std::runtime_error("V12 response-bank cannot be opened");
        requireEqual(readScalar<std::uint64_t>(input), kMagic, "magic");
        requireEqual(readScalar<std::uint64_t>(input), kVersion, "version");
        requireEqual(readScalar<std::uint64_t>(input), expected.dimensionsX, "dimensions_x");
        requireEqual(readScalar<std::uint64_t>(input), expected.dimensionsY, "dimensions_y");
        requireEqual(readScalar<std::uint64_t>(input), expected.cellCount, "cell_count");
        requireEqual(readScalar<std::uint64_t>(input), expected.carrierCount, "carrier_count");
        requireEqual(readScalar<std::uint64_t>(input), expected.transportMembers, "transport_members");
        requireEqual(readScalar<std::uint64_t>(input), expected.recordedTimesteps, "recorded_timesteps");
        requireEqual(readScalar<std::uint64_t>(input), expected.methodSeed, "method_seed");
        requireEqual(readScalar<std::uint64_t>(input), expected.transportSubstream, "transport_substream");
        requireEqual(readScalar<double>(input), expected.cellSize, "cell_size");
        requireEqual(readScalar<double>(input), expected.originX, "origin_x");
        requireEqual(readScalar<double>(input), expected.originY, "origin_y");
        requireEqual(readScalar<double>(input), expected.deltaTime, "delta_time");
        requireEqual(readScalar<double>(input), expected.noiseStandardDeviation, "noise_standard_deviation");
        requireEqual(readScalar<double>(input), expected.blurSigmaX, "blur_sigma_x");
        requireEqual(readScalar<double>(input), expected.blurSigmaY, "blur_sigma_y");
        std::vector<std::uint8_t> occupancy(expected.occupancy.size());
        input.read(reinterpret_cast<char*>(occupancy.data()),
                   static_cast<std::streamsize>(occupancy.size()));
        if (!input)
            throw std::runtime_error("V12 response-bank occupancy truncated");
        requireEqual(occupancy, expected.occupancy, "occupancy");
        for (std::size_t carrier = 0; carrier < expected.carrierCount; ++carrier)
        {
            requireEqual(readString(input), expected.carrierIds[carrier], "carrier_id");
            requireEqual(readScalar<double>(input), expected.carrierX[carrier], "carrier_x");
            requireEqual(readScalar<double>(input), expected.carrierY[carrier], "carrier_y");
            requireEqual(readScalar<std::uint64_t>(input),
                         expected.carrierFreeCells[carrier], "carrier_free_cells");
        }
        const std::size_t mapCount = static_cast<std::size_t>(
            expected.carrierCount * expected.transportMembers);
        std::vector<std::vector<float>> maps(
            mapCount, std::vector<float>(static_cast<std::size_t>(expected.cellCount)));
        for (auto& map : maps)
        {
            input.read(reinterpret_cast<char*>(map.data()),
                       static_cast<std::streamsize>(map.size() * sizeof(float)));
            if (!input)
                throw std::runtime_error("V12 response-bank map truncated");
        }
        char trailing = 0;
        if (input.read(&trailing, 1))
            throw std::runtime_error("V12 response-bank has trailing bytes");
        if (!input.eof())
            throw std::runtime_error("V12 response-bank read failure");
        return maps;
    }
}
