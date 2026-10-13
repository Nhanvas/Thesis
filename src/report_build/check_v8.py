#!/usr/bin/env python3
"""Checks over the built v8 report (.docx). Usage: check_v8.py Thesis_v8.docx
Reads only the built document; prints one line per check and FAIL lines; exit 1 on any FAIL.
1 captions in sequence (Table 1..N, Figure 1..M) and every exhibit cited in the text outside its caption;
2 every 'Table n', 'Figure n', 'Equation n', 'Section x.y', 'Appendix X' in the text has a target;
3 citations [n]: every n in 1..R, first appearances in order 1, 2, 3, ...;
4 forbidden numbers and internal labels (project instructions, section 4 and report rules);
5 abstract word count; 6 table font size, page margins and landscape sections.
"""
import re, sys, zipfile
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}
q = lambda t: '{%s}%s' % (W, t)

FORBIDDEN = ['0.750', '0.829', '0.791', '39.77', '71.25', '0.6497', '0.3095', '0.7758', '0.8879', '−0.1261',
             '-0.1261', '0.6267', '0.6681', '0.2672', '0.3578', 'p = 0.984', '8.9e-11', '16.9 ms', '~15 s per hour',
             '9.76', '10.83', '21.0s per hour of EEG (median', 'median 21.0']
LABELS = [r'(?<![\w-])[GHC]\d\b(?!-)', r'\bL[123]\b', r'\bA[45]\b', r'\btier\b', r'\blook #?\d', r'(?<![\w-])P3\b(?!-)', r'\bE\d{1,2}\b',
          r'@', r'§', r'\.py\b', r'results/', r'\bphase B\b', r'\blever\b']

