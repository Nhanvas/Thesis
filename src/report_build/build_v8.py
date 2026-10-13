#!/usr/bin/env python3
"""Build the v8 thesis report (.docx) from the chapter markdown files.

Inputs (paths below): chapter/appendix markdown (Notes sections are dropped), figures, the reference
sheet (full citations), the school Word template (title page, approval page, header logo, footers).
Steps: (1) per-file citation map [n] -> sheet code, renumbered globally by first appearance;
(2) one pandoc markdown with markers for captions and equation numbers; (3) pandoc -> docx with a
reference doc derived from the template; (4) lxml post-processing: captions with SEQ fields, numbered
equations, table borders/fonts/shading, title/approval pages, ToC/LoT/LoF fields, sections and margins.
Fails fast on any unmapped citation or missing figure file (unless declared a placeholder).
"""
import copy, hashlib, json, os, re, shutil, subprocess, sys, zipfile
from pathlib import Path
from lxml import etree
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(os.environ.get('THESIS_BUILD_ROOT', '/home/claude'))  # ROOT/work/{chapters,appendix}, ROOT/in/{Template.docx,figures}, ROOT/repo = clone
WORK = ROOT / 'work'
IN = ROOT / 'in'
REPO = ROOT / 'repo'
OUT = ROOT / 'build' / 'out'
TMP = ROOT / 'build' / 'tmp'
TEMPLATE = IN / 'Template.docx'
# chat 8 (13/10, author): margins of Report format.md and of the template's own text -- left 1.5 in, top, bottom
# and right 1 in (header/footer 0.5 in). Text block 6.0 in x 9.0 in; landscape pages 9.0 in x 6.0 in, the 1.5-in
# binding margin at the top of the landscape page (the binding edge).
TW = 1440  # twips per inch
MARGIN = {'left': 2160, 'right': 1440, 'top': 1440, 'bottom': 1440, 'header': 720, 'footer': 720}
TEXT_W_IN, LAND_W_IN = 6.0, 9.0
MAXH_IN = 7.6  # text height (9 in) minus room for the caption
# chat 8 (13/10, author): every table at 12 pt (no smaller table font), on portrait pages only (a table may run
# longer); no landscape pages. LANDSCAPE stays empty; the section code below is kept for reference only.
TABLE_PT = 12
FIG_MAXW = {4: 4.0}  # chat 8: the montage drawing (square) at 4.0 in instead of the full 6.0 in
LANDSCAPE = set()  # author 13/10: no landscape pages
SHEET = REPO / 'docs' / 'Thesis_Reference_Sheet.md'

FILES = [WORK / 'chapters/Front_matter_v8.md'] + [WORK / f'chapters/{n}' for n in (
    'Chapter_1_Introduction_v8.md', 'Chapter_2_Methodology_v8.md', 'Chapter_3_Results_v8.md',
    'Chapter_4_Discussion_v8.md', 'Chapter_5_Conclusion_v8.md')] + [WORK / 'appendix/Appendix_v8.md']

INH = Path(os.environ.get('INH_DIR', IN / 'figures_inherited'))  # Reports/v8/figures_inherited/ (11/10 draft drawings)
# chat 6 (13/10): 1, 2, 4, 5, 7 are byte-identical to the repository copies (sha256 41f2e2f0feb5, 016cd16dc409,
# c675eca4623d, af4cdb6563e3, b82ba6d507e0); 6 and 10 checked by eye: final system (per-channel Ledoit-Wolf,
# four members, drift correction, kernel CPD localizer; label guards of the application)
FIG = {
    1: INH / 'Fig01_seizure_phases.png', 2: INH / 'Fig02_connectivity.png',
    3: IN / 'figures/fig03_framework.png', 4: INH / 'Fig04_montage.png',
    5: INH / 'Fig05_preprocessing.png', 6: INH / 'Fig06_pipeline.png', 7: INH / 'Fig07_graph_construction.png',
    8: IN / 'figures/fig08_drift.png', 9: IN / 'figures/fig09_event_scoring.png', 10: INH / 'Fig10_architecture.png',
    11: IN / 'figures/fig11_sparsification.png', 12: IN / 'figures/fig12_duration.png',
    13: IN / 'figures/fig13_boundaries.png', 14: IN / 'figures/fig14_gallery.png', 15: 'COMPOSE',
    # chat 7 (13/10): the sensitivity-vs-false-alarm figure is dropped (Table 18 suffices); fig17 becomes Figure 16
    16: IN / 'figures/fig17_budget_needed.png',
}
if os.environ.get('FIG6'): FIG[6] = Path(os.environ['FIG6'])
if os.environ.get('FIG10'): FIG[10] = Path(os.environ['FIG10'])

NOTE_STARTS = ("Siena, 14 patients", "Seed 42; interval", "Mean over four seeds", "Pooled sensitivity at the best", "Seed 42", "Median absolute error",
               "Per-patient mean = ", "62 focal", "Application: label-free", "Values marked",
               "Hours listed:", "PhysioNet hours:", "Seizures in file order", "Laptop processor",
               "Total = total")

# ---------------------------------------------------------------- references
def sheet_rows():
    s = SHEET.read_text(encoding='utf8')
    s = s[s.index('## Full detail by group'):]
    rows = {}
    for line in s.splitlines():
        if not line.startswith('| '):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        code = cells[0].replace('*', '').strip()
        if re.fullmatch(r'[A-N]\d+', code) and len(cells) >= 3 and code not in rows:
            rows[code] = cells[1]
    return rows

