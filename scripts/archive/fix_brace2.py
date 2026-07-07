filepath = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(filepath) as f:
    content = f.read()

# Insert closing brace for sdnbvStep before computeEIGField
old = "    }\n\nvoid OPGSL::computeEIGField()"
new = "    }\n}\n\nvoid OPGSL::computeEIGField()"
content = content.replace(old, new, 1)

with open(filepath, "w") as f:
    f.write(content)
print("FIX SUCCESS")
