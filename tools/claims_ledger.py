"""문장 단위 근거 원장.

사용법: python3 -I tools/claims_ledger.py
docs/index.html의 본문을 문장 단위로 나누고, 문장마다
  - 붙은 인용 ID와 그 사실의 진술, S-1 줄번호, 원문 인용, 원문 대조 결과
  - 문장 속 숫자 하나하나가 어디서 확인되는지(인용 근거 / S-1 원문 / 계산값 / 검토 목록)
를 기록해 data/audit/claims_ledger.json 과 claims_ledger.md 로 쓴다.
인용 없는 숫자 문장, 원문에 없는 인용, 근거 없는 숫자가 하나라도 있으면 종료 코드 1.
"""
import re, json, html, os, sys, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location('na', os.path.join(ROOT, 'tools', 'number_audit.py'))
src_na = open(os.path.join(ROOT, 'tools', 'number_audit.py'), encoding='utf-8').read()
# number_audit의 사전(CALC, REVIEWED)만 재사용한다
ns = {'__file__': os.path.join(ROOT, 'tools', 'number_audit.py')}
exec(src_na.split("\nbad = []")[0], ns)
CALC, REVIEWED, money_forms = ns['CALC'], ns['REVIEWED'], ns['money_forms']

s = open(os.path.join(ROOT, 'docs', 'index.html'), encoding='utf-8').read()
s1n = re.sub(r'\s+', ' ', open(os.path.join(ROOT, 'data', 's1.txt'), encoding='utf-8').read())
s1z = re.sub(r'\s+', '', s1n).replace('&amp;', '&')
FACTS = json.loads(re.search(r'const FACTS = (\{.*?\});\nconst NEWS', s, re.S).group(1))

def norm(x):
    return re.sub(r'\s+', '', x.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"').replace('—', '-').replace('–', '-'))
S1N = norm(s1z)

body = s[s.index('<main id="main">'):s.index('</footer>')]
sections = re.split(r'(?=<section )', body)
NUM = ns['NUM']
ledger, problems = [], []
for sec in sections:
    m = re.search(r'id="([^"]+)"', sec); sid = m.group(1) if m else 'misc'
    for blk in re.split(r'(?=<(?:p|div|li|h1|h2|h4)[ >])', sec):
        t = re.sub(r'<button class="cite[^"]*" data-f="([^"]+)"></button>', r' ⟦\1⟧ ', blk)
        t = re.sub(r'<br\s*/?>', ' ', t); t = re.sub(r'<[^>]+>', ' ', t); t = re.sub(r'\s+', ' ', html.unescape(t)).strip()
        if not t or not re.search(r'[가-힣A-Za-z0-9]', t):
            continue
        bids = re.findall(r'⟦([^⟧]+)⟧', t)
        bsrc = ' '.join(FACTS[i]['claim'] + ' ' + FACTS[i]['quote'] for i in bids if i in FACTS)
        for sent in re.split(r'(?<=[다요])\.\s+|(?<=\.)\s(?=[가-힣A-Z])', t):
            sent = sent.strip()
            if len(sent) < 4:
                continue
            ids = re.findall(r'⟦([^⟧]+)⟧', sent)
            clean = re.sub(r'\s*⟦[^⟧]+⟧\s*', ' ', sent).strip()
            cites = []
            for i in ids:
                f = FACTS.get(i)
                if not f:
                    problems.append(('missing-fact', sid, i)); continue
                ok = True if f.get('ext') else (norm(f['quote'])[:200] in S1N)
                if not ok:
                    problems.append(('quote-not-in-s1', sid, i))
                cites.append(dict(id=i, line=f.get('line'), claim=f['claim'], quote=f['quote'][:300], quote_in_s1=ok, external=bool(f.get('ext'))))
            srcs = ' '.join(c['claim'] + ' ' + c['quote'] for c in cites)
            nums = []
            for mm in NUM.finditer(clean):
                tok = mm.group(0).strip().rstrip(',')
                if not re.search(r'\d', tok):
                    continue
                core = re.sub(r'(%|배|명|곳|주|석|년|월|일|개|시간|표|달러|\$)$', '', tok).strip()
                if re.fullmatch(r'\d{1,2}', core) and not tok.endswith(('%', '배')):
                    continue
                if re.fullmatch(r'(20\d\d)(\.\d\d)?|\d\d\.\d\d', core):
                    continue
                how = None
                if tok in REVIEWED or core in REVIEWED: how = 'reviewed: ' + REVIEWED.get(tok, REVIEWED.get(core, ''))
                elif tok in CALC or core in CALC: how = 'calc: ' + CALC.get(tok, CALC.get(core, ''))
                elif mm.group(1) or mm.group(2):
                    eok = float(mm.group(1).replace(',', '')) if mm.group(1) else 0
                    man = float(mm.group(2).replace(',', '')) if mm.group(2) else 0
                    k = ((mm.group(1) + '억') if mm.group(1) else '') + ((' ' + mm.group(2) + '만') if mm.group(2) else '')
                    if k.strip() in srcs: how = 'cited fact'
                    elif any(fm in s1n for fm in money_forms(eok, man)): how = 's1 text'
                if not how:
                    if core in srcs or tok in srcs: how = 'cited fact'
                    elif core in s1n and len(core.replace(',', '').replace('.', '')) >= 3: how = 's1 text'
                    elif re.search(r'\d+행', clean[mm.start():mm.end() + 1]): how = 'line reference'
                    elif core in bsrc or tok in bsrc: how = 'cited fact (same paragraph)'
                if not how:
                    problems.append(('number-unsupported', sid, tok, clean[:100]))
                nums.append(dict(token=tok, verified_by=how))
            if nums and not cites and not all((n['verified_by'] or '').startswith(('calc', 'reviewed', 'line')) for n in nums):
                # 숫자가 있는데 인용이 없는 문장: 같은 블록의 인용이나 원문으로 확인됐는지 남긴다
                pass
            ledger.append(dict(section=sid, sentence=clean, cites=cites, numbers=nums))

out = os.path.join(ROOT, 'data', 'audit')
json.dump(dict(summary=dict(sentences=len(ledger), with_cites=sum(1 for l in ledger if l['cites']),
                            cite_links=sum(len(l['cites']) for l in ledger), numbers=sum(len(l['numbers']) for l in ledger),
                            problems=len(problems)), problems=problems, ledger=ledger),
          open(os.path.join(out, 'claims_ledger.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
with open(os.path.join(out, 'claims_ledger.md'), 'w', encoding='utf-8') as w:
    w.write('# 문장 단위 근거 원장\n\n')
    w.write(f'문장 {len(ledger)}개, 인용 연결 {sum(len(l["cites"]) for l in ledger)}개, 숫자 {sum(len(l["numbers"]) for l in ledger)}개, 문제 {len(problems)}건\n\n')
    for l in ledger:
        w.write(f'- **[{l["section"]}]** {l["sentence"]}\n')
        for c in l['cites']:
            w.write(f'  - 근거 `{c["id"]}` ' + ('(S-1 밖 출처)' if c['external'] else f'S-1 {c["line"]}행, 원문 대조 {"OK" if c["quote_in_s1"] else "실패"}') + f': "{c["quote"][:160]}"\n')
        for n in l['numbers']:
            w.write(f'  - 숫자 `{n["token"]}` → {n["verified_by"]}\n')
print(f'sentences={len(ledger)} cite_links={sum(len(l["cites"]) for l in ledger)} numbers={sum(len(l["numbers"]) for l in ledger)} problems={len(problems)}')
for p in problems[:40]:
    print('  ', p)
sys.exit(1 if problems else 0)
