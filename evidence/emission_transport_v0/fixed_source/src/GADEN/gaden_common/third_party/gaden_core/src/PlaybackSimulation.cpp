#include "gaden/datatypes/sources/PointSource.hpp"
#include "gaden/internal/Serialization.hpp"
#include <fstream>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <gaden/PlaybackSimulation.hpp>

namespace gaden
{

    PlaybackSimulation::PlaybackSimulation(Parameters params, std::shared_ptr<EnvironmentConfiguration> const& config, LoopConfig loop)
        : Simulation(config), parameters(params), loopConfig(loop)
    {
        currentIteration = parameters.startIteration;
        if (loopConfig.loop)
        {
            if (currentIteration > loopConfig.to)
                GADEN_WARN("Starting iteration {} is greater than loop limit {}!", currentIteration, loopConfig.to);

            if (loopConfig.from > loopConfig.to)
            {
                GADEN_ERROR("Incorrect loop configuration {}-{}. Setting loop to false", loopConfig.from, loopConfig.to);
                loopConfig.loop = false;
            }
        }

        compressedBuffer.resize(serialization::defaultBufferSize);
        rawBuffer.resize(serialization::defaultBufferSize);
    }

    void PlaybackSimulation::AdvanceTimestep()
    {
        std::string filename = fmt::format("{}/iteration_{}", parameters.resultsDirectory.c_str(), currentIteration);
        if (!std::filesystem::exists(filename))
        {
            GADEN_ERROR("File '{}' does not exist!", filename.c_str());
            currentIteration++;
            return;
        }

        // calculate the buffer sizes and resize if needed
        std::ifstream infile(filename, std::ios_base::binary);
        bool isModernFile = serialization::IsModernResultsFile(infile);
        serialization::FileCompressionMetadata compressionMetadata = serialization::GetCompressionMetadata(infile);

        // figure out how the file was compressed. Old files always used DEFLATE (zlib), but new ones have an enum in the header
        serialization::SkipGadenHeader(infile);

        // size the buffers
        size_t compressedSize = serialization::RemainingFileSize(infile);
        // uncompressed files
        if (compressionMetadata.uncompressedSize == 0)
            compressionMetadata.uncompressedSize = compressedSize;

        if (compressedBuffer.size() < compressedSize)
        {
            size_t newSize = compressedSize * 1.5;
            compressedBuffer.resize(newSize);
            GADEN_INFO("Resizing compressedBuffer to {} bytes", newSize);
        }

        if (rawBuffer.size() < compressionMetadata.uncompressedSize)
        {
            size_t newSize = compressionMetadata.uncompressedSize * 1.5;
            rawBuffer.resize(newSize);
            GADEN_INFO("Resizing rawBuffer to {} bytes", newSize);
        }

        // read the file
        // the stream position is set to the start of the compressed area (even in modern files with an uncompressed header)
        infile.read((char*)compressedBuffer.data(), compressedSize);
        infile.close();

        // decompress the contents
        if (compressionMetadata.mode == serialization::CompressionMode::LIBBSC)
            LibBSC::Decompress(compressedBuffer.data(), rawBuffer.data());
        else if (compressionMetadata.mode == serialization::CompressionMode::ZLIB)
            zlib::uncompress(rawBuffer.data(), &compressionMetadata.uncompressedSize, compressedBuffer.data(), compressedBuffer.size());
        else
            memcpy(rawBuffer.data(), compressedBuffer.data(), compressionMetadata.uncompressedSize);

        serialization::BufferReader reader((char*)rawBuffer.data(), compressionMetadata.uncompressedSize);

        // check the version of gaden used to generate the file
        reader.Read(&config->environment.versionMajor);
        if (config->environment.versionMajor == 1)
        {
            config->environment.versionMinor = 0; // pre 2.0 files had no minor version
            LoadLogfileVersion1(reader);
        }
        else if (config->environment.versionMajor == 2)
        {
            reader.Read(&config->environment.versionMinor, sizeof(int));
            if (config->environment.versionMinor <= 5)
                LoadLogfileVersionPre2_6(reader);
            else
                LoadLogfileVersion2_6(reader);
        }
        else
        {
            reader.Read(&config->environment.versionMinor, sizeof(int));
            LoadLogfile(reader);
        }
        currentIteration++;

        if (loopConfig.loop && currentIteration > loopConfig.to)
            currentIteration = loopConfig.from;
    }

