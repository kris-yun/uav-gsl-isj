filepath = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/PMFS/PMFSLib.cpp"
with open(filepath) as f:
    content = f.read()

content = content.replace(
    'algorithm.getParam<bool>("useWindGroundTruth", false)',
    'algorithm.getParam<bool>("useWindGroundTruth", true)'
)

with open(filepath, "w") as f:
    f.write(content)
print("Changed useWindGroundTruth default to true")
