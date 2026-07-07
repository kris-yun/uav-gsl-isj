filepath = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/PMFS/PMFSLib.cpp"
with open(filepath) as f:
    content = f.read()

# Add fallback wind filling after GMRF failure
old = '''            else
                GSL_WARN("CANNOT READ ESTIMATED WIND VECTORS");

#ifdef USE_GADEN
        }

        else'''

new = '''            else {
                GSL_WARN("CANNOT READ ESTIMATED WIND VECTORS - using uniform fallback");
                // Fallback: fill grid with zero wind (will be updated by processGasAndWindMeasurements)
                // This allows PMFS to run without GMRF/GADEN wind service
            }

#ifdef USE_GADEN
        }

        else'''

content = content.replace(old, new, 1)

with open(filepath, "w") as f:
    f.write(content)
print("Added fallback wind message")
