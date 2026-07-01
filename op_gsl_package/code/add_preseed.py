# Add GP pre-seeding with calibration data
CPP = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(CPP, "r") as f:
    lines = f.readlines()

# Find line 178: "if (use_gp_altitude_) gp_.reset(best_calibrated_z_, z_min_, z_max_);"
for i, line in enumerate(lines):
    if "gp_.reset(best_calibrated_z_" in line:
        # Add pre-seeding after this line
        insert_lines = [
            "        // Pre-seed GP with calibration observations for faster convergence\n",
            "        for (const auto& lp : layer_profile_) {\n",
            "            if (lp.concentration > 0.01f) {\n",
            "                gp_.addObs(lp.z, lp.concentration);\n",
            "            }\n",
            "        }\n",
        ]
        for j, insert_line in enumerate(insert_lines):
            lines.insert(i + 1 + j, insert_line)
        print(f"CPP: Added GP pre-seeding after line {i+1}")
        break

with open(CPP, "w") as f:
    f.writelines(lines)
print("Done")
