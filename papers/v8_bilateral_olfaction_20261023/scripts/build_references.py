#!/usr/bin/env python3
"""Render the project's verified BibTeX records in first-citation order.

This small deterministic renderer supports the brace-valued records shipped
with this project. The .bib remains the editable bibliographic source.
"""
import re
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

def balanced(s, start):
    depth = 1
    pos = start + 1
    while depth:
        if s[pos] == '{' and s[pos-1] != '\\': depth += 1
        elif s[pos] == '}' and s[pos-1] != '\\': depth -= 1
        pos += 1
    return s[start+1:pos-1], pos

def parse(s):
    entries = {}
    pos = 0
    while True:
        m = re.search(r'@(\w+)\s*\{\s*([^,]+),', s[pos:])
        if not m: break
        base = pos + m.start()
        body, pos = balanced(s, s.index('{', base))
        key, fields = body.split(',', 1)
        item = {'type': m.group(1).lower(), 'key': key.strip()}
        k = 0
        while True:
            fm = re.search(r'(\w+)\s*=\s*\{', fields[k:])
            if not fm: break
            start = k + fm.end() - 1
            item[fm.group(1)] , k = balanced(fields, start)
        entries[item['key']] = item
    return entries

def names(s):
    result = []
    for a in s.split(' and '):
        if ',' not in a:
            result.append(a)
            continue
        family, given = a.split(',', 1)
        init = ' '.join(t[0] for t in re.split(r'[\s.-]+', given.strip()) if t)
        result.append(family + ' ' + init)
    return ', '.join(result)

def render(e):
    if 'formatted' in e: return e['formatted']
    out = names(e.get('author','')) + '. ' + e['title'] + '. '
    ty = e['type']
    if ty == 'book':
        out += r'{\sl ' + e['title'] + '}.' if not e.get('author') else ''
        out += e.get('edition','').rstrip('.') + '. ' + e.get('publisher','') + ', ' + e['year'] + '.'
        if 'isbn' in e: out += ' ISBN: ' + e['isbn'] + '.'
    elif ty == 'inproceedings':
        out += r'In: {\sl ' + e['booktitle'] + '}. IEEE, ' + e['year']
        if 'pages' in e: out += ': ' + e['pages']
        out += '.'
    elif 'journal' in e:
        out += r'{\sl ' + e['journal'] + '}, ' + e['year']
        if 'volume' in e: out += r', {\bf ' + e['volume'] + '}'
        if 'number' in e: out += '(' + e['number'] + ')'
        if 'pages' in e: out += ': ' + e['pages']
        out += '.'
    else:
        out += e['year'] + '.'
        if 'eprint' in e:
            out += ' arXiv:' + e['eprint'] + 'v1.'
    if e.get('doi'):
        out += r' DOI: \url{' + e['doi'] + '}.'
    elif e.get('url'):
        out += r' \url{' + e['url'] + '}.'
    return out

entries = parse((ROOT/'references.bib').read_text())
main = (ROOT/'main.tex').read_text()
for name in re.findall(r'\\input\{(sections/[^}]+)\}', main):
    main += '\n' + (ROOT/name).read_text()
order = []
for cite in re.findall(r'\\(?:ccite|cite)\{([^}]+)\}', main):
    for key in cite.split(','):
        if '#' in key: continue
        if key not in order: order.append(key)
missing = [key for key in order if key not in entries]
if missing: raise ValueError('Unresolved references: '+str(missing))
lines = [r'\begin{thebibliography}{99}', r'\small']
for key in order:
    lines += [r'\bibitem{'+key+'}', render(entries[key]), '']
lines += [r'\end{thebibliography}', '']
(ROOT/'references.tex').write_text('\n'.join(lines))
(ROOT/'verification'/'CURRENT_REFERENCES.json').write_text(json.dumps([dict(citation_number=i+1,**entries[k]) for i,k in enumerate(order)],ensure_ascii=False,indent=2))
print(f'Rendered {len(order)} references; all citation keys resolved.')
