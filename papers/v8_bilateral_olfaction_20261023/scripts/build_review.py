#!/usr/bin/env python3
"""Build the review PDF source from authored notes and item-level audit data."""
from pathlib import Path
import csv, json, subprocess, re

ROOT = Path(__file__).resolve().parents[1]
V = ROOT/'verification'

def esc(s):
    s = str(s)
    table = {'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
    return ''.join(table.get(c,c) for c in s)

def clean(s):
    return str(s).replace(r'\&','&').replace(r'{\"o}','ö').replace('{','').replace('}','')

def urlify(s):
    return ''.join(r'\url{'+x+'}' if x.startswith(('https://','http://')) else esc(x)
                   for x in re.split(r'(https?://[^\s；;|，]+)', str(s)))

def table_head(widths, headers):
    cols = '@{}'+''.join(r'>{\raggedright\arraybackslash}p{'+w+'}' for w in widths)+'@{}'
    heads = ' & '.join(esc(x) for x in headers)+r' \\'
    return '\n'.join([r'\begingroup\fontsize{9}{11.5}\selectfont\setlength{\parskip}{1pt}\setlength{\parindent}{0pt}',r'\begin{longtable}{'+cols+'}',r'\toprule',heads,r'\midrule',r'\endfirsthead',r'\toprule',heads,r'\midrule',r'\endhead',r'\bottomrule',r'\endfoot'])+'\n'

def table_end(): return '\\end{longtable}\n\\endgroup\n'

subprocess.run(['pandoc',str(V/'review_narrative.md'),'-f','markdown','-t','latex','--top-level-division=section','-o',str(V/'review_body.tex')],check=True)
subprocess.run(['pandoc',str(V/'KEY_UNPROVEN_CLAIMS.md'),'-f','markdown','-t','latex','-o',str(V/'unproven_body.tex')],check=True)
u = V/'unproven_body.tex'
u.write_text(re.sub(r'\\section\{[^}]+\}\n?', '', u.read_text(), count=1))
for p in [V/'review_body.tex',V/'unproven_body.tex']:
    s=p.read_text()
    s=re.sub(r'\\texttt\{([^{}]+)\}',lambda m:r'\nolinkurl{'+m.group(1).replace(r'\_','_')+'}',s)
    p.write_text(s)

parts=[]
parts.append(r'\clearpage\section{附录A：10篇团队论文的完整阅读与迁移索引}')
parts.append(r'已逐页读取全部10篇PDF，共123页，范围含方法、公式、实验、图表、结论与参考文献；T-ASE另含附录。完整学习笔记见随稿TEAM\_WRITING\_AUDIT.md。此处只列写作迁移对象，不将原文算法或成绩作为V8定位证据。')
parts.append(table_head(['1cm','7.0cm','7.4cm'],['编号/页数','原件题录与DOI','实际阅读重点及限制']))
for e in json.loads((V/'TEAM_PAPER_INDEX.json').read_text()):
    mid=esc(e['title'])+r'\par '+esc(f"{e['venue']}, {e['year']}. ")+r'\par DOI: \url{'+e['doi']+'}'
    last=esc(e['reading_focus'])+r'\par '+esc(e['caution'])
    parts.append(esc(e['id'])+r'\par '+str(e['pdf_pages'])+'页 & '+mid+' & '+last+r' \\\addlinespace[5pt]')
parts.append(table_end())

parts.append(r'\clearpage\section{附录B：正文29项参考文献逐条核验}')
parts.append(r'正文包含24项学术来源、4项冻结项目证据及1项官方作者指南。元数据确认、方法阅读与复现实验分级记录；没有读到的最终全文不标为全文阅读。完整字段及一级来源URL见CURRENT\_29\_REFERENCE\_REVIEW.csv。')
rows=list(csv.DictReader((V/'CURRENT_29_REFERENCE_REVIEW.csv').open(encoding='utf-8-sig')))
meta={str(x['citation_number']):x for x in json.loads((V/'CURRENT_REFERENCES.json').read_text())}
parts.append(table_head(['0.7cm','14.8cm'],['序号','题录、实际核验与论断范围']))
for idx,row in enumerate(rows,1):
    e=meta[str(idx)]
    content=r'\textbf{'+esc(clean(e['title']))+'}'+r'\par '+esc(clean(e.get('author','')))+'. '+esc(e['year'])+'. '
    if e.get('doi'): content+=r'DOI: \url{'+e['doi']+'}. '
    content+=r'\par\textbf{类别/核验：} '+esc(row['category']+'；'+row['verification_level']+'；'+row['verified_metadata'])
    loc=re.sub(r'（sections/.*?）','',row['manuscript_locations'])
    content+=r'\par\textbf{引用位置：} '+esc(loc)
    for key,label in [('reading_depth','实际阅读'),('allowed_claims','论据范围'),('pending_limits','限制/待核')]:
        content+=r'\par\textbf{'+label+'：} '+esc(row[key])
    urls=re.findall(r'https?://[^\s；;|，]+',row['primary_source_urls'])
    content+=r'\par\textbf{一级来源：} '+ '；'.join(r'\href{'+u+'}{来源'+str(i+1)+'}' for i,u in enumerate(urls))
    parts.append(str(idx)+' & '+content+r' \\\addlinespace[6pt]')
parts.append(table_end())

parts.append(r'\clearpage\section{附录C：原稿35项参考文献的逐条处置}')
parts.append('以下编号为原稿引用键，保留旧身份以便回查。L1/L2等等级的具体含义见原始核验表。429只表示限流，404也不足以证明文献虚构。删去的支线文献不因此被判断为错误论文；本轮未全文阅读者均明确记录。正文最终是否保留以当前29项表为准。')
rows=list(csv.DictReader((V/'ORIGINAL_35_REFERENCE_REVIEW.csv').open(encoding='utf-8-sig')))
parts.append(table_head(['0.7cm','7.0cm','7.8cm'],['旧号','原始身份及核验层级','纠错、处置与未核事项']))
for r in rows:
    a=esc(r['原始著录'])+r'\par\textbf{核验层级：}'+esc(r['本轮核验层级'])+r'\par '+esc(r['实际阅读与核验范围'])
    b=r'\textbf{'+esc(r['V8建议处置'])+'} '+esc(r['保留或删除理由'])+r'\par '+esc(r['身份及DOI年份纠错'])+r'\par\textbf{未核：}'+esc(r['未完成核验项目'])
    parts.append(esc(r['原稿编号'])+' & '+a+' & '+b+r' \\\addlinespace[6pt]')
parts.append(table_end())

parts.append(r'\clearpage\section{附录D：待证明命题与禁止升级的表述}')
parts.append(r'\input{unproven_body.tex}')
parts.append(r'\clearpage\section{附录E：编译与交付核查记录}')
parts.append(r'\input{BUILD_QA.tex}')
(V/'review_appendices.tex').write_text('\n'.join(parts))

preamble=r'''% !TEX TS-program = xelatex
\documentclass[UTF8,fontset=fandol,11pt,a4paper]{ctexart}
\usepackage[margin=21mm,headheight=15pt]{geometry}
\usepackage{amsmath,amssymb,booktabs,longtable,array,calc,graphicx}
\usepackage{xurl,enumitem,fancyhdr}
\usepackage[unicode,hidelinks]{hyperref}
\input{../font_config.tex}
\hypersetup{pdftitle={V8研究稿重构与完整性审查},pdfauthor={},pdfsubject={证据、文献、修改与审稿视角核查}}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\small V8研究稿｜重构与完整性审查}
\fancyhead[R]{\small 2026-10-23}
\fancyfoot[C]{\small\thepage}
\setlength{\parskip}{4pt}\setlength{\parindent}{2em}
\setlength{\emergencystretch}{3em}
\setlist{nosep,leftmargin=2em}
\setlength{\LTpre}{7pt}\setlength{\LTpost}{9pt}
\renewcommand{\arraystretch}{1.13}
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
\setcounter{tocdepth}{1}
\setcounter{secnumdepth}{0}
\begin{document}
\input{review_body.tex}
\input{review_appendices.tex}
\end{document}
'''
(V/'V8_Review_and_Verification.tex').write_text(preamble)
print('Generated review source and complete audit appendices.')
