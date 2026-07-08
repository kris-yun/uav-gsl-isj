import sys, re
sys.stdout.reconfigure(encoding='utf-8')

# Read all section files
sections_dir = r"D:\ZYC\A-gas\ASCi\sci\paper-isj-zh-cn\sections"
files_order = [
    "introduction.tex",
    "related_work.tex", 
    "system_model.tex",
    "methodology.tex",
    "theory.tex",
    "experiments.tex",
    "conclusion.tex",
    "algorithm.tex",
    "appendix_proofs.tex"
]

all_cites = []
seen = set()
for fname in files_order:
    path = f"{sections_dir}\\{fname}"
    try:
        with open(path, encoding='utf-8') as f:
            text = f.read()
        # Find all \cite{...} patterns
        for m in re.finditer(r'\\cite\{([^}]+)\}', text):
            keys = [k.strip() for k in m.group(1).split(',')]
            for k in keys:
                if k not in seen:
                    seen.add(k)
                    all_cites.append(k)
                    print(f"  [{len(all_cites):2d}] {k}  (from {fname})")
    except FileNotFoundError:
        print(f"  SKIP: {fname} not found")

print(f"\nTotal unique references: {len(all_cites)}")
print("\nOrdered list:")
for i, k in enumerate(all_cites, 1):
    print(f"  [{i}] {k}")
