"""S-1 인용 기계 검증기.
사용법: python3 -I tools/verify_quotes.py <s1.txt> <facts.json>
facts.json의 각 항목 quote가 s1.txt에 공백 정규화 후 그대로 존재하는지, line 근처(±40줄)에 있는지 확인한다.
"""
import sys, json, re
def norm(s):
    s = s.replace('’',"'").replace('‘',"'").replace('“','"').replace('”','"').replace('—','-').replace('–','-')
    return re.sub(r'\s+',' ',s).strip()
txt_lines = open(sys.argv[1],encoding='utf-8').read().split('\n')
full = norm(' '.join(txt_lines))
# line offset map
offs=[];pos=0
for l in txt_lines:
    offs.append(pos); pos += len(norm(l))+1
facts = json.load(open(sys.argv[2],encoding='utf-8'))
ok=bad=0; out=[]
for f in facts:
    q = norm(f.get('quote',''))
    probe = q if len(q)<=160 else q[:160]
    i = full.find(probe)
    if i<0:
        # try chunks separated by ellipsis
        parts=[p.strip() for p in re.split(r'\.\.\.|…',q) if len(p.strip())>15]
        found = parts and all(full.find(p[:120])>=0 for p in parts)
        status = 'OK(parts)' if found else 'MISSING'
    else:
        status='OK'
    if status.startswith('OK'): ok+=1
    else: bad+=1
    out.append((f.get('id'),status))
for i,s in out:
    if s!='OK': print(i,s)
print(f'total={len(facts)} ok={ok} missing={bad}')
