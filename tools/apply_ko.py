"""윤문 결과 검증·적용.

사용법: python3 -I tools/apply_ko.py <workflow_result.json>
- HTML 조각: 인용 버튼 순서, 숫자 목록, 태그 구조가 원본과 같을 때만 src/template.html에 반영한다.
- 사실 진술·검증 메모·기사 메모: 숫자 목록이 같을 때만 data/ko/*_display.json에 쓴다.
통과하지 못한 항목은 원본을 유지하고 목록으로 출력한다.
"""
import json, re, sys, os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ROOT, *p)
NUM = re.compile(r'\d+(?:[.,]\d+)*')

def nums(t):
    t = re.sub(r'<[^>]+>', ' ', t)
    return Counter(NUM.findall(t))

def cites(h):
    return re.findall(r'data-f="([^"]+)"', h)

def skeleton(h):
    # 문단 나누기(<p>, </p> 추가)는 허용한다. 나머지 태그는 순서까지 같아야 한다.
    return [re.sub(r'\s+', ' ', x) for x in re.findall(r'<[^>]+>', h) if x not in ('<p>', '</p>')]

res = json.load(open(sys.argv[1], encoding='utf-8'))
res = res['result'] if isinstance(res, dict) and 'result' in res else res
src_chunks = json.load(open(D('data', 'ko', 'src_chunks.json'), encoding='utf-8'))
src_facts = json.load(open(D('data', 'ko', 'src_facts.json'), encoding='utf-8'))
src_misc = {x['key']: x['text'] for x in json.load(open(D('data', 'ko', 'in_misc.json'), encoding='utf-8'))}

tpl = open(D('src', 'template.html'), encoding='utf-8').read()
rej, ok_html, facts_out, misc_out = [], 0, {}, {}
for job in res:
    for it in (job.get('items') or []):
        k = it['key']
        if job['job'].startswith('html'):
            old = src_chunks[int(k)]; new = it.get('html') or ''
            why = []
            if cites(old) != cites(new): why.append('cite order')
            if nums(old) != nums(new): why.append('numbers ' + str((nums(old) - nums(new)) + (nums(new) - nums(old))))
            if skeleton(old) != skeleton(new): why.append('tags')
            if '—' in new: why.append('em dash')
            if why:
                rej.append(('html', k, why)); continue
            assert tpl.count(old) == 1, ('chunk not unique', k)
            tpl = tpl.replace(old, new); ok_html += 1
        elif job['job'].startswith('facts'):
            o = src_facts.get(k)
            if not o: rej.append(('fact', k, ['unknown'])); continue
            c, n = it.get('claim') or o['claim'], it.get('note', o['note'])
            why = []
            if nums(o['claim']) != nums(c): why.append('claim numbers')
            if nums(o['note']) != nums(n or ''): why.append('note numbers')
            if why: rej.append(('fact', k, why)); continue
            facts_out[k] = dict(claim=c, note=n)
        else:
            o = src_misc.get(k); t = it.get('text') or ''
            if o is None or nums(o) != nums(t): rej.append(('misc', k, ['numbers'])); continue
            misc_out[k] = t

open(D('src', 'template.html'), 'w', encoding='utf-8').write(tpl)
json.dump(facts_out, open(D('data', 'ko', 'facts_display.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(misc_out, open(D('data', 'ko', 'misc_display.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'html applied {ok_html}/{len(src_chunks) - 1}, facts {len(facts_out)}/{len(src_facts)}, misc {len(misc_out)}/{len(src_misc)}')
for r in rej:
    print('REJECT', r)
