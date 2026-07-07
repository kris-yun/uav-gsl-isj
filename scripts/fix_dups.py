f = '/home/zyc/gsl_ws/install/vgr_bridge/share/vgr_bridge/launch/vgr_edpa_full.launch.py'
with open(f) as fh:
    lines = fh.readlines()

# Remove duplicate old lines (keep only the first occurrence of each param)
seen = set()
new_lines = []
for line in lines:
    stripped = line.strip()
    if 'opgsl.edpa.lambda0' in stripped or 'opgsl.edpa.ell' in stripped or 'opgsl.edpa.alphaw' in stripped:
        key = stripped.split(':')[0].strip().strip('"')
        if key not in seen:
            seen.add(key)
            new_lines.append(line)
        else:
            continue  # skip duplicate
    else:
        new_lines.append(line)

with open(f, 'w') as fh:
    fh.writelines(new_lines)
print('Removed duplicate parameters')