OVERRIDE = {
    'I1': 'World Health Organization. *Epilepsy* [fact sheet]. Version of 7 February 2024.',
    'D4': 'Dan, J., Pale, U., Amirshahi, A., Cappelletti, W., Ingolfsson, T.M., Wang, X., Cossettini, A., '
          'Bernini, A., Benini, L., Beniczky, S., Atienza, D., Ryvlin, P. (2024). SzCORE: Seizure Community '
          'Open-Source Research Evaluation framework for the validation of electroencephalography-based '
          'automated seizure detection algorithms. *Epilepsia*, 66(S3), 14–24.',
    'K3': 'EPFL Embedded Systems Laboratory. SzCORE seizure detection benchmark, commit c57da2f '
          '(6 Sep 2026). Accessed 8 Oct 2026.',
    'K5': 'EPFL Embedded Systems Laboratory. epilepsy2bids: conversion of public seizure datasets to BIDS, '
          'commit d3fb175 (10 Apr 2026).',
    'N2': 'Xiao, T., Wang, Z., Zhang, Y., Lv, H., Wang, S., Feng, H., Zhao, Y. (2024). Self-supervised '
          'learning with attention mechanism for EEG-based seizure detection. *Biomedical Signal '
          'Processing and Control*, 87, 105464.',
    'N3': 'Hong, T., Li, D., Chang, Y., et al. (2025). MCAN: Cross-domain self-supervised attention network '
          'based on multiscale EEG feature learning for epileptic seizure detection. *Knowledge-Based '
          'Systems*, 327, 114199.',
    'N5': 'Dani, M., Liebe, S. (2026). Parameter-efficient self-supervised adaptation for EEG-FM under fixed '
          'computational budgets. In *Medical Image Computing and Computer Assisted Intervention – MICCAI '
          '2026*, Lecture Notes in Computer Science, 449–458. Springer, Cham.',
    'B11': 'Mazurek, S., Moore, S., Crimi, A. (2025). Graph attention networks for detecting epilepsy from '
           'EEG signals using accessible hardware in low-resource settings. *IEEE Open Journal of '
           'Engineering in Medicine and Biology*.',
    'E9': 'Tang, S., Dunnmon, J., Saab, K., Zhang, X., Huang, Q., Dubost, F., Rubin, D., Lee-Messer, C. '
          '(2022). Self-supervised graph neural networks for improved electroencephalographic seizure '
          'analysis. *International Conference on Learning Representations (ICLR 2022)*.',
    'E11': 'Ho, T.K.K., Armanfard, N. (2023). Self-supervised learning for anomalous channel detection in '
           'EEG graphs: application to seizure analysis. *Proceedings of the AAAI Conference on '
           'Artificial Intelligence (AAAI-23)*.',
    'E6': 'Kipf, T.N., Welling, M. (2016). Variational graph auto-encoders. NIPS 2016 Workshop on Bayesian '
          'Deep Learning.',
    'J4': 'American Clinical Neurophysiology Society (2006). Guideline 6: A proposal for standard montages '
          'to be used in clinical EEG.',
    'K6': 'Dan, J., Pale, U., Amirshahi, A., Cappelletti, W., Ingolfsson, T.M., Wang, X., Cossettini, A., '
          'Bernini, A., Benini, L., Beniczky, S., Atienza, D., Ryvlin, P. (2024). SzCORE: A Seizure Community '
          'Open-source Research Evaluation framework for the validation of EEG-based automated seizure '
          'detection algorithms. arXiv preprint.',
    'X3': 'Welch, P.D. (1967). The use of fast Fourier transform for the estimation of power spectra: a '
          'method based on time averaging over short, modified periodograms. *IEEE Transactions on Audio '
          'and Electroacoustics*, 15(2), 70–73.',
    'X4': 'Kipf, T.N., Welling, M. (2017). Semi-supervised classification with graph convolutional '
          'networks. *International Conference on Learning Representations (ICLR 2017)*.',
    'X5': 'Kingma, D.P., Ba, J. (2015). Adam: A method for stochastic optimization. *International '
          'Conference on Learning Representations (ICLR 2015)*.',
    'X10': 'Zhang, J., Bargal, S.A., Lin, Z., Brandt, J., Shen, X., Sclaroff, S. (2018). Top-down neural '
           'attention by excitation backprop. *International Journal of Computer Vision*, 126(10), '
           '1084–1102.',
}

def clean_cite(t):
    t = t.replace('**', '').replace('`', '')
    t = re.sub(r'\s*\(?arXiv:\d{4}\.\d{4,5}(v\d)?( \[[^\]]+\])?\)?\.?', '', t)
    t = re.sub(r'(\d)–\.', r'\1.', t)
    t = re.sub(r'\s+', ' ', t).strip()
    if not t.endswith('.'):
        t += '.'
    t = t.replace('..', '.')
    t = re.sub(r'\.\*\.$', '.*', t)
    return t

def ident(raw):
    raw = raw.strip()
    m = re.search(r'\b(10\.\d{4,9}/[^\s|]+)', raw)
    if raw.startswith('reprint') and m:
        return f'Reprint: https://doi.org/{m.group(1)}'
    if raw.startswith('10.') and m:
        return f'https://doi.org/{m.group(1)}'
    m = re.match(r'arXiv:(\S+)', raw)
    if m:
        return f'arXiv:{m.group(1)}'
    m = re.match(r'(URL|handle) (\S+)', raw)
    if m:
        return m.group(2)
    return ''

def notes_table(text):
    """Return {local n: (code, chapter-table reference, identifier)} from the Notes section."""
    out = {}
    if '# Notes' not in text:
        return out
    notes = text.split('# Notes', 1)[1]
    for line in notes.splitlines():
        m = re.match(r'\|\s*\[(\d+)\]\s*\|\s*([A-Z]\d+)\s*\|(.*)\|(.*)\|\s*$', line)
        if m:
            out[int(m.group(1))] = (m.group(2), m.group(3).strip(), m.group(4).strip())
    return out

