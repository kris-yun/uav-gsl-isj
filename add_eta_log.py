import re

path = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(path, "r") as fh:
    content = fh.read()

old = """        eta = std::clamp(std::pow(H_ratio, 1.5f), 0.05f, 1.0f);
    }
    float mx, my, mz; getMAP(mx, my, mz);"""

new = """        eta = std::clamp(std::pow(H_ratio, 1.5f), 0.05f, 1.0f);
    }
    GSL_INFO("ETA: H_ratio={:.3f} eta={:.3f} (fixed={:.1f})", H_ratio, eta, eta_fixed_);
    float mx, my, mz; getMAP(mx, my, mz);"""

if old in content:
    content = content.replace(old, new)
    with open(path, "w") as fh:
        fh.write(content)
    print("OK: eta logging added")
else:
    print("ERROR: block not found")
