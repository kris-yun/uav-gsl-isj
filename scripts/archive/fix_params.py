path = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp'
with open(path, 'r') as f:
    lines = f.readlines()

# Fix lines 78-85: change to posterior3d_.xxx
for i, line in enumerate(lines):
    if 'use_event_driven_ = getParam' in line and 'opgsl.event_driven' in line:
        lines[i] = line.replace('use_event_driven_', 'posterior3d_.use_event_driven_')
    elif 'detection_threshold_ = getParam' in line and 'opgsl.event_driven' in line:
        lines[i] = line.replace('detection_threshold_', 'posterior3d_.detection_threshold_')
    elif 'arrival_rate_lambda0_ = getParam' in line:
        lines[i] = line.replace('arrival_rate_lambda0_', 'posterior3d_.arrival_rate_lambda0_')
    elif 'arrival_rate_ell_ = getParam' in line:
        lines[i] = line.replace('arrival_rate_ell_', 'posterior3d_.arrival_rate_ell_')
    elif 'arrival_rate_alphaw_ = getParam' in line:
        lines[i] = line.replace('arrival_rate_alphaw_', 'posterior3d_.arrival_rate_alphaw_')

# Fix the GSL_INFO line: replace bare references with posterior3d_.
for i, line in enumerate(lines):
    if 'GSL_INFO' in line and 'Event-driven model' in line:
        lines[i] = '    GSL_INFO("Event-driven model: enabled={} lambda0={:.1f} ell={:.1f} alpha_w={:.2f} threshold={:.3f}",\n'
        lines[i+1] = '             posterior3d_.use_event_driven_, posterior3d_.arrival_rate_lambda0_, posterior3d_.arrival_rate_ell_, posterior3d_.arrival_rate_alphaw_, posterior3d_.detection_threshold_);\n'

with open(path, 'w') as f:
    f.writelines(lines)

print('DONE: Fixed parameter assignments to use posterior3d_.')