    bool PlaybackSimulation::LoadIteration(size_t iteration)
    {
        const auto previous = currentIteration;
        currentIteration = iteration;
        const std::string filename = fmt::format("{}/iteration_{}", parameters.resultsDirectory.c_str(), currentIteration);
        if (!std::filesystem::exists(filename))
        {
            currentIteration = previous;
            return false;
        }
        AdvanceTimestep();
        return true;
    }

    const std::vector<Filament>& PlaybackSimulation::GetFilaments() const
    {
        return activeFilaments;
    }

    void PlaybackSimulation::LoadLogfile(serialization::BufferReader reader)
    {
        reader.Read(&config->environment.description);
        GasSource::DeserializeBinary(reader, simulationMetadata.source);
        reader.Read(&simulationMetadata.constants);

        int windIndex;
        reader.Read(&windIndex, sizeof(int));
        config->windSequence.SetCurrentIndex(windIndex);

        std::string modeStr;
        reader.ReadString(&modeStr);

        if (modeStr == "filaments")
        {
            mode = Mode::Filaments;
            activeFilaments.clear();
            reader.ReadVector(&activeFilaments);
        }
        else if (modeStr == "concentrations")
        {
            mode = Mode::Concentration;
            if (!concentrations)
            {
                GADEN_INFO("Simulation was generated with pre-calculated concentrations");
                concentrations.emplace();
                concentrations->resize(config->environment.numCells(), 0.0);
            }
            reader.ReadVector(&(*concentrations));
        }
        else
        {
            GADEN_SERIOUS_ERROR("File mode not recognized: '{}'. Something might have gone wrong with the binary serialization.");
            GADEN_TERMINATE;
        }
    }

} // namespace gaden

// backwards compatibility file parsing
//-------------------------------------
namespace gaden
{
    void PlaybackSimulation::LoadLogfileVersion1(serialization::BufferReader reader)
    {
        mode = Mode::Filaments;
        static bool warned = false;
        if (!warned)
        {
            GADEN_WARN(
                "You are reading a log file that was generated with an old version of gaden. While it should work correctly, if you experience any bugs, "
                "this is likely the cause. You can just re-run the filament simulator node to generate an updated version of the simulation");
            warned = true;
        }

        // Version-1 datasets exist in two on-disk coordinate variants under
        // the same version tag.  Newer VGR exports copied float-backed
        // coordinates into sizeof(double) slots, while older House02/03
        // exports stored native doubles.  Both variants have identical slot
        // widths, so decode both interpretations and select the one consistent
        // with the environment already loaded from OccupancyGrid3D.csv.
        double coordinatesAsDouble[6];
        float coordinatesAsFloat[6];
        for (size_t i = 0; i < 6; ++i)
        {
            std::uint8_t slot[sizeof(double)];
            reader.Read(slot, sizeof(slot));
            std::memcpy(&coordinatesAsDouble[i], slot, sizeof(double));
            std::memcpy(&coordinatesAsFloat[i], slot, sizeof(float));
        }

        auto& description = config->environment.description;
        const double expected[6] = {
            description.minCoord.x, description.minCoord.y, description.minCoord.z,
            description.maxCoord.x, description.maxCoord.y, description.maxCoord.z};
        double doubleScore = 0.0;
        double floatScore = 0.0;
        for (size_t i = 0; i < 6; ++i)
        {
            doubleScore += std::isfinite(coordinatesAsDouble[i])
                               ? std::fabs(coordinatesAsDouble[i] - expected[i])
                               : 1e300;
            floatScore += std::isfinite(coordinatesAsFloat[i])
                              ? std::fabs(static_cast<double>(coordinatesAsFloat[i]) - expected[i])
                              : 1e300;
        }
        const bool useFloatSlots = floatScore < doubleScore;
        const auto coordinate = [&](size_t i) {
            return useFloatSlots ? static_cast<double>(coordinatesAsFloat[i])
                                 : coordinatesAsDouble[i];
        };
        description.minCoord.x = coordinate(0);
        description.minCoord.y = coordinate(1);
        description.minCoord.z = coordinate(2);
        description.maxCoord.x = coordinate(3);
        description.maxCoord.y = coordinate(4);
        description.maxCoord.z = coordinate(5);
        GADEN_INFO(
            "Legacy V1 coordinate format={} double_score={} float_slot_score={}",
            useFloatSlots ? "FLOAT_IN_DOUBLE_SLOT" : "NATIVE_DOUBLE",
            doubleScore,
            floatScore);

        reader.Read(&description.dimensions.x, sizeof(int));
        reader.Read(&description.dimensions.y, sizeof(int));
        reader.Read(&description.dimensions.z, sizeof(int));

        double bufferDoubles[5];
        reader.Read(bufferDoubles, sizeof(double));
        description.cellSize = bufferDoubles[0];

        // Version-1 headers reserve five native-double slots after cell size.
        // They contain historical source metadata and are never exposed to the
        // player query API.
        reader.Read(bufferDoubles, 5 * sizeof(double));

        if (!simulationMetadata.source)
            simulationMetadata.source = std::make_shared<PointSource>();

        int gas_type_index;
        reader.Read(&gas_type_index, sizeof(int));
        simulationMetadata.source->gasType = static_cast<GasType>(gas_type_index);

        reader.Read(bufferDoubles, sizeof(double));
        simulationMetadata.constants.totalMolesInFilament = bufferDoubles[0];
        reader.Read(bufferDoubles, sizeof(double));
        simulationMetadata.constants.numMolesAllGasesIncm3 = bufferDoubles[0];

        int windIndex;
        reader.Read(&windIndex, sizeof(int));
        config->windSequence.SetCurrentIndex(windIndex);

        activeFilaments.clear();
        int filament_index;
        double x, y, z, stdDev;
        constexpr size_t legacyFilamentRecordBytes = sizeof(int) + 4 * sizeof(double);
        while (reader.CanRead(legacyFilamentRecordBytes))
        {
            reader.Read(&filament_index, sizeof(int));
            reader.Read(&x, sizeof(double));
            reader.Read(&y, sizeof(double));
            reader.Read(&z, sizeof(double));
            reader.Read(&stdDev, sizeof(double));

            activeFilaments.emplace_back(x, y, z, stdDev);
        }
    }

