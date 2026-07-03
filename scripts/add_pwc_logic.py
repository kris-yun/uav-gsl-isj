# Add PWC correction to saveResultsToFile in PMFS_utils.cpp
path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFS_utils.cpp"
with open(path) as f:
    content = f.read()

# Find the location after HCE block and before error calculation
# The HCE block ends with "sourceLocation = hceEstimate;" followed by "}"
# Then the error calculation starts

pwc_block = """
        // PWC: Plume Wind Correction
        // Correct source estimate by shifting upwind from the plume peak
        if (pwcCorrector_ && pwcCorrector_->config().enabled)
        {
            // Get wind at source estimate location
            int src_i = gridMetadata.coordinatesToIndices(sourceLocation).x;
            int src_j = gridMetadata.coordinatesToIndices(sourceLocation).y;
            src_i = std::max(0, std::min((int)gridMetadata.dimensions.x - 1, src_i));
            src_j = std::max(0, std::min((int)gridMetadata.dimensions.y - 1, src_j));
            int src_idx = src_j * gridMetadata.dimensions.x + src_i;

            double wind_x = 0, wind_y = 0;
            if (src_idx >= 0 && src_idx < (int)estimatedWindVectors.size()) {
                wind_x = estimatedWindVectors[src_idx].x;
                wind_y = estimatedWindVectors[src_idx].y;
            }
            // Fallback to raw wind if GMRF not available
            if (std::abs(wind_x) < 1e-6 && std::abs(wind_y) < 1e-6) {
                wind_x = last_windSpeed * std::cos(last_windDirection);
                wind_y = last_windSpeed * std::sin(last_windDirection);
            }

            // Estimate plume spread from probability map variance
            double plume_spread = std::sqrt(variance);

            auto pwc_out = pwcCorrector_->correct(
                sourceLocation.x, sourceLocation.y,
                wind_x, wind_y, plume_spread);

            if (pwc_out.applied) {
                double pwcError = sqrt(pow(resultLogging.sourcePositionGT.x - pwc_out.corrected_x, 2) +
                                      pow(resultLogging.sourcePositionGT.y - pwc_out.corrected_y, 2));
                double origError = sqrt(pow(resultLogging.sourcePositionGT.x - sourceLocation.x, 2) +
                                       pow(resultLogging.sourcePositionGT.y - sourceLocation.y, 2));
                GSL_INFO("[PWC] ({:.2f},{:.2f})->({:.2f},{:.2f}) wind=({:.4f},{:.4f}) corr_dist={:.3f}m err: {:.3f}->{:.3f}",
                         sourceLocation.x, sourceLocation.y,
                         pwc_out.corrected_x, pwc_out.corrected_y,
                         wind_x, wind_y, pwc_out.correction_distance,
                         origError, pwcError);
                sourceLocation.x = pwc_out.corrected_x;
                sourceLocation.y = pwc_out.corrected_y;
            }
        }

"""

# Find the error calculation line
error_marker = '        double error = sqrt(pow(resultLogging.sourcePositionGT.x - sourceLocation.x, 2)'

if error_marker in content and "[PWC]" not in content:
    content = content.replace(error_marker, pwc_block + error_marker)
    with open(path, 'w') as f:
        f.write(content)
    print("OK: Added PWC to saveResultsToFile")
else:
    if "[PWC]" in content:
        print("PWC already in saveResultsToFile")
    else:
        print("ERROR: Could not find error calculation marker")
