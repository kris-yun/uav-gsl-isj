path = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp'
with open(path, 'r') as f:
    lines = f.readlines()

# Fix lines 234-241: the plumeLogLikelihood declaration was broken by the insert
# Current broken state:
# 234: float plumeLogLikelihood(float sx, float sy, float sz,
# 235: bool use_event_driven_ = false;
# 236: float detection_threshold_ = 0.01f;
# 237: float arrival_rate_lambda0_ = 2.0f;
# 238: float arrival_rate_ell_ = 3.0f;
# 239: float arrival_rate_alphaw_ = 0.5f;
# 240: float cx, float cy, float cz,
# 241: float wind_x, float wind_y, float wind_speed) const;

# Find and replace this broken section
for i, line in enumerate(lines):
    if 'float plumeLogLikelihood(float sx, float sy, float sz,' in line and i > 200:
        # Check if next line is NOT a proper continuation
        if i+1 < len(lines) and 'bool use_event_driven_' in lines[i+1]:
            # Replace lines i through i+7 with correct structure
            replacement = [
                '        bool use_event_driven_ = false;\n',
                '        float detection_threshold_ = 0.01f;\n',
                '        float arrival_rate_lambda0_ = 2.0f;\n',
                '        float arrival_rate_ell_ = 3.0f;\n',
                '        float arrival_rate_alphaw_ = 0.5f;\n',
                '        float plumeLogLikelihood(float sx, float sy, float sz,\n',
                '                                  float cx, float cy, float cz,\n',
                '                                  float wind_x, float wind_y, float wind_speed) const;\n',
            ]
            # Remove the old broken lines (8 lines from i to i+7)
            del lines[i:i+8]
            # Insert replacement
            for j, repl in enumerate(replacement):
                lines.insert(i+j, repl)
            print(f'Fixed plumeLogLikelihood declaration at lines {i+1}-{i+8}')
            break

with open(path, 'w') as f:
    f.writelines(lines)
print('DONE')
