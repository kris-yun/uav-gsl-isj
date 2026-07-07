import re

path = "/tmp/batch_eprocess.sh"
with open(path, 'r') as f:
    content = f.read()

# Fix the EY extraction regex - handle 3-tuple (x,y,z) format
# Old: EY=$(echo "$LAST" | sed "s/.*,\([-0-9.]*\),[-0-9.]*)/\1/")
# New: EY=$(echo "$LAST" | sed "s/.*,\([-0-9.]*\),[-0-9.]*).*/\1/")
content = content.replace(
    'EY=$(echo "$LAST" | sed "s/.*,' + '\\([-0-9.]*\\)' + ',[-0-9.]*)/\\1/")',
    'EY=$(echo "$LAST" | sed "s/.*,' + '\\([-0-9.]*\\)' + ',[-0-9.]*).*/\\1/")'
)

with open(path, 'w') as f:
    f.write(content)
print("Fixed EY extraction in batch script")