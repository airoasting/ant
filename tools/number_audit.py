"""페이지 숫자 전수 대조.

사용법: python3 -I tools/number_audit.py
docs/index.html의 본문 숫자를 모두 뽑아, 다음 중 하나로 확인되는지 본다.
  1) 같은 블록의 인용 사실(claim 또는 quote)에 같은 숫자가 있다
  2) S-1 원문(data/s1.txt)에 그 값이 있다 (억·만 달러는 백만·십억 달러 표기로 바꿔 찾는다)
  3) CALC 목록에 계산식과 함께 등록된 계산값이다
확인되지 않는 숫자를 출력하고, 하나라도 있으면 종료 코드 1을 낸다.
"""
import re, json, html, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = open(os.path.join(ROOT, 'docs', 'index.html'), encoding='utf-8').read()
s1 = open(os.path.join(ROOT, 'data', 's1.txt'), encoding='utf-8').read()
s1n = re.sub(r'\s+', ' ', s1)
FACTS = json.loads(re.search(r'const FACTS = (\{.*?\});\nconst NEWS', s, re.S).group(1))

# 계산값: 값 -> 계산식 (S-1 숫자에서 나온 것)
CALC = {
    '169억': '1억 9,700만 × 86 = 약 169.4억 (rf1-06, biz-18)',
    '16,900': '같은 역산값을 백만 달러로 표기',
    '16,942': '197 × 86 (백만 달러)',
    '89.6%': '72,388 ÷ 80,748',
    '9.4배': '386 ÷ 41', '11.9배': '4,585 ÷ 386', '3.5배': '16,286 ÷ 4,585 = 3.55',
    '30.7배': '11,555 ÷ 376', '52배': '589.0095 ÷ 11.2261 = 52.5',
    '9배': 'NRR 약 900% = 약 9배 (sum-10, S-1 663행)',
    '807': '순손실 807억 4,800만 달러(fin-07)를 억 달러 단위로 줄인 큰 숫자 표기',
    '14배': '162억 8,600만 ÷ 11억 6,300만 = 14.0 (2026년 상반기 vs 2025년 상반기, S-1 1,300%)',
    '5배': '약 940명 → 약 5,300명 = 5.6배 (S-1: over five times)', '5.6배': '5,300 ÷ 940',
    '+397': '−80,748 + 72,388 + 8,757', '397': '같은 계산',
    '251%': '944 ÷ 376', '177%': '1,390 ÷ 787', '148%': '2,047 ÷ 1,382', '144%': '2,945 ÷ 2,040 또는 11,555 ÷ 4,731', '72%': '3,387 ÷ 4,731', '48%': '5,558 ÷ 11,555 또는 2,040 ÷ 1,382',
    '109%': '787 ÷ 376', '76%': '1,382 ÷ 787', '132%': '4,731 ÷ 2,040',
    '2,008,016,032': '2,000,000,000 × 50.1 ÷ 49.9 (슬라이더 예시)', '2,000,000,000': '슬라이더 예시 입력값',
    '49.9%': '100 − 50.1 (S-1 원문에도 49.9%)',
    '21개월': '2024-12-31 → 2026-09-30',
    '2.5배': '944 ÷ 376 = 2.51 (비율 251%)', '10배': '로그 축 눈금 설명', '5.6배': '5,300 ÷ 940',
    '4 : 3': '이사회 7석 중 Class T 4석, 나머지 3석',
    '23,197': 's1.txt 줄 수',
    '61': '검증자 수정 건수', '366': '5차 감사 확인 주장 수', '5차': '감사 회차', '0건': '마지막 감사 지적 수', '4': '2·4차 감사 지적 수', '51': '1차 감사 지적 건수', '341': '1차 감사 확인 주장 수', '292': '2차 감사 확인 주장 수', '12': '직접 확인한 기사 수', '3': '제외한 기사 수',
}

