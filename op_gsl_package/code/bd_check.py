depth = 0
with open("/tmp/orig_opgsl.cpp") as f:
    for line in f:
        for c in line:
            if c == "{": depth += 1
            if c == "}": depth -= 1
print("Original brace depth:", depth)
