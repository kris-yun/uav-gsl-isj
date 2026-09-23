#!/usr/bin/env python3
"""Stage a fresh VM gsl_server package with official PMFS plus passive wind audit.

The existing ROS workspace source and installed binary are never edited.
"""

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path


PMFS_REL = Path("src/gsl_server/algorithms/PMFS")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    if text.count(old) != 1:
        raise RuntimeError(f"expected one source anchor in {path}: {old[:90]!r}")
    path.write_text(text.replace(old, new), newline="\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-package", type=Path, required=True)
    ap.add_argument("--official-pmfs", type=Path, required=True)
    ap.add_argument("--fingerprints", type=Path, required=True)
    ap.add_argument("--output-package", type=Path, required=True)
    args = ap.parse_args()
    base, official, output = (p.resolve() for p in (args.base_package, args.official_pmfs, args.output_package))
    if output.exists() or output == base or base in output.parents:
        raise RuntimeError("output must be a new package directory outside the base source tree")
    if not (base / "package.xml").is_file() or not (official / "PMFSLib.cpp").is_file():
        raise RuntimeError("base gsl_server package or official PMFS source is missing")

    expected = {}
    with args.fingerprints.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            prefix = "gsl_server/src/gsl_server/algorithms/PMFS/"
            if row["relative_path"].startswith(prefix):
                expected[row["relative_path"][len(prefix):]] = row["archive_sha256"]
    for relative, sha in expected.items():
        path = official / relative
        if not path.is_file() or digest(path) != sha:
            raise RuntimeError(f"official ZIP fingerprint mismatch: {path}")
    if not expected:
        raise RuntimeError("no official PMFS fingerprints")

    shutil.copytree(base, output)
    target = output / PMFS_REL
    if target.resolve().is_relative_to(output) is False:
        raise RuntimeError("PMFS target escaped fresh staging directory")
    shutil.rmtree(target)
    shutil.copytree(official, target)
    cmake = output / "CMakeLists.txt"
    cmake_text = cmake.read_text()
    if "set(USE_GADEN OFF)" in cmake_text:
        cmake_text = cmake_text.replace("set(USE_GADEN OFF)", "set(USE_GADEN ON)", 1)
    if "set(USE_GADEN ON)" not in cmake_text:
        raise RuntimeError("USE_GADEN ON was not established in isolated package")
    if "set(USE_GUI ON)" in cmake_text:
        cmake_text = cmake_text.replace("set(USE_GUI ON)", "set(USE_GUI OFF)", 1)
    # Keep only the common library and official PMFS target in the recovery
    # binary. This excludes historical experimental algorithm registrations.
    disabled = ("PlumeTracking", "Spiral", "ParticleFilter", "GrGSL",
                "OPGSL", "OPGSLScientificV31", "OPGSLSCIMV1")
    for algorithm in disabled:
        include = f"include(src/gsl_server/algorithms/{algorithm}/CMakeLists.txt)"
        if include in cmake_text:
            cmake_text = cmake_text.replace(include, "# native recovery disabled: " + include, 1)
    if "include(src/gsl_server/algorithms/PMFS/CMakeLists.txt)" not in cmake_text:
        raise RuntimeError("PMFS target missing from isolated package")
    cmake.write_text(cmake_text, newline="\n")
    server = output / "src/gsl_server/gsl_server.cpp"
    replace_once(server, '    auto scim = std::dynamic_pointer_cast<GSL::OPGSLSCIMV1>(algorithm);\n', '')
    replace_once(server, '            if (scim) scim->forceSimulationTimeBudgetReached();\n', '')

    lib = target / "PMFSLib.cpp"
    replace_once(lib, '#include <gsl_server/algorithms/PMFS/PMFSLib.hpp>',
                 '#include <gsl_server/algorithms/PMFS/PMFSLib.hpp>\n'
                 '#include <chrono>\n#include <cmath>\n#include <cstdlib>\n#include <filesystem>\n'
                 '#include <fstream>\n#include <iomanip>\n#include <stdexcept>')
    replace_once(lib,
                 '        // if not compiled with gaden support, you have no choice but to use GMRF :)\n#ifdef USE_GADEN\n        if (!useGroundTruth)',
                 '        // Recovery is fail-closed: a non-GADEN request cannot become a Native run.\n'
                 '#ifndef USE_GADEN\n        throw std::runtime_error("NATIVE_RECOVERY_USE_GADEN_NOT_COMPILED");\n'
                 '#else\n        if (!useGroundTruth)\n'
                 '            throw std::runtime_error("NATIVE_RECOVERY_GROUND_TRUTH_NOT_REQUESTED");\n'
                 '#endif\n#ifdef USE_GADEN\n        if (!useGroundTruth)')
    old_branch = '''            auto future = groundTruth.client->async_send_request(groundTruth.request);
            auto result = rclcpp::spin_until_future_complete(node, future, std::chrono::seconds(5));
            if (result == rclcpp::FutureReturnCode::SUCCESS)
            {
                auto response = future.get();
                for (int ind = 0; ind < groundTruth.request->x.size(); ind++)
                {
                    Vector2Int pair = estimatedWind.metadata.coordinatesToIndices(groundTruth.request->x[ind], groundTruth.request->y[ind]);
                    estimatedWind.dataAt(pair.x, pair.y) = Vector2(response->u[ind], response->v[ind]);
                }
            }
            else
                GSL_WARN("CANNOT READ ESTIMATED WIND VECTORS");'''
    new_branch = '''            if (!groundTruth.client->wait_for_service(std::chrono::seconds(5)))
                throw std::runtime_error("NATIVE_RECOVERY_WIND_SERVICE_UNAVAILABLE");
            auto future = groundTruth.client->async_send_request(groundTruth.request);
            auto result = rclcpp::spin_until_future_complete(node, future, std::chrono::seconds(5));
            if (result != rclcpp::FutureReturnCode::SUCCESS)
                throw std::runtime_error("NATIVE_RECOVERY_WIND_QUERY_FAILED");
            auto response = future.get();
            const auto count = groundTruth.request->x.size();
            if (count == 0 || response->u.size() != count || response->v.size() != count)
                throw std::runtime_error("NATIVE_RECOVERY_WIND_RESPONSE_SHAPE_MISMATCH");
            const char* auditPath = std::getenv("NATIVE_RECOVERY_WIND_QUERY_CSV");
            if (!auditPath || !*auditPath)
                throw std::runtime_error("NATIVE_RECOVERY_WIND_AUDIT_PATH_MISSING");
            const bool writeHeader = !std::filesystem::exists(auditPath) || std::filesystem::file_size(auditPath) == 0;
            std::ofstream audit(auditPath, std::ios::app);
            if (!audit) throw std::runtime_error("NATIVE_RECOVERY_WIND_AUDIT_OPEN_FAILED");
            if (writeHeader) audit << "steady_ns,query_id,cell_index,x,y,service_u,service_v,internal_u,internal_v\\n";
            audit << std::setprecision(17);
            static unsigned long long queryId = 0;
            ++queryId;
            const auto steadyNs = std::chrono::duration_cast<std::chrono::nanoseconds>(
                std::chrono::steady_clock::now().time_since_epoch()).count();
            for (size_t ind = 0; ind < count; ++ind)
            {
                const double u = response->u[ind], v = response->v[ind];
                if (!std::isfinite(u) || !std::isfinite(v))
                    throw std::runtime_error("NATIVE_RECOVERY_WIND_NONFINITE");
                Vector2Int pair = estimatedWind.metadata.coordinatesToIndices(
                    groundTruth.request->x[ind], groundTruth.request->y[ind]);
                estimatedWind.dataAt(pair.x, pair.y) = Vector2(u, v);
                const Vector2 internal = estimatedWind.dataAt(pair.x, pair.y);
                const auto cellIndex = estimatedWind.metadata.indexOf(pair);
                audit << steadyNs << ',' << queryId << ',' << cellIndex << ','
                      << groundTruth.request->x[ind] << ',' << groundTruth.request->y[ind] << ','
                      << u << ',' << v << ',' << internal.x << ',' << internal.y << '\\n';
            }
            audit.flush();
            if (!audit) throw std::runtime_error("NATIVE_RECOVERY_WIND_AUDIT_WRITE_FAILED");
            GSL_INFO("NATIVE_RECOVERY_WIND_PATH=GADEN_GROUND_TRUTH QUERY_SUCCESS={} FALLBACK=0", queryId);'''
    replace_once(lib, old_branch, new_branch)

    pmfs = target / "PMFS.cpp"
    replace_once(pmfs, '#include <gsl_server/algorithms/PMFS/PMFS.hpp>',
                 '#include <gsl_server/algorithms/PMFS/PMFS.hpp>\n'
                 '#include <chrono>\n#include <cstdlib>\n#include <filesystem>\n#include <fstream>\n#include <iomanip>\n#include <stdexcept>')
    replace_once(pmfs, '        static int number_of_updates = 0;\n\n        // Update the gas presence map',
                 '''        static int number_of_updates = 0;
        const char* eventPath = std::getenv("NATIVE_RECOVERY_MEASUREMENT_EVENTS_CSV");
        if (!eventPath || !*eventPath)
            throw std::runtime_error("NATIVE_RECOVERY_MEASUREMENT_AUDIT_PATH_MISSING");
        const bool writeHeader = !std::filesystem::exists(eventPath) || std::filesystem::file_size(eventPath) == 0;
        std::ofstream eventAudit(eventPath, std::ios::app);
        if (!eventAudit) throw std::runtime_error("NATIVE_RECOVERY_MEASUREMENT_AUDIT_OPEN_FAILED");
        if (writeHeader) eventAudit << "steady_ns,event_id,hit,concentration,wind_speed,wind_direction,robot_i,robot_j,robot_x,robot_y\\n";
        static unsigned long long eventId = 0;
        ++eventId;
        const auto steadyNs = std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::steady_clock::now().time_since_epoch()).count();
        const auto robotCell = gridMetadata.coordinatesToIndices(currentRobotPosition);
        eventAudit << std::setprecision(17) << steadyNs << ',' << eventId << ','
                   << (concentration > thresholdGas ? 1 : 0)
                   << ',' << concentration << ',' << windSpeed << ',' << windDirection << ','
                   << robotCell.x << ',' << robotCell.y << ',' << currentRobotPosition.x << ','
                   << currentRobotPosition.y << '\\n';
        eventAudit.flush();
        if (!eventAudit) throw std::runtime_error("NATIVE_RECOVERY_MEASUREMENT_AUDIT_WRITE_FAILED");

        // Update the gas presence map''')

    sims = target / "internal/Simulations.cpp"
    replace_once(sims, '#include <gsl_server/algorithms/PMFS/internal/Simulations.hpp>',
                 '#include <gsl_server/algorithms/PMFS/internal/Simulations.hpp>\n'
                 '#include <chrono>\n#include <cmath>\n#include <cstdlib>\n#include <filesystem>\n'
                 '#include <fstream>\n#include <iomanip>\n#include <stdexcept>')
    replace_once(sims, '        Utils::Time::Stopwatch stopwatch;\n        std::vector<NQA::Node> localCopyLeaves = QTleaves;',
                 '''        Utils::Time::Stopwatch stopwatch;
        const char* auditPath = std::getenv("NATIVE_RECOVERY_WIND_UPDATE_CSV");
        if (!auditPath || !*auditPath)
            throw std::runtime_error("NATIVE_RECOVERY_SOURCE_UPDATE_AUDIT_PATH_MISSING");
        const bool writeHeader = !std::filesystem::exists(auditPath) || std::filesystem::file_size(auditPath) == 0;
        std::ofstream windAudit(auditPath, std::ios::app);
        if (!windAudit) throw std::runtime_error("NATIVE_RECOVERY_SOURCE_UPDATE_AUDIT_OPEN_FAILED");
        if (writeHeader) windAudit << "steady_ns,source_update_id,cell_index,x,y,internal_u,internal_v,magnitude\\n";
        windAudit << std::setprecision(17);
        static unsigned long long sourceUpdateId = 0;
        ++sourceUpdateId;
        const auto steadyNs = std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::steady_clock::now().time_since_epoch()).count();
        for (size_t i = 0; i < wind.data.size(); ++i)
        {
            if (wind.occupancy[i] != Occupancy::Free) continue;
            const auto coords = wind.metadata.indexToCoordinates(i);
            const auto vector = wind.data[i];
            const double magnitude = std::hypot(vector.x, vector.y);
            if (!std::isfinite(magnitude)) throw std::runtime_error("NATIVE_RECOVERY_INTERNAL_WIND_NONFINITE");
            windAudit << steadyNs << ',' << sourceUpdateId << ',' << i << ','
                      << coords.x << ',' << coords.y << ',' << vector.x << ',' << vector.y << ','
                      << magnitude << '\\n';
        }
        windAudit.flush();
        if (!windAudit) throw std::runtime_error("NATIVE_RECOVERY_SOURCE_UPDATE_AUDIT_WRITE_FAILED");
        GSL_INFO("NATIVE_RECOVERY_SOURCE_UPDATE_WIND_EXPORTED={}", sourceUpdateId);
        const char* measuredPath = std::getenv("NATIVE_RECOVERY_MEASURED_MAP_CSV");
        const char* candidatesPath = std::getenv("NATIVE_RECOVERY_CANDIDATES_CSV");
        if (!measuredPath || !*measuredPath || !candidatesPath || !*candidatesPath)
            throw std::runtime_error("NATIVE_RECOVERY_SNAPSHOT_PATH_MISSING");
        const bool measuredHeader = !std::filesystem::exists(measuredPath) || std::filesystem::file_size(measuredPath) == 0;
        std::ofstream measuredAudit(measuredPath, std::ios::app);
        if (!measuredAudit) throw std::runtime_error("NATIVE_RECOVERY_MEASURED_MAP_OPEN_FAILED");
        if (measuredHeader) measuredAudit << "source_update_id,cell_index,grid_i,grid_j,x,y,occupancy,probability,log_odds,confidence,omega,distance_from_robot,propagation_x,propagation_y,grid_width,grid_height,cell_size,origin_x,origin_y\\n";
        measuredAudit << std::setprecision(17);
        for (size_t i = 0; i < measuredHitProb.data.size(); ++i)
        {
            const auto coords = measuredHitProb.metadata.indexToCoordinates(i);
            const auto cell = measuredHitProb.metadata.indices2D(i);
            auto& hit = measuredHitProb.data[i];
            measuredAudit << sourceUpdateId << ',' << i << ',' << cell.x << ',' << cell.y << ','
                          << coords.x << ',' << coords.y << ','
                          << (measuredHitProb.occupancy[i] == Occupancy::Free ? "Free" : "Obstacle") << ','
                          << hit.probability() << ',' << hit.logOdds << ',' << hit.confidence << ','
                          << hit.omega << ',' << hit.distanceFromRobot << ','
                          << hit.originalPropagationDirection.x << ',' << hit.originalPropagationDirection.y << ','
                          << measuredHitProb.metadata.dimensions.x << ',' << measuredHitProb.metadata.dimensions.y << ','
                          << measuredHitProb.metadata.cellSize << ',' << measuredHitProb.metadata.origin.x << ','
                          << measuredHitProb.metadata.origin.y << '\\n';
        }
        measuredAudit.flush();
        if (!measuredAudit) throw std::runtime_error("NATIVE_RECOVERY_MEASURED_MAP_WRITE_FAILED");
        const bool candidateHeader = !std::filesystem::exists(candidatesPath) || std::filesystem::file_size(candidatesPath) == 0;
        std::ofstream candidateAudit(candidatesPath, std::ios::app);
        if (!candidateAudit) throw std::runtime_error("NATIVE_RECOVERY_CANDIDATES_OPEN_FAILED");
        if (candidateHeader) candidateAudit << "source_update_id,candidate_id,origin_i,origin_j,size_i,size_j,center_x,center_y\\n";
        candidateAudit << std::setprecision(17);
        for (const auto& leaf : QTleaves)
        {
            if (leaf.value != 1) continue;
            const double centerX = measuredHitProb.metadata.origin.x +
                (leaf.origin.x + leaf.size.x * 0.5) * measuredHitProb.metadata.cellSize;
            const double centerY = measuredHitProb.metadata.origin.y +
                (leaf.origin.y + leaf.size.y * 0.5) * measuredHitProb.metadata.cellSize;
            candidateAudit << sourceUpdateId << ",quadtree_" << leaf.origin.x << '_' << leaf.origin.y
                           << '_' << leaf.size.x << '_' << leaf.size.y << ','
                           << leaf.origin.x << ',' << leaf.origin.y << ',' << leaf.size.x << ','
                           << leaf.size.y << ',' << centerX << ',' << centerY << '\\n';
        }
        candidateAudit.flush();
        if (!candidateAudit) throw std::runtime_error("NATIVE_RECOVERY_CANDIDATES_WRITE_FAILED");
        std::vector<NQA::Node> localCopyLeaves = QTleaves;''')
    replace_once(sims, '        GSL_INFO("Time ellapsed in simulation = {} s", stopwatch.ellapsed());',
                 '''        GSL_INFO("Time ellapsed in simulation = {} s", stopwatch.ellapsed());
        const char* completePath = std::getenv("NATIVE_RECOVERY_UPDATE_COMPLETE_FILE");
        if (!completePath || !*completePath)
            throw std::runtime_error("NATIVE_RECOVERY_UPDATE_COMPLETE_PATH_MISSING");
        std::ofstream complete(completePath, std::ios::app);
        if (!complete) throw std::runtime_error("NATIVE_RECOVERY_UPDATE_COMPLETE_OPEN_FAILED");
        complete << sourceUpdateId << '\\n';
        complete.flush();
        if (!complete) throw std::runtime_error("NATIVE_RECOVERY_UPDATE_COMPLETE_WRITE_FAILED");
        GSL_INFO("NATIVE_RECOVERY_SOURCE_UPDATE_COMPLETE={}", sourceUpdateId);''')

    manifest = {"contract": "NATIVE_PMFS_RECOVERY_SOURCE_V1", "base_package": str(base),
                "official_pmfs": str(official), "output_package": str(output),
                "official_pmfs_files_verified": len(expected),
                "pmfs_lib_sha256": digest(lib), "pmfs_sha256": digest(pmfs),
                "simulations_sha256": digest(sims),
                "cmake_sha256": digest(cmake), "server_sha256": digest(server),
                "use_gaden": True, "use_gui": False,
                "enabled_algorithms": ["PMFS"],
                "instrumentation": "Fail-closed ground-truth wind query and read-only query/update, measurement, map, and candidate CSV"}
    (output.parent / "source_stage_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