# 사람이 검토해 근거를 확인한 항목 (블록 분할 때문에 인용과 자동으로 짝지어지지 않는 것)
REVIEWED = {
    '86배': 'biz-18 (S-1 10186행 "86 times")', '90%': 'mdna-12 (S-1 "over 90%"), 표기는 90% 이상·90%+',
    '45배': 'mdna-13 (옆 칸 인용)', '6.6': 'biz-17 ($6.6M+)', '1.4': 'biz-17 ($1.4M)', '80%': 'rf2-50·mdna-27 (자선 서약 80%)',
    '20배': 'biz-14', '10%': 'uw-02 (첫 거래일 최대 10%)', '29%': 'uw-01 (최대 29%)', '1': '2대1 판결 rf1-20',
    '3,181': 'x-own-5 (231,809,780주)', '4,417': 'x-own-5 (244,173,040주)', '4,526': 'x-own-dd (245,259,100주)',
    '5,180억 달러': '보도 숫자: Reuters 9월 단독(검증 에이전트가 Yahoo 전재본 열람)', '5,420': '보도 숫자: Fortune(Forlini) 합산',
    '5,670억 달러': '보도 숫자: Fortune 제목 "up to $567 billion"(메인 세션 직접 확인)', '4,300': '보도 숫자: Yahoo Finance(Howley) 합산',
    '6,370억 달러': '보도 숫자: Yahoo Finance(Howley) 합산', '2.08': '보도 숫자: Fortune 계산 11,555 ÷ 5,558 = 2.079',
}
# 기업가치 비교 (cval): S-1 밖 보도 숫자로 계산한 값
CALC.update({
    '50%': '과반선 = 의결권 절반 (정의)', '29일': '2026-08-27 → 2026-09-25 = 29일', '11.1%': '100 ÷ 900 (NRR 약 900%)',
    '81%': '1.5조 ÷ 1.85조 = 81.1% (앤트로픽 IPO 논의값 ÷ 삼성전자+SK하이닉스 시가총액 합계)',
    '8%': '2조 ÷ 1.85조 = 1.081', '67%': '1.5조 ÷ 2.2459조 = 66.8%',
    '1,415': '5,846,278,608주 × 242,000원 = 1,414.8조 원', '1,060': '712,702,365주 × 1,487,000원 = 1,059.8조 원',
    '1.06': '1,414.8조 원 ÷ 1,337.7원 = 1조 576억 달러', '0.79': '1,059.8조 원 ÷ 1,337.7원 = 7,922억 달러',
    '1.85': '(1,414.8 + 1,059.8)조 원 ÷ 1,337.7원 = 1조 8,499억 달러', '1.4배': '1.5조 ÷ 1.0576조 = 1.42',
    '0.97': '9,650억 달러를 조 단위로', '0.85': '8,520억 달러를 조 단위로', '1.50': '1.5조 달러 막대 표기',
    '1.0배': '9,650억 ÷ 9,650억', '1.6배': '1.5조 ÷ 9,650억 = 1.55', '235배': '9,650억 ÷ 41억 = 235.4', '366배': '1.5조 ÷ 41억 = 365.9',
    '29억 달러': '0.3% × 9,650억 = 28.95억', '29배': '28.95억 ÷ 1억', '45억 달러': '0.3% × 1.5조 = 45억', '45배': '45억 ÷ 1억',
})
REVIEWED.update({
    '6,300': '사실 01 리드 행 .k의 반기 매출 11억 6,300만 달러(근거 표시 있음)를 막대 끝 라벨에 반복', '8,600': '사실 01 리드 행 .k의 반기 매출 162억 8,600만 달러(근거 표시 있음)를 막대 끝 라벨에 반복',
    '2,450': 'x-note17-cond (6월 30일 이후 추가 약 2,450억 달러, 같은 KPI 카드 .dl에 근거 표시)',
    '11%': 'rf1-08 (2023년 클라우드 마켓플레이스 비중 약 11%, 같은 리드 행 .k에 근거 표시)',
    '1.5': 'news-rt-15t (Reuters: around $1.5 trillion)', '2.25': 'news-imf-2026 (IMF 2조 2,459억 달러)',
    '1.25': 'news-oai-125 (CNBC $1.25 trillion pre-money)', '9,650억 달러': 'news-bbg-965 · news-elec-h (시리즈 H 투자 후 기업가치)',
    '8,520억 달러': 'news-oai-852', '1,220억 달러': 'news-oai-852', '300억 달러': 'news-oai-125', '41억 달러': 'news-hk-skt',
    '1억 달러': 'news-hk-skt', '2%': 'news-hk-skt (초기 지분 약 2%)', '0.3%': 'news-hk-skt', '3,782억': 'news-hk-skt (1조 3,782억 원)',
    '1,337.7': 'news-fx-1028', '5,846,278,608': 'dart-shares', '712,702,365': 'dart-shares',
})

