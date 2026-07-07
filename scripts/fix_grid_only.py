with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'r') as f:
    c = f.read()
c = c.replace('posterior3d_.init(-7.5f, 3.9f, -7.9f, 0.82f', 'posterior3d_.init(-1.0f, 11.0f, -1.0f, 11.0f')
with open('/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp', 'w') as f:
    f.write(c)
print("Grid fix applied to original code")