def main(path):
    z = zipfile.ZipFile(path)
    doc = etree.fromstring(z.read('word/document.xml'))
    body = doc.find('w:body', NS)
    fails = []
    paras = []  # (style, text)
    for p in body.iter(q('p')):
        ps = p.find('w:pPr/w:pStyle', NS)
        st = ps.get(q('val')) if ps is not None else ''
        t = ''.join(x.text or '' for x in p.iter(q('t')))
        paras.append((st, t))
    caps = [(st, t) for st, t in paras if st == 'Caption']
    tabs = [int(m.group(1)) for _, t in caps for m in [re.match(r'Table (\d+):', t)] if m]
    figs = [int(m.group(1)) for _, t in caps for m in [re.match(r'Figure (\d+):', t)] if m]
    print('1 tables', len(tabs), 'figures', len(figs))
    if tabs != list(range(1, len(tabs) + 1)): fails.append(f'table captions out of sequence {tabs}')
    if figs != list(range(1, len(figs) + 1)): fails.append(f'figure captions out of sequence {figs}')
    text = '\n'.join(t for st, t in paras if st not in ('Caption',) and not st.startswith('TOC') and not st.startswith('toc'))
    refs_part = text
    # stop the text at the reference list for citation checks
    i_ref = text.find('\nReferences\n')
    body_txt = text if i_ref < 0 else text[:i_ref] + text[text.find('\nAppendices\n'):] if '\nAppendices\n' in text else text
    for kind, have in (('Table', set(tabs)), ('Figure', set(figs))):
        cited = set()
        for m in re.finditer(kind + r's? (\d+)((?:\s*(?:,|and|to|–)\s*\d+)*)', body_txt):
            nums = [int(m.group(1))] + [int(x) for x in re.findall(r'\d+', m.group(2))]
            if re.search(r'(?:to|–)', m.group(2) or ''):
                a, b = nums[0], nums[-1]; nums = list(range(a, b + 1))
            for n in nums:
                cited.add(n)
                if n not in have: fails.append(f'{kind} {n} cited, no such exhibit')
        miss = sorted(have - cited)
        if miss: fails.append(f'{kind}s never cited in text: {miss}')
    eqs = [int(x) for x in re.findall(r'\((\d+)\)\s*$', '\n'.join(t for st, t in paras if st == 'Equation'), re.M)]
    print('  equations', len(eqs))
    if eqs != list(range(1, len(eqs) + 1)): fails.append(f'equations out of sequence {eqs}')
    for m in re.finditer(r'Equations? (\d+)((?:\s*(?:,|and|to|–)\s*\d+)*)', body_txt):
        for n in [int(m.group(1))] + [int(x) for x in re.findall(r'\d+', m.group(2))]:
            if n not in eqs: fails.append(f'Equation {n} cited, no such equation')
    heads = [t.strip() for st, t in paras if st.startswith('Heading')]
    secnums = set(re.match(r'(\d+(?:\.\d+)*)\s', h).group(1) for h in heads if re.match(r'\d+(?:\.\d+)*\s', h))
    apps = set(re.match(r'Appendix ([A-F])', h).group(1) for h in heads if re.match(r'Appendix [A-F]', h))
    print('2 numbered sections', len(secnums), 'appendices', sorted(apps))
    for m in re.finditer(r'Sections? (\d+(?:\.\d+)+)((?:\s*(?:,|and|to|–)\s*\d+(?:\.\d+)+)*)', body_txt):
        for n in [m.group(1)] + re.findall(r'\d+(?:\.\d+)+', m.group(2)):
            if n not in secnums: fails.append(f'Section {n} cited, no such section')
    for m in re.finditer(r'Appendix ([A-Z])\b', body_txt):
        if m.group(1) not in apps: fails.append(f'Appendix {m.group(1)} cited, no such appendix')
    # 3 citations (reference list paragraphs excluded)
    refitems = [t for st, t in paras if st == 'ReferenceItem']
    R = len(refitems)
    seq = []
    for m in re.finditer(r'\[(\d+(?:\s*[,–-]\s*\d+)*)\]', body_txt):
        if m.group(1).replace(' ', '') == '0,1':  # the value range [0, 1], not a citation
            continue
        parts = re.split(r'\s*,\s*', m.group(1))
        for prt in parts:
            if re.search(r'[–-]', prt):
                a, b = map(int, re.split(r'[–-]', prt)); seq += list(range(a, b + 1))
            else:
                seq.append(int(prt))
    first = []
    for n in seq:
        if n not in first: first.append(n)
    print('3 references', R, 'cited distinct', len(set(seq)))
    if sorted(set(seq)) != list(range(1, R + 1)): fails.append(f'citations vs list mismatch: missing {sorted(set(range(1, R + 1)) - set(seq))}, extra {sorted(set(seq) - set(range(1, R + 1)))}')
    if first != list(range(1, len(first) + 1)): fails.append(f'citations not in first-appearance order: {first[:20]}...')
    # 4 forbidden numbers, labels
    alltext = '\n'.join(t for _, t in paras)
    n4 = 0
    for f in FORBIDDEN:
        for m in re.finditer(re.escape(f), alltext):
            ctx = alltext[max(0, m.start() - 50):m.end() + 50].replace('\n', ' ')
            fails.append(f'forbidden {f!r}: …{ctx}…'); n4 += 1
    for rx in LABELS:
        for m in re.finditer(rx, body_txt):
            ctx = body_txt[max(0, m.start() - 50):m.end() + 50].replace('\n', ' ')
            fails.append(f'label {rx!r}: …{ctx}…'); n4 += 1
    print('4 forbidden/label hits', n4)
    # 5 abstract
    try:
        i = [k for k, (st, t) in enumerate(paras) if st.startswith('Heading1') and t.strip() == 'Abstract'][0]
        words = []
        for st, t in paras[i + 1:]:
            if st.startswith('Heading1') or t.startswith('Keywords'): break
            words += t.split()
        print('5 abstract words', len(words))
        if len(words) > 300: fails.append(f'abstract {len(words)} words > 300')
    except IndexError:
        fails.append('abstract heading not found')
    # 6 tables and sections
    small = set()
    ack = [p for p in body.iter(q('p')) if ''.join(x.text or '' for x in p.iter(q('t'))).strip() == 'Acknowledgements'][0]
    template_tbls = set()
    for el in body:
        if el is ack or ack in el.iter(q('p')):
            break
        if el.tag == q('tbl'):
            template_tbls.add(el)  # title and approval pages copied from Template.docx
    for tbl in body.iter(q('tbl')):
        if tbl in template_tbls:
            continue
        for sz in tbl.iter(q('sz')):
            if sz.get(q('val')) != '24': small.add(sz.get(q('val')))
    sects = list(body.iter(q('sectPr')))
    land = sum(1 for s in sects if s.find('w:pgSz', NS).get(q('orient')) == 'landscape')
    print('6 table font sizes other than 12 pt:', sorted(small) or 'none', '| sections', len(sects), 'landscape', land)
    if small: fails.append(f'table runs not at 12 pt: {small}')
    if land: fails.append(f'{land} landscape section(s); the author asked for portrait pages only (13/10)')
    for s in sects:
        pm = s.find('w:pgMar', NS); pz = s.find('w:pgSz', NS)
        m = {k: pm.get(q(k)) for k in ('top', 'bottom', 'left', 'right')}
        want = ({'top': '2160', 'bottom': '1440', 'left': '1440', 'right': '1440'} if pz.get(q('orient')) == 'landscape'
                else {'top': '1440', 'bottom': '1440', 'left': '2160', 'right': '1440'})
        if m != want: fails.append(f'margins {m} != {want}')
    for f in fails:
        print('FAIL', f)
    print('RESULT', 'PASS' if not fails else f'{len(fails)} FAIL')
    return 1 if fails else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