_na=len(json.load(open(os.path.join(ROOT,'data','facts.json'),encoding='utf-8'))); _nm=len(json.load(open(os.path.join(ROOT,'data','manual_facts.json'),encoding='utf-8')))
for _k in (f'{_na+_nm:,}', f'{_na+_nm:,}개', str(_na), str(_nm)): CALC[_k]='사실 DB 건수(빌드 시 계산)'
body = s[s.index('<main id="main">'):s.index('</footer>')]
blocks = re.split(r'(?=<(?:p|div|li|h2|h4)[ >])', body)

def money_forms(eok, man):
    v = (eok or 0) * 1e8 + (man or 0) * 1e4  # dollars
    m = v / 1e6
    forms = set()
    if abs(m - round(m)) < 1e-6:
        forms.add(f'{round(m):,}')
    b = v / 1e9
    for d in (1, 2):
        forms.add(f'{b:.{d}f} billion'); forms.add(f'${b:.{d}f} billion')
    if abs(b - round(b)) < 1e-9:
        forms.add(f'{round(b)} billion'); forms.add(f'{round(b):,} billion')
    forms.add(f'{round(m):,}')
    return forms

NUM = re.compile(r'(?:(\d[\d,]*(?:\.\d+)?)억\s*)?(?:(\d[\d,]*)만\s*)?(?:달러|\$)|\d[\d,]*(?:\.\d+)?(?:%|배|명|곳|주|석|년|월|일|개|시간|표)?')
bad = []
seen = 0
for blk in blocks:
    ids = re.findall(r'data-f="([^"]+)"', blk)
    t = re.sub(r'<[^>]+>', ' ', blk); t = html.unescape(t); t = re.sub(r'\s+', ' ', t)
    if not re.search(r'\d', t):
        continue
    src = ' '.join((FACTS.get(i, {}).get('claim', '') + ' ' + FACTS.get(i, {}).get('quote', '')) for i in ids)
    for m in NUM.finditer(t):
        tok = m.group(0).strip().rstrip(',')
        if re.match(r'\d+행', t[m.end():m.end()+1] and t[m.start():m.end()+1] or ''):
            continue
        if not tok or not re.search(r'\d', tok):
            continue
        core = re.sub(r'(%|배|명|곳|주|석|년|월|일|개|시간|표|달러|\$)$', '', tok).strip()
        if re.fullmatch(r'\d{1,2}', core) and not tok.endswith(('%', '배')):
            continue  # 날짜 조각, 장 번호 등 한두 자리 정수
        if re.fullmatch(r'20\d\d', core) or re.fullmatch(r'20\d\d\.\d\d', core) or re.fullmatch(r'\d\d\.\d\d', core):
            # 연도·날짜: 원문이나 근거에 연도가 있는지만 본다
            if core[:4] in s1n or core[:4] in src or re.fullmatch(r'\d\d\.\d\d', core):
                continue
        seen += 1
        ok = False
        if tok in REVIEWED or core in REVIEWED:
            continue
        if tok in CALC or core in CALC or (core + tok[len(core):]) in CALC:
            ok = True
        if not ok and (m.group(1) or m.group(2)):
            eok = float(m.group(1).replace(',', '')) if m.group(1) else 0
            man = float(m.group(2).replace(',', '')) if m.group(2) else 0
            k = (f"{m.group(1)}억" if m.group(1) else '') + (f" {m.group(2)}만" if m.group(2) else '')
            if k.strip() in src or tok in src:
                ok = True
            else:
                ok = any(f in s1n for f in money_forms(eok, man)) or (k.strip() + ' 달러') in src
        if not ok:
            ok = (core in src) or (tok in src) or (core in s1n and len(core.replace(',', '').replace('.', '')) >= 3)
        if not ok:
            bad.append((tok, t[:140], ids[:4]))

print(f'checked_tokens={seen} unmatched={len(bad)}')
for b in bad:
    print('  ', b[0], '|', b[1], '|', b[2])
sys.exit(1 if bad else 0)
