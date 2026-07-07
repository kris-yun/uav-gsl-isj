filepath = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp'
with open(filepath, 'r') as f:
    content = f.read()

old = '''    arrival_rate_alphaw_ = getParam<float>("opgsl.edpa.alphaw", 0.5f);
    use_upwind_tracking_ = getParam<bool>("opgsl.modules.upwind_tracking", true);'''

new = '''    arrival_rate_alphaw_ = getParam<float>("opgsl.edpa.alphaw", 0.5f);
    cr_stopping_.epsilon = getParam<float>("opgsl.edpa.stop_epsilon", 1.5f);
    cr_stopping_.delta = getParam<float>("opgsl.edpa.stop_delta", 0.10f);
    cr_stopping_.eta = getParam<float>("opgsl.edpa.stop_eta", 5.0f);
    cr_stopping_.warmup_steps = getParam<int>("opgsl.edpa.warmup_steps", 3);
    use_upwind_tracking_ = getParam<bool>("opgsl.modules.upwind_tracking", true);'''

if old in content:
    content = content.replace(old, new)
    with open(filepath, 'w') as f:
        f.write(content)
    print('Added EDPA stop parameter loading')
else:
    print('ERROR: pattern not found')