# ---------------------------------------------------------------- figure 15
def compose_fig15(path):
    shots = [IN / 'figures/app_screens' / n for n in ('a_import.png', 'b_analysis.png', 'c_panel_review.png')]
    ims = [Image.open(p).convert('RGB') for p in shots]
    # chat 7 (13/10): 2 + 1 layout -- (a) and (b) side by side, (c) centred below, same size
    w, h = ims[0].size
    gap, lab = 40, 70
    W = 2 * w + gap
    H = 2 * (h + lab) + gap
    canvas = Image.new('RGB', (W, H), 'white')
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf', 48)
    except OSError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(canvas)
    pos = [(0, 0), (w + gap, 0), ((W - w) // 2, h + lab + gap)]
    for im, l, (x, y) in zip(ims, 'abc', pos):
        d.text((x + 4, y + 10), f'({l})', fill='black', font=font)
        canvas.paste(im.resize((w, h)), (x, y + lab))
    canvas.save(path)
    return path

# ---------------------------------------------------------------- markdown assembly
_FONTS = {}
def text_w_in(s, pt, bold=False):
    """Width in inches of s in Times New Roman (Liberation Serif is metric-compatible)."""
    k = 'B' if bold else 'R'
    if k not in _FONTS:
        _FONTS[k] = ImageFont.truetype(f'/usr/share/fonts/truetype/liberation/LiberationSerif-{"Bold" if bold else "Regular"}.ttf', 120)
    return _FONTS[k].getlength(s) / 120 * pt / 72

def pieces(word):
    """Line-break points of a word: after each hyphen (Word and LibreOffice break there)."""
    return [x for x in re.split(r'(?<=-)', word) if x]

CELL_PAD_IN = 0.13  # left + right cell margins (70 twips each = 0.097 in) plus rounding

def col_widths_pt(rows, avail_in, pt=TABLE_PT):
    """Column widths for a table set at pt in avail_in inches (auto layout as in HTML tables): every column
    gets at least its longest word, and the remaining width goes to columns in proportion to how much
    their longest cell exceeds that minimum. Returns (widths, fits_without_breaking_words)."""
    n = len(rows[0])
    mins, nats = [], []
    for j in range(n):
        mn = nt = 0.0
        for k, r in enumerate(rows):
            c = r[j] if j < len(r) else ''
            bold = k == 0 or c.startswith('**')
            c = c.replace('**', '').replace('`', '')
            words = [pc for w in c.split() for pc in pieces(w)] or ['']
            mn = max(mn, max(text_w_in(w, pt, bold) for w in words))
            nt = max(nt, text_w_in(c, pt, bold))
        mins.append(mn + CELL_PAD_IN); nats.append(nt + CELL_PAD_IN)
    if sum(nats) <= avail_in:
        return [w * avail_in / sum(nats) for w in nats], True
    if sum(mins) > avail_in:
        return [w * avail_in / sum(mins) for w in mins], False
    # widths that minimise the table height (row height = its tallest cell): start at the minimum widths;
    # at each step widen the column whose widening (looking up to 2 in ahead) removes the most rows of
    # wrapped text per inch, then the most wrapped lines
    cells = [[((r[j] if j < len(r) else '').replace('**', '').replace('`', ''),
               k == 0 or (r[j] if j < len(r) else '').startswith('**')) for j in range(n)] for k, r in enumerate(rows)]
    # each word as its hyphen pieces: (width, joined to the previous piece without a space)
    ww = [[([(text_w_in(pc, TABLE_PT, b_), k > 0) for w in t.split() for k, pc in enumerate(pieces(w))],
            text_w_in(' ', TABLE_PT, b_)) for t, b_ in r] for r in cells]
    def lines(cell, w):
        widths, sp = cell
        avail = w - CELL_PAD_IN
        cnt, cur = 1, 0.0
        for x, joined in widths:
            gap = 0.0 if joined else sp
            if cur == 0:
                cur = x
            elif cur + gap + x <= avail:
                cur += gap + x
            else:
                cnt += 1; cur = x
        return cnt
    ws = list(mins)
    L = [[lines(ww[k][j], ws[j]) for j in range(n)] for k in range(len(rows))]
    step = 0.05
    while avail_in - sum(ws) >= step - 1e-9:
        slack = avail_in - sum(ws)
        H0 = sum(max(r) for r in L); T0 = sum(map(sum, L))
        best = None
        for j in range(n):
            d = step
            while d <= min(slack, 2.0) + 1e-9 and ws[j] + d <= nats[j] + step:
                col = [lines(ww[k][j], ws[j] + d) for k in range(len(rows))]
                H = sum(max(max((L[k][i] for i in range(n) if i != j), default=0), col[k]) for k in range(len(rows)))
                T = T0 - sum(L[k][j] for k in range(len(rows))) + sum(col)
                if (H0 - H, T0 - T) > (0, 0):
                    score = ((H0 - H) / d, (T0 - T) / d)
                    if best is None or score > best[0]:
                        best = (score, j, d, col)
                    break
                d += step
        if best is None:
            break
        _, j, d, col = best
        ws[j] += d
        for k in range(len(rows)):
            L[k][j] = col[k]
    left = avail_in - sum(ws)
    gap = [max(nt - w, 0.0) for nt, w in zip(nats, ws)]
    ws = [w + left * (g / sum(gap) if sum(gap) else 1 / n) for w, g in zip(ws, gap)]
    return ws, True

def col_widths(rows):
    n = len(rows[0])
    ws = []
    for j in range(n):
        cells = [r[j] if j < len(r) else '' for r in rows]
        lens = [len(c) for c in cells]
        maxword = max((len(w) for c in cells for w in c.split()), default=3)
        w = max(maxword * 1.5 + 4, min(0.5 * (sum(lens) / len(lens)) + 0.5 * max(lens), 30 if n < 8 else 16))
        ws.append(max(w, 7))
    return ws

def split_row(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]

def convert_file(path, cmap):
    text = path.read_text(encoding='utf8')
    body = text.split('\n# Notes', 1)[0]
    body = re.sub(r'\n---\s*$', '\n', body.rstrip()) + '\n'
    local = notes_table(text)

    def cite(m):
        n = int(m.group(1))
        if n not in local:
            sys.exit(f'FAIL: unmapped citation [{n}] in {path.name}')
        code = local[n][0]
        return f'[{cmap(code, local[n])}]'
    body = re.sub(r'\[(\d+)\](?!\()', cite, body)
    body = body.replace('ZZ^T', 'ZZᵀ')
    # plain-text variables with an underscore subscript (outside display math) -> pandoc subscript
    body = '\n'.join(ln if '$$' in ln or ln.startswith('```') or '\\' in ln else
                     re.sub(r'(?<![\w/.])([A-Za-z\u0391-\u03a9\u03b1-\u03c9][\u0302\u0304]?)_([A-Za-z0-9]+(?:-[a-z]+)?)',
                            r'\1~\2~', ln) for ln in body.split('\n'))

    lines = body.split('\n')
    out = []
    i = 0
    after_table = False
    cur_table = None
    while i < len(lines):
        ln = lines[i]
        m = re.match(r'\[Figure (\d+): (.+)\]\s*$', ln)
        if m:
            out.append(f'FIGURE|{m.group(1)}|{m.group(2)}')
            i += 1; continue
        m = re.match(r'Table (\d+): (.+)$', ln)
        if m and i + 2 < len(lines) and lines[i + 2].startswith('|'):
            out.append(f'TABCAP|{m.group(1)}|{m.group(2)}')
            cur_table = int(m.group(1))
            i += 1; continue
        m = re.match(r'\[Equation (\d+)\]\s*$', ln)
        if m:
            n = m.group(1)
            j = i + 1
            assert lines[j].startswith('```latex'), (path, ln)
            k = j + 1
            tex = []
            while not lines[k].startswith('```'):
                tex.append(lines[k]); k += 1
            out.append('$$' + ' '.join(tex).strip() + '$$')
            out.append('')
            out.append(f'EQNUM|{n}')
            i = k + 1; continue
        if ln.startswith('|'):
            j = i
            rows = []
            while j < len(lines) and lines[j].startswith('|'):
                if not re.match(r'^\|[\s:|-]+\|\s*$', lines[j]):
                    rows.append(split_row(lines[j]))
                j += 1
            ws, fits = col_widths_pt(rows, TEXT_W_IN)
            if not fits:
                sys.exit(f'FAIL: table {cur_table} in {path.name}: a word does not fit {TEXT_W_IN} in at {TABLE_PT} pt')
            cur_table = None
            scale = 400 / sum(ws)
            dashes = ['-' * max(3, int(round(w * scale))) for w in ws]
            out.append('| ' + ' | '.join(rows[0]) + ' |')
            out.append('|' + '|'.join(dashes) + '|')
            for r in rows[1:]:
                r = r + [''] * (len(rows[0]) - len(r))
                out.append('| ' + ' | '.join(c if c else ' ' for c in r) + ' |')
            i = j
            after_table = True
            continue
        if after_table and ln.strip():
            if ln.startswith(NOTE_STARTS):
                para = []
                while i < len(lines) and lines[i].strip():
                    para.append(lines[i]); i += 1
                out.append('::: {custom-style="Table Note"}')
                out.append(' '.join(para))
                out.append(':::')
                after_table = False
                continue
            after_table = False
        out.append(ln)
        i += 1
    return '\n'.join(out)

def build_markdown():
    order = {}
    refs = {}

    def cmap(code, info):
        if code not in order:
            order[code] = len(order) + 1
            refs[code] = info
        return order[code]

    parts = {}
    for f in FILES:
        parts[f.name] = convert_file(f, cmap)
    return parts, order, refs

# ---------------------------------------------------------------- reference doc (styles)
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS = {'w': W, 'm': M, 'r': R}
def q(tag):
    p, t = tag.split(':')
    return '{%s}%s' % (NS[p], t)

STYLE_XML = {
    'Normal': ('paragraph', None, '<w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>'
               '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Times New Roman" '
               'w:cs="Times New Roman"/><w:sz w:val="24"/><w:szCs w:val="24"/><w:lang w:val="en-US"/></w:rPr>'),
    'Body Text': ('paragraph', 'Normal', '<w:pPr><w:spacing w:before="0" w:after="0" w:line="360" w:lineRule="auto"/>'
                  '<w:ind w:firstLine="720"/><w:jc w:val="both"/></w:pPr>'),
    'First Paragraph': ('paragraph', 'Body Text', ''),
    'Compact': ('paragraph', 'Normal', '<w:pPr><w:spacing w:before="20" w:after="20" w:line="240" w:lineRule="auto"/>'
                '<w:ind w:firstLine="0"/><w:jc w:val="left"/></w:pPr><w:rPr><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'),
    'List Text': ('paragraph', 'Normal', '<w:pPr><w:spacing w:before="0" w:after="80" w:line="360" w:lineRule="auto"/>'
                  '<w:jc w:val="both"/></w:pPr>'),
    'Table Note': ('paragraph', 'Normal', '<w:pPr><w:spacing w:before="60" w:after="240" w:line="240" w:lineRule="auto"/>'
                   '<w:jc w:val="left"/></w:pPr><w:rPr><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'),
    'Caption': ('paragraph', 'Normal', '<w:pPr><w:spacing w:before="120" w:after="240" w:line="240" w:lineRule="auto"/>'
                '<w:jc w:val="center"/></w:pPr><w:rPr><w:i w:val="0"/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr>'),
    'Figure Para': ('paragraph', 'Normal', '<w:pPr><w:keepNext/><w:spacing w:before="240" w:after="0" w:line="240" w:lineRule="auto"/>'
                    '<w:jc w:val="center"/></w:pPr>'),
    'Reference Item': ('paragraph', 'Normal', '<w:pPr><w:spacing w:after="120" w:line="276" w:lineRule="auto"/>'
                       '<w:ind w:left="567" w:hanging="567"/><w:jc w:val="left"/></w:pPr><w:rPr><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr>'),
    'Equation': ('paragraph', 'Normal', '<w:pPr><w:tabs><w:tab w:val="center" w:pos="4320"/><w:tab w:val="right" w:pos="8640"/></w:tabs>'
                 '<w:spacing w:before="120" w:after="120"/></w:pPr>'),
    'Heading 1': ('paragraph', 'Normal', '<w:pPr><w:keepNext/><w:pageBreakBefore/><w:spacing w:before="0" w:after="360" w:line="240" w:lineRule="auto"/>'
                  '<w:jc w:val="center"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:bCs/><w:caps/><w:color w:val="000000"/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr>'),
    'Heading 2': ('paragraph', 'Normal', '<w:pPr><w:keepNext/><w:spacing w:before="240" w:after="120" w:line="240" w:lineRule="auto"/>'
                  '<w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:bCs/><w:color w:val="000000"/><w:sz w:val="26"/><w:szCs w:val="26"/></w:rPr>'),
    'Heading 3': ('paragraph', 'Normal', '<w:pPr><w:keepNext/><w:spacing w:before="200" w:after="100" w:line="240" w:lineRule="auto"/>'
                  '<w:outlineLvl w:val="2"/></w:pPr><w:rPr><w:b/><w:bCs/><w:i/><w:color w:val="000000"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr>'),
    'TOC Heading': ('paragraph', 'Heading 1', '<w:pPr><w:outlineLvl w:val="9"/></w:pPr>'),
    'toc 1': ('paragraph', 'Normal', '<w:pPr><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="8630"/></w:tabs><w:spacing w:before="60" w:after="0" w:line="240" w:lineRule="auto"/></w:pPr><w:rPr><w:b/></w:rPr>'),
    'toc 2': ('paragraph', 'Normal', '<w:pPr><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="8630"/></w:tabs><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:ind w:left="240"/></w:pPr>'),
    'toc 3': ('paragraph', 'Normal', '<w:pPr><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="8630"/></w:tabs><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:ind w:left="480"/></w:pPr>'),
    'table of figures': ('paragraph', 'Normal', '<w:pPr><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="8630"/></w:tabs><w:spacing w:after="40" w:line="240" w:lineRule="auto"/></w:pPr>'),
}

def make_reference_doc(path):
    shutil.copy(TEMPLATE, path)
    with zipfile.ZipFile(path) as z:
        data = {n: z.read(n) for n in z.namelist()}
    st = etree.fromstring(data['word/styles.xml'])
    for name, (typ, based, inner) in STYLE_XML.items():
        sid = name.replace(' ', '')
        if name == 'Normal':
            sid = 'Normal'
        for old in st.findall('w:style', NS):
            nm = old.find('w:name', NS)
            if old.get(q('w:styleId')) == sid or (nm is not None and nm.get(q('w:val')).lower() == name.lower()):
                st.remove(old)
        xml = (f'<w:style xmlns:w="{W}" w:type="{typ}" w:styleId="{sid}"><w:name w:val="{name}"/>'
               + (f'<w:basedOn w:val="{based.replace(" ", "")}"/>' if based else '')
               + '<w:qFormat/>' + inner + '</w:style>')
        st.append(etree.fromstring(xml))
    # table style used by pandoc ("Table"): grid borders
    for old in st.findall('w:style', NS):
        if old.get(q('w:styleId')) == 'Table':
            st.remove(old)
    st.append(etree.fromstring(
        f'<w:style xmlns:w="{W}" w:type="table" w:styleId="Table"><w:name w:val="Table"/><w:basedOn w:val="TableNormal"/>'
        '<w:tblPr><w:jc w:val="center"/><w:tblBorders>'
        + ''.join(f'<w:{b} w:val="single" w:sz="4" w:space="0" w:color="000000"/>' for b in
                  ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'))
        + '</w:tblBorders><w:tblCellMar><w:top w:w="0" w:type="dxa"/><w:left w:w="70" w:type="dxa"/><w:bottom w:w="0" w:type="dxa"/>'
        '<w:right w:w="70" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style>'))
    data['word/styles.xml'] = etree.tostring(st, xml_declaration=True, encoding='UTF-8', standalone=True)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, b in data.items():
            z.writestr(n, b)

# ---------------------------------------------------------------- post-processing helpers
def run(text, rpr=''):
    t = etree.SubElement(etree.Element(q('w:r')), q('w:t'))
    r = t.getparent()
    if rpr:
        r.insert(0, etree.fromstring(f'<w:rPr xmlns:w="{W}">{rpr}</w:rPr>'))
    t.text = text
    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    return r

def fld_runs(instr, result):
    rs = [etree.fromstring(f'<w:r xmlns:w="{W}"><w:fldChar w:fldCharType="begin"/></w:r>'),
          etree.fromstring(f'<w:r xmlns:w="{W}"><w:instrText xml:space="preserve"> {instr} </w:instrText></w:r>'),
          etree.fromstring(f'<w:r xmlns:w="{W}"><w:fldChar w:fldCharType="separate"/></w:r>'),
          run(result),
          etree.fromstring(f'<w:r xmlns:w="{W}"><w:fldChar w:fldCharType="end"/></w:r>')]
    return rs

def para(style, runs=(), extra_ppr=''):
    p = etree.fromstring(f'<w:p xmlns:w="{W}"><w:pPr><w:pStyle w:val="{style}"/>{extra_ppr}</w:pPr></w:p>')
    for r in runs:
        p.append(r)
    return p

def ptext(p):
    return ''.join(p.itertext())

def caption_para(kind, n, title, keep_next):
    runs = [run(f'{kind} ')] + fld_runs(f'SEQ {kind} \\* ARABIC', str(n)) + [run(f': {title}')]
    return para('Caption', runs, '<w:keepNext/>' if keep_next else '')

def field_block(instr, placeholder):
    p = para('Normal', [], '')
    p.append(etree.fromstring(f'<w:r xmlns:w="{W}"><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r>'))
    p.append(etree.fromstring(f'<w:r xmlns:w="{W}"><w:instrText xml:space="preserve"> {instr} </w:instrText></w:r>'))
    p.append(etree.fromstring(f'<w:r xmlns:w="{W}"><w:fldChar w:fldCharType="separate"/></w:r>'))
    p.append(run(placeholder))
    p.append(etree.fromstring(f'<w:r xmlns:w="{W}"><w:fldChar w:fldCharType="end"/></w:r>'))
    return p

def heading_para(text, style='Heading1'):
    return para(style, [run(text)])

def template_blocks():
    with zipfile.ZipFile(TEMPLATE) as z:
        d = etree.fromstring(z.read('word/document.xml'))
    body = d.find('w:body', NS)
    blocks = [b for b in body if b.tag in (q('w:p'), q('w:tbl'))]
    txt = [ptext(b) for b in blocks]
    i0 = [i for i, t in enumerate(txt) if t.startswith('Unsupervised Epileptic')][0]
    i1 = [i for i, t in enumerate(txt) if t.strip() == 'ACKNOWLEDGMENTS'][0]
    sel = [copy.deepcopy(b) for b in blocks[i0:i1]]
    for b in sel:
        for br in b.iter(q('w:br')):
            if br.get(q('w:type')) == 'page':
                br.getparent().remove(br)
        for ppr in b.iter(q('w:pPr')):
            for pb in ppr.findall('w:pageBreakBefore', NS):
                ppr.remove(pb)
    # second title (approval page) starts a new page
    k = [i for i, b in enumerate(sel) if ptext(b).startswith('Unsupervised Epileptic')][1]
    ppr = sel[k].find('w:pPr', NS)
    ppr.insert(0, etree.fromstring(f'<w:pageBreakBefore xmlns:w="{W}"/>'))
    return sel

def set_cell_shade(tc, fill):
    tcpr = tc.find('w:tcPr', NS)
    if tcpr is None:
        tcpr = etree.SubElement(tc, q('w:tcPr')); tc.insert(0, tcpr)
    for s in tcpr.findall('w:shd', NS):
        tcpr.remove(s)
    tcpr.append(etree.fromstring(f'<w:shd xmlns:w="{W}" w:val="clear" w:color="auto" w:fill="{fill}"/>'))

def size_runs(el, half_points):
    for r in el.iter(q('w:r')):
        rpr = r.find('w:rPr', NS)
        if rpr is None:
            rpr = etree.Element(q('w:rPr')); r.insert(0, rpr)
        for s in rpr.findall('w:sz', NS) + rpr.findall('w:szCs', NS):
            rpr.remove(s)
        rpr.append(etree.fromstring(f'<w:sz xmlns:w="{W}" w:val="{half_points}"/>'))
        rpr.append(etree.fromstring(f'<w:szCs xmlns:w="{W}" w:val="{half_points}"/>'))
    for m_r in el.iter(q('m:r')):
        pass

ORDER = {
    'pPr': ['pStyle', 'keepNext', 'keepLines', 'pageBreakBefore', 'framePr', 'widowControl', 'numPr',
            'suppressLineNumbers', 'pBdr', 'shd', 'tabs', 'suppressAutoHyphens', 'kinsoku', 'wordWrap',
            'overflowPunct', 'topLinePunct', 'autoSpaceDE', 'autoSpaceDN', 'bidi', 'adjustRightInd',
            'snapToGrid', 'spacing', 'ind', 'contextualSpacing', 'mirrorIndents', 'suppressOverlap', 'jc',
            'textDirection', 'textAlignment', 'textboxTightWrap', 'outlineLvl', 'divId', 'cnfStyle', 'rPr',
            'sectPr', 'pPrChange'],
    'rPr': ['rStyle', 'rFonts', 'b', 'bCs', 'i', 'iCs', 'caps', 'smallCaps', 'strike', 'dstrike', 'outline',
            'shadow', 'emboss', 'imprint', 'noProof', 'snapToGrid', 'vanish', 'webHidden', 'color', 'spacing',
            'w', 'kern', 'position', 'sz', 'szCs', 'highlight', 'u', 'effect', 'bdr', 'shd', 'fitText',
            'vertAlign', 'rtl', 'cs', 'em', 'lang', 'eastAsianLayout', 'specVanish', 'oMath'],
    'tblPr': ['tblStyle', 'tblpPr', 'tblOverlap', 'bidiVisual', 'tblStyleRowBandSize', 'tblStyleColBandSize',
              'tblW', 'jc', 'tblCellSpacing', 'tblInd', 'tblBorders', 'shd', 'tblLayout', 'tblCellMar',
              'tblLook', 'tblCaption', 'tblDescription'],
    'tcPr': ['cnfStyle', 'tcW', 'gridSpan', 'hMerge', 'vMerge', 'tcBorders', 'shd', 'noWrap', 'tcMar',
             'textDirection', 'tcFitText', 'vAlign', 'hideMark'],
}

def schema_order(root):
    for tag, order in ORDER.items():
        rank = {n: i for i, n in enumerate(order)}
        for el in root.iter(q('w:' + tag)):
            kids = list(el)
            if not kids:
                continue
            kids_sorted = sorted(kids, key=lambda c: rank.get(etree.QName(c).localname, len(order)))
            if kids_sorted != kids:
                for c in kids:
                    el.remove(c)
                for c in kids_sorted:
                    el.append(c)

def postprocess(docx, out, eq_count, ack_text_present=True):
    with zipfile.ZipFile(docx) as z:
        data = {n: z.read(n) for n in z.namelist()}
    doc = etree.fromstring(data['word/document.xml'])
    body = doc.find('w:body', NS)
    final_sect = body.find('w:sectPr', NS)

    # margins (chat 8, author 13/10): Report format.md -- left 1.5 in, top/bottom/right 1 in (MARGIN above);
    # supersedes P-5 (the template file's own section, top/bottom 1.5 in)
    pgmar = final_sect.find('w:pgMar', NS)
    for k, v in MARGIN.items():
        pgmar.set(q('w:' + k), str(v))
    for k in ('gutter',):
        pgmar.set(q('w:' + k), '0')

    children = list(body)
    # 1) markers
    eq_seen = []
    for p in children:
        if p.tag != q('w:p'):
            continue
        t = ptext(p)
        if t.startswith('TABCAP|') or t.startswith('FIGCAP|'):
            kind_m, n, title = t.split('|', 2)
            kind = 'Table' if kind_m == 'TABCAP' else 'Figure'
            p.addprevious(caption_para(kind, int(n), title, keep_next=(kind == 'Table')))
            body.remove(p)
        elif t.startswith('EQNUM|'):
            n = t.split('|')[1]
            prev = p.getprevious()
            omp = prev.find('.//m:oMathPara', NS)
            assert omp is not None, f'equation {n}: no display math before marker'
            maths = omp.findall('m:oMath', NS)
            newp = para('Equation', [], '')
            newp.append(run('\t'))
            for mth in maths:
                newp.append(mth)
            newp.append(run(f'\t({n})'))
            prev.addprevious(newp)
            body.remove(prev)
            body.remove(p)
            eq_seen.append(int(n))
    assert eq_seen == list(range(1, eq_count + 1)), eq_seen

    # 1b) tight lists outside tables use Compact in pandoc: give them body-text size and spacing
    for p in body.findall('w:p', NS):
        ps = p.find('w:pPr/w:pStyle', NS)
        if ps is not None and ps.get(q('w:val')) == 'Compact':
            ps.set(q('w:val'), 'ListText')

    # 2) tables: header bold, font size by column count, Table 3 shading, widths
    for tbl in body.iter(q('w:tbl')):
        rows = tbl.findall('w:tr', NS)
        ncol = len(rows[0].findall('w:tc', NS))
        tblpr = tbl.find('w:tblPr', NS)
        for tw in tblpr.findall('w:tblW', NS):
            tblpr.remove(tw)
        tblpr.append(etree.fromstring(f'<w:tblW xmlns:w="{W}" w:w="5000" w:type="pct"/>'))
        for r in rows[0].iter(q('w:r')):
            rpr = r.find('w:rPr', NS)
            if rpr is None:
                rpr = etree.Element(q('w:rPr')); r.insert(0, rpr)
            if rpr.find('w:b', NS) is None:
                rpr.insert(0, etree.fromstring(f'<w:b xmlns:w="{W}"/>'))
        trpr = rows[0].find('w:trPr', NS)
        if trpr is None:
            trpr = etree.Element(q('w:trPr')); rows[0].insert(0, trpr)
        if trpr.find('w:tblHeader', NS) is None:
            trpr.append(etree.fromstring(f'<w:tblHeader xmlns:w="{W}"/>'))
        for tc in rows[0].findall('w:tc', NS):
            set_cell_shade(tc, 'E7E6E6')
        size_runs(tbl, 2 * TABLE_PT)  # chat 8: every table at 12 pt
        # Table 3 week shading
        texts = [ptext(tc).strip() for tc in rows[0].findall('w:tc', NS)]
        if texts[:3] == ['No', 'Task', '1']:
            for tr in rows[1:]:
                for tc in tr.findall('w:tc', NS):
                    if ptext(tc).strip() == '■':
                        set_cell_shade(tc, '808080')
                        for t in tc.iter(q('w:t')):
                            t.text = t.text.replace('■', '')
        # chat 8: the caption never stands with only the header and one row -- keep the header and the first
        # two rows together (with the caption, which is keepNext)
        if True:
            for tr in rows[:min(3, len(rows) - 1)]:
                for pp in tr.iter(q('w:p')):
                    ppr = pp.find('w:pPr', NS)
                    if ppr is None:
                        ppr = etree.Element(q('w:pPr')); pp.insert(0, ppr)
                    if ppr.find('w:keepNext', NS) is None:
                        ppr.insert(1 if ppr.find('w:pStyle', NS) is not None else 0, etree.fromstring(f'<w:keepNext xmlns:w="{W}"/>'))
    # cells: no first-line indent (Compact already), keep rows together
    for tr in body.iter(q('w:tr')):
        trpr = tr.find('w:trPr', NS)
        if trpr is None:
            trpr = etree.Element(q('w:trPr')); tr.insert(0, trpr)
        if trpr.find('w:cantSplit', NS) is None:
            trpr.insert(0, etree.fromstring(f'<w:cantSplit xmlns:w="{W}"/>'))

    # 3) front: title + approval pages, then field lists
    first = body[0]
    for b in template_blocks():
        first.addprevious(b)
    data_hdr = None

    # locate headings
    def find_heading(txt):
        for p in body.iter(q('w:p')):
            ps = p.find('w:pPr/w:pStyle', NS)
            if ps is not None and ps.get(q('w:val')).startswith('Heading1') and ptext(p).strip() == txt:
                return p
        raise SystemExit(f'FAIL: heading {txt!r} not found')
    ack = find_heading('Acknowledgements')
    abbr = find_heading('List of Abbreviations')
    abstract = find_heading('Abstract')
    # move Acknowledgements block before Abstract? Order: Ack, ToC, LoT, LoF, Abbrev, Abstract
    def block_until_next_h1(h):
        out = [h]
        n = h.getnext()
        while n is not None and n.tag != q('w:sectPr'):
            ps = n.find('w:pPr/w:pStyle', NS) if n.tag == q('w:p') else None
            if ps is not None and ps.get(q('w:val')) == 'Heading1':
                break
            out.append(n); n = n.getnext()
        return out
    ack_blk = block_until_next_h1(ack)
    abbr_blk = block_until_next_h1(abbr)
    for b in ack_blk:
        abstract.addprevious(b)
    toc = [heading_para('Table of Contents', 'TOCHeading'),
           field_block('TOC \\o "1-3" \\h \\z \\u', '[Table of contents: update fields (F9)]'),
           heading_para('List of Tables', 'TOCHeading'),
           field_block('TOC \\h \\z \\c "Table"', '[List of tables: update fields (F9)]'),
           heading_para('List of Figures', 'TOCHeading'),
           field_block('TOC \\h \\z \\c "Figure"', '[List of figures: update fields (F9)]')]
    for b in toc:
        abstract.addprevious(b)
    for b in abbr_blk:
        abstract.addprevious(b)

    # 4) section break before Chapter 1: front matter roman, body arabic from 1
    ch1 = find_heading('Chapter 1: Introduction')
    front_sect = copy.deepcopy(final_sect)
    for pn in front_sect.findall('w:pgNumType', NS):
        front_sect.remove(pn)
    front_sect.append(etree.fromstring(f'<w:pgNumType xmlns:w="{W}" w:fmt="lowerRoman" w:start="1"/>'))
    sp = para('Normal', [], '')
    sp.find('w:pPr', NS).append(front_sect)
    ch1.addprevious(sp)
    for pn in final_sect.findall('w:pgNumType', NS):
        final_sect.remove(pn)
    final_sect.append(etree.fromstring(f'<w:pgNumType xmlns:w="{W}" w:fmt="decimal" w:start="1"/>'))
    # the first heading of a section must not add a second page break
    ppr = ch1.find('w:pPr', NS)
    ppr.append(etree.fromstring(f'<w:pageBreakBefore xmlns:w="{W}" w:val="0"/>'))

    # 5) landscape sections for the tables in LANDSCAPE (chat 8): caption + table + its note on their own
    #    landscape pages; page numbers run on; the section that starts at Chapter 1 restarts at 1
    def sect_like(orient):
        s_ = copy.deepcopy(final_sect)
        for pn in s_.findall('w:pgNumType', NS):
            s_.remove(pn)
        s_.append(etree.fromstring(f'<w:pgNumType xmlns:w="{W}" w:fmt="decimal"/>'))
        pz = s_.find('w:pgSz', NS)
        pm = s_.find('w:pgMar', NS)
        if orient == 'landscape':
            pz.set(q('w:w'), '15840'); pz.set(q('w:h'), '12240'); pz.set(q('w:orient'), 'landscape')
            for k, v in {'top': MARGIN['left'], 'bottom': MARGIN['right'], 'left': MARGIN['top'],
                         'right': MARGIN['bottom']}.items():
                pm.set(q('w:' + k), str(v))
        else:
            pz.set(q('w:w'), '12240'); pz.set(q('w:h'), '15840'); pz.set(q('w:orient'), 'portrait')
        for t in s_.findall('w:type', NS):
            s_.remove(t)
        return s_
    def holder(sect):
        p_ = para('Normal', [], '')
        p_.find('w:pPr', NS).append(sect)
        return p_
    caps = {}
    for p in body.findall('w:p', NS):
        ps = p.find('w:pPr/w:pStyle', NS)
        if ps is not None and ps.get(q('w:val')) == 'Caption':
            mm = re.match(r'Table (\d+):', ''.join(t.text or '' for t in p.iter(q('w:t'))))
            if mm:
                caps[int(mm.group(1))] = p
    # column grid = the text width of the table's page (pandoc writes 5.5 in), fixed layout so the 12-pt
    # widths computed from the text hold in Word and LibreOffice
    for tbl in body.findall('w:tbl', NS):
        prev = tbl.getprevious()
        num = next((k for k, c in caps.items() if c is prev), None)
        tw = int((LAND_W_IN if num in LANDSCAPE else TEXT_W_IN) * TW)
        cols = tbl.findall('w:tblGrid/w:gridCol', NS)
        g = [int(c.get(q('w:w'))) for c in cols]
        new = [int(round(x * tw / sum(g))) for x in g]
        new[-1] += tw - sum(new)
        for c, x in zip(cols, new):
            c.set(q('w:w'), str(x))
        tblpr = tbl.find('w:tblPr', NS)
        for el in tblpr.findall('w:tblW', NS) + tblpr.findall('w:tblLayout', NS):
            tblpr.remove(el)
        tblpr.append(etree.fromstring(f'<w:tblW xmlns:w="{W}" w:w="{tw}" w:type="dxa"/>'))
        tblpr.append(etree.fromstring(f'<w:tblLayout xmlns:w="{W}" w:type="fixed"/>'))
        for tr in tbl.findall('w:tr', NS):
            for j, tc in enumerate(tr.findall('w:tc', NS)):
                tcpr = tc.find('w:tcPr', NS)
                if tcpr is None:
                    tcpr = etree.Element(q('w:tcPr')); tc.insert(0, tcpr)
                for el in tcpr.findall('w:tcW', NS):
                    tcpr.remove(el)
                tcpr.insert(0, etree.fromstring(f'<w:tcW xmlns:w="{W}" w:w="{new[j]}" w:type="dxa"/>'))
    for n in sorted(LANDSCAPE):
        cap = caps[n]
        tbl = cap.getnext()
        assert tbl.tag == q('w:tbl'), n
        last = tbl
        nx = tbl.getnext()
        if nx is not None and nx.tag == q('w:p'):
            ps = nx.find('w:pPr/w:pStyle', NS)
            if ps is not None and ps.get(q('w:val')) == 'TableNote':
                last = nx
        cap.addprevious(holder(sect_like('portrait')))
        last.addnext(holder(sect_like('landscape')))
    # page numbering: front = lowerRoman from i; first body section decimal from 1; the rest run on
    sects = [s_ for s_ in body.iter(q('w:sectPr'))]
    for k, s_ in enumerate(sects):
        if k == 0:
            continue
        for pn in s_.findall('w:pgNumType', NS):
            s_.remove(pn)
        s_.append(etree.fromstring(f'<w:pgNumType xmlns:w="{W}" w:fmt="decimal"' + (' w:start="1"' if k == 1 else '') + '/>'))

    schema_order(doc)
    data['word/document.xml'] = etree.tostring(doc, xml_declaration=True, encoding='UTF-8', standalone=True)
    hd = etree.fromstring(data['word/header1.xml'])
    last = hd.findall('w:p', NS)[-1]
    sp = last.find('w:pPr/w:spacing', NS)
    sp.set(q('w:after'), '240')
    data['word/header1.xml'] = etree.tostring(hd, xml_declaration=True, encoding='UTF-8', standalone=True)
    st = etree.fromstring(data['word/settings.xml'])
    if st.find('w:updateFields', NS) is None:
        after = {'hdrShapeDefaults', 'footnotePr', 'endnotePr', 'compat', 'docVars', 'rsids', 'mathPr',
                 'attachedSchema', 'themeFontLang', 'clrSchemeMapping', 'doNotIncludeSubdocsInStats',
                 'doNotAutoCompressPictures', 'forceUpgrade', 'captions', 'readModeInkLockDown', 'smartTagType',
                 'schemaLibrary', 'shapeDefaults', 'doNotEmbedSmartTags', 'decimalSymbol', 'listSeparator'}
        uf = etree.fromstring(f'<w:updateFields xmlns:w="{W}" w:val="true"/>')
        nxt = next((c for c in st if etree.QName(c).localname in after), None)
        if nxt is not None:
            nxt.addprevious(uf)
        else:
            st.append(uf)
    data['word/settings.xml'] = etree.tostring(st, xml_declaration=True, encoding='UTF-8', standalone=True)
    # pandoc copies fontTable.xml.rels from the template but not the embedded font files: drop the embedding
    if 'word/_rels/fontTable.xml.rels' in data:
        del data['word/_rels/fontTable.xml.rels']
        ft = etree.fromstring(data['word/fontTable.xml'])
        for el in list(ft.iter()):
            if etree.QName(el).localname.startswith('embed'):
                el.getparent().remove(el)
        data['word/fontTable.xml'] = etree.tostring(ft, xml_declaration=True, encoding='UTF-8', standalone=True)
    for k in [k for k in data if k.startswith('word/fonts/')]:
        del data[k]
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, b in data.items():
            z.writestr(n, b)

# ---------------------------------------------------------------- main
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    parts, order, refs = build_markdown()
    sheet = sheet_rows()

    # figures
    fig_md = {}
    report = []
    for n, p in FIG.items():
        if p == 'COMPOSE':
            p = compose_fig15(TMP / 'fig15_app_screens.png')
        if p is None:
            fig_md[n] = None
            report.append((n, 'PLACEHOLDER', ''))
            continue
        if not Path(p).exists():
            sys.exit(f'FAIL: figure {n} file missing: {p}')
        im = Image.open(p)
        w, h = im.size
        width = min(FIG_MAXW.get(n, TEXT_W_IN), MAXH_IN * w / h)  # tall figures: height bounded so figure + caption fit one page
        fig_md[n] = f'![]({p}){{width={width:.2f}in}}'
        report.append((n, str(p), hashlib.sha256(Path(p).read_bytes()).hexdigest()[:12]))

    md = []
    for name in ['Front_matter_v8.md', 'Chapter_1_Introduction_v8.md', 'Chapter_2_Methodology_v8.md',
                 'Chapter_3_Results_v8.md', 'Chapter_4_Discussion_v8.md', 'Chapter_5_Conclusion_v8.md']:
        md.append(parts[name])
    # references
    md.append('# References\n')
    ref_rows = []
    for code, n in sorted(order.items(), key=lambda kv: kv[1]):
        _, chap_ref, chap_id = refs[code]
        cit = OVERRIDE.get(code) or (clean_cite(sheet[code]) if code in sheet else clean_cite(chap_ref))
        idf = ident(chap_id)
        line = f'[{n}] {cit}' + (f' {idf}' if idf else '')
        ref_rows.append((n, code, line))
        md.append('::: {custom-style="Reference Item"}\n' + line + '\n:::\n')
    md.append(parts['Appendix_v8.md'].replace('# Appendix', '# Appendices', 1))
    text = '\n\n'.join(md)

    # figure markers -> image paragraph + caption marker
    def figrep(m):
        n, title = int(m.group(1)), m.group(2)
        img = fig_md[n]
        if img is None:
            img_block = (f'::: {{custom-style="Figure Para"}}\n[Figure {n} to be inserted: the 11/10 draft drawing '
                         f'of the final system, Reports/v8/figures_inherited/]\n:::')
        else:
            img_block = f'::: {{custom-style="Figure Para"}}\n{img}\n:::'
        return f'{img_block}\n\nFIGCAP|{n}|{title}'
    text = re.sub(r'^FIGURE\|(\d+)\|(.+)$', figrep, text, flags=re.M)
    # abstract keywords bold label kept; drop horizontal rules
    text = re.sub(r'^---\s*$', '', text, flags=re.M)
    mdpath = TMP / 'thesis_v8.md'
    mdpath.write_text(text, encoding='utf8')

    ref = TMP / 'reference.docx'
    make_reference_doc(ref)
    raw = TMP / 'pandoc_raw.docx'
    subprocess.run(['pandoc', str(mdpath), '-f', 'markdown-superscript-implicit_figures+tex_math_dollars',
                    '--columns=20', '--reference-doc', str(ref), '-o', str(raw)], check=True)
    out = OUT / 'Thesis_v8_NguyenQuocTrungNhan.docx'
    postprocess(raw, out, eq_count=12)
    (OUT / 'reference_map.json').write_text(json.dumps(
        [{'n': n, 'sheet': c, 'text': l} for n, c, l in ref_rows], ensure_ascii=False, indent=1), encoding='utf8')
    (OUT / 'figure_sources.txt').write_text('\n'.join(f'{n}\t{p}\t{h}' for n, p, h in report), encoding='utf8')
    print('OK', out, 'references', len(ref_rows))

if __name__ == '__main__':
    main()