    void PlaybackSimulation::LoadLogfileVersionPre2_6(serialization::BufferReader reader)
    {
        mode = Mode::Filaments;
        reader.Read(&config->environment.description, sizeof(config->environment.description));
        gaden::Vector3 source_position;
        reader.Read(&source_position, sizeof(gaden::Vector3));

        if (!simulationMetadata.source)
            simulationMetadata.source = std::make_shared<PointSource>();

        int gas_type_index;
        reader.Read(&gas_type_index, sizeof(int));
        simulationMetadata.source->gasType = static_cast<GasType>(gas_type_index);

        double aux;
        reader.Read(&aux, sizeof(double));
        simulationMetadata.constants.totalMolesInFilament = aux;
        reader.Read(&aux, sizeof(double));
        simulationMetadata.constants.numMolesAllGasesIncm3 = aux;

        int windIndex;
        reader.Read(&windIndex, sizeof(int));
        config->windSequence.SetCurrentIndex(windIndex);

        activeFilaments.clear();
        int filament_index;
        double x, y, z, stdDev;
        while (!reader.Ended())
        {
            reader.Read(&filament_index, sizeof(int));
            reader.Read(&x, sizeof(double));
            reader.Read(&y, sizeof(double));
            reader.Read(&z, sizeof(double));
            reader.Read(&stdDev, sizeof(double));

            activeFilaments.emplace_back(x, y, z, stdDev);
        }
    }

    void PlaybackSimulation::LoadLogfileVersion2_6(serialization::BufferReader reader)
    {
        mode = Mode::Filaments;
        reader.Read(&config->environment.description);

        if (!simulationMetadata.source)
            simulationMetadata.source = std::make_shared<PointSource>();
        reader.Read(&simulationMetadata.constants);

        int windIndex;
        reader.Read(&windIndex, sizeof(int));
        config->windSequence.SetCurrentIndex(windIndex);

        activeFilaments.clear();
        int filament_index;
        float x, y, z, stdDev;
        while (!reader.Ended())
        {
            reader.Read(&filament_index, sizeof(int));
            reader.Read(&x, sizeof(float));
            reader.Read(&y, sizeof(float));
            reader.Read(&z, sizeof(float));
            reader.Read(&stdDev, sizeof(float));

            activeFilaments.emplace_back(x, y, z, stdDev);
        }
    }
} // namespace gaden
