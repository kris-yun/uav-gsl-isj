#pragma once
#include "gaden/core/Assertions.hpp"
#include <algorithm>
#include <filesystem>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace gaden::paths
{
    inline void TryCreateDirectory(std::filesystem::path const& path)
    {
        if (!std::filesystem::exists(path))
        {
            if (!std::filesystem::create_directories(path))
            {
                GADEN_WARN("Cannot create directory '{}'", path);
                GADEN_TERMINATE;
            }
        }
    }

    inline std::vector<std::filesystem::path> AsPaths(const std::vector<std::string>& strs)
    {
        std::vector<std::filesystem::path> paths;
        paths.reserve(strs.size());
        for (const auto& str : strs)
            paths.emplace_back(str);
        return paths;
    }

    inline std::vector<std::filesystem::path> GetAllFilesInDirectory(std::filesystem::path const& directory)
    {
        std::vector<std::filesystem::path> files;
        if (std::filesystem::exists(directory))
            for (const auto& file : std::filesystem::directory_iterator(directory))
                files.push_back(file);

        // Wind files are named wind_iteration_<integer>.  Filesystem iteration
        // order is not a time order, and lexical sorting would put 10 before 2.
        // Keep the generic fallback deterministic while sorting this numeric
        // sequence by its actual iteration index.
        const auto windIndex = [](const std::filesystem::path& path) -> std::optional<unsigned long long>
        {
            const auto name = path.filename().string();
            constexpr std::string_view prefix = "wind_iteration_";
            if (name.rfind(prefix, 0) != 0 || name.size() == prefix.size())
                return std::nullopt;
            try
            {
                size_t parsed = 0;
                const auto value = std::stoull(name.substr(prefix.size()), &parsed);
                if (parsed != name.size() - prefix.size())
                    return std::nullopt;
                return value;
            }
            catch (...)
            {
                return std::nullopt;
            }
        };

        std::sort(files.begin(), files.end(), [&](const auto& lhs, const auto& rhs)
        {
            const auto li = windIndex(lhs);
            const auto ri = windIndex(rhs);
            if (li && ri)
                return *li < *ri;
            if (li)
                return true;
            if (ri)
                return false;
            return lhs.string() < rhs.string();
        });
        return files;
    }

    inline std::filesystem::path MakeAbsolutePath(std::filesystem::path const& path, std::filesystem::path const& referencePoint)
    {
        if (!path.is_relative())
            return path;

        return referencePoint / path;
    }

    inline std::vector<std::filesystem::path> GetExternalWindFiles(std::string const& commonPath)
    {
        std::string filename = fmt::format("{}_{}.csv", commonPath, 0);
        if (!std::filesystem::exists(filename))
        {
            GADEN_WARN("Wind file '{}' does not exist", filename.c_str());
            return {};
        }

        size_t idx = 0;
        std::vector<std::filesystem::path> paths;
        for (; std::filesystem::exists(filename); filename = fmt::format("{}_{}.csv", commonPath, idx))
        {
            paths.emplace_back(filename);
            idx++;
        }
        return paths;
    }

    inline bool IsInContainedDirectory(std::filesystem::path const& path, std::filesystem::path const& directory)
    {
        std::filesystem::path p = path;
        while (p.has_parent_path() && p != p.root_path())
        {
            p = p.parent_path();
            if (p == directory)
                return true;
        }
        return false;
    }

    inline std::filesystem::path MakeRelativeIfInProject(std::filesystem::path const& path,
                                                         std::filesystem::path const& projectRoot,
                                                         std::filesystem::path const& relativeTo)
    {
        if (IsInContainedDirectory(path, projectRoot))
            return std::filesystem::relative(path, relativeTo);

        return path;
    }
} // namespace gaden::paths
