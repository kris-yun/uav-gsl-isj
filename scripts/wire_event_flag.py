# Fix: pass event_driven flag as parameter to update()
filepath = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp'
with open(filepath, 'r') as f:
    content = f.read()

# Change function signature
old_sig = 'void OPGSL::SourcePosterior3D::update(float cx, float cy, float cz, float concentration,\n                                       float wind_x, float wind_y, float wind_speed) {'
new_sig = 'void OPGSL::SourcePosterior3D::update(float cx, float cy, float cz, float concentration,\n                                       float wind_x, float wind_y, float wind_speed, bool use_event_driven) {'
content = content.replace(old_sig, new_sig)

# Remove the hardcoded flag
content = content.replace('    bool use_event_driven = true;  // TODO: make this a parameter\n', '')

with open(filepath, 'w') as f:
    f.write(content)

# Update header
hpath = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp'
with open(hpath, 'r') as f:
    hcontent = f.read()
old_hsig = 'void update(float cx, float cy, float cz, float concentration,\n                                     float wind_x, float wind_y, float wind_speed);'
new_hsig = 'void update(float cx, float cy, float cz, float concentration,\n                                     float wind_x, float wind_y, float wind_speed, bool use_event_driven = false);'
hcontent = hcontent.replace(old_hsig, new_hsig)
with open(hpath, 'w') as f:
    f.write(hcontent)

# Update all call sites to pass use_event_driven_posterior_
# Find all calls to posterior3d_.update(
import re
calls = list(re.finditer(r'posterior3d_\.update\([^)]+\)', content))
for call in calls:
    old_call = call.group()
    if 'use_event_driven' not in old_call:
        new_call = old_call.rstrip(')') + ', use_event_driven_posterior_)'
        content = content.replace(old_call, new_call, 1)

with open(filepath, 'w') as f:
    f.write(content)

print(f'Updated function signature and {len(calls)} call sites')
