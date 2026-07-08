import sys, re, os, shutil
sys.stdout.reconfigure(encoding='utf-8')

sections_dir = r"D:\ZYC\A-gas\ASCi\sci\paper-isj-zh-cn\sections"
files_order = [
    "introduction.tex", "related_work.tex", "system_model.tex",
    "methodology.tex", "theory.tex", "experiments.tex",
    "conclusion.tex", "algorithm.tex", "appendix_proofs.tex"
]

# Step 1: Collect citation order
all_cites = []
seen = set()
for fname in files_order:
    path = os.path.join(sections_dir, fname)
    if not os.path.exists(path):
        continue
    with open(path, encoding='utf-8') as f:
        text = f.read()
    for m in re.finditer(r'\\cite\{([^}]+)\}', text):
        keys = [k.strip() for k in m.group(1).split(',')]
        for k in keys:
            if k not in seen:
                seen.add(k)
                all_cites.append(k)

# Build mapping: old_key -> new_number
key_to_num = {k: i+1 for i, k in enumerate(all_cites)}
print("Reference mapping:")
for k, n in key_to_num.items():
    print(f"  {k} -> [{n}]")

# Step 2: Replace citations in all files
for fname in files_order:
    path = os.path.join(sections_dir, fname)
    if not os.path.exists(path):
        continue
    with open(path, encoding='utf-8') as f:
        text = f.read()
    
    def replace_cite(m):
        keys = [k.strip() for k in m.group(1).split(',')]
        nums = sorted([key_to_num[k] for k in keys if k in key_to_num])
        return '\\cite{' + ','.join(str(n) for n in nums) + '}'
    
    new_text = re.sub(r'\\cite\{([^}]+)\}', replace_cite, text)
    if new_text != text:
        with open(path, encoding='utf-8') as f2:
            pass
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_text)
        print(f"Updated citations in {fname}")

print("\nDone: all citations renumbered")
