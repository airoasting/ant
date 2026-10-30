"""S-1 스토리 페이지 빌드.

사용법: python3 -I tools/build.py   (프로젝트 루트에서)
1) src/template.html 안의 data-f="..." 인용 ID를 모두 모은다.
2) data/facts.json + data/manual_facts.json + 아래 EXTERNAL에서 찾는다. 하나라도 없으면 실패.
3) S-1 인용은 data/s1.txt와 공백 정규화 후 대조한다. 원문에 없으면 실패.
4) 쓰인 사실만 FACTS로, 언론 카드는 NEWS로 넣어 docs/index.html(바로 열리는 완성 문서)과 build/artifact.html(아티팩트 발행용 본문 조각)을 만든다.
"""
import json, re, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ROOT, *p)

def norm(s):
    s = (s.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
          .replace('—', '-').replace('–', '-').replace('&amp;', '&'))
    return re.sub(r'\s+', '', s)  # 줄바꿈 위치 차이를 무시하려고 공백을 모두 제거해 비교

EDGAR = 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0002130357&type=&dateb=&owner=include&count=40'
EXTERNAL = {
    'edgar-hist': dict(ext=True, label='EDGAR', head='SEC EDGAR · 제출 목록',
        claim='SEC EDGAR에 따르면 앤트로픽은 2026년 6월 1일 비공개 초안(DRS)을 내고, 7월 13일·8월 10일·9월 4일·10월 1일·10월 9일 다섯 차례 수정 초안(DRS/A)을 낸 뒤 10월 26일 S-1을 공개 제출했다.',
        quote='2026-10-26 S-1 · 2026-10-09 DRS/A · 2026-10-01 DRS/A · 2026-09-04 DRS/A · 2026-08-10 DRS/A · 2026-07-13 DRS/A · 2026-06-01 DRS',
        note='EDGAR 회사 페이지(CIK 0002130357)의 제출 목록에서 직접 확인했다.', url=EDGAR, urlLabel='SEC EDGAR · Anthropic, PBC 제출 이력'),
    'news-bbg-965': dict(ext=True, label='Bloomberg', head='Bloomberg · 2026-05-28',
        claim='Bloomberg는 2026년 5월 28일 앤트로픽이 9,650억 달러 기업가치로 자금을 조달해 OpenAI의 기업가치를 넘어섰다고 보도했다. 이 숫자는 S-1에 없다.',
        quote='Anthropic Raises at $965 Billion Valuation, Eclipsing OpenAI',
        note='검증 에이전트가 기사 페이지를 열어 제목, 바이라인, 날짜를 확인했다. S-1 밖 정보다.',
        url='https://news.bgov.com/private-equity/anthropic-raises-at-965-billion-valuation-eclipsing-openai-1', urlLabel='Bloomberg (2026-05-28)'),
    'news-rt-15t': dict(ext=True, label='Reuters', head='Reuters · 2026-10-15',
        claim='Reuters는 2026년 10월 15일 일부 투자자가 10월 14일 투자자 설명회 뒤 앤트로픽의 11월 공모 기업가치로 약 1.5조 달러를 논의했으며, 이는 회사와 투자자가 이전에 거론한 약 2조 달러보다 낮다고 보도했다. S-1 밖 정보다.',
        quote='discussed a valuation of around $1.5 trillion ... the roughly $2 trillion valuation that the company and investors had previously floated',
        note='Investing.com의 Reuters 인용 기사를 직접 열어 문구와 날짜를 확인했다. 확정된 공모가가 아니다.',
        url='https://www.investing.com/news/stock-market-news/some-investors-push-anthropic-to-cut-ipo-valuation-to-15-trillion--report-4952696', urlLabel='Investing.com (Reuters 인용, 2026-10-15)'),
    'news-oai-852': dict(ext=True, label='Bloomberg', head='Bloomberg · 2026-03-31',
        claim='OpenAI는 2026년 3월 31일 투자 후 기업가치 8,520억 달러로 1,220억 달러 조달을 마쳤다. S-1 밖 정보다.',
        quote='OpenAI Valued at $852 Billion After Completing $122 Billion Round',
        note='Bloomberg 기사 제목과 날짜를 검색 결과로 확인했고, Reuters(2026-05-28)도 "last valued at $852 billion post-money in March"라고 썼다.',
        url='https://www.bloomberg.com/news/articles/2026-03-31/openai-valued-at-852-billion-after-completing-122-billion-round', urlLabel='Bloomberg (2026-03-31)'),
    'news-oai-125': dict(ext=True, label='CNBC', head='CNBC · 2026-10-22',
        claim='CNBC는 2026년 10월 22일 OpenAI가 투자 전 기업가치 1.25조 달러로 최대 300억 달러를 조달하는 라운드를 마무리하고 있다고 소식통을 인용해 보도했다. 협상 단계의 숫자다.',
        quote='OpenAI nears up to $30 billion funding round at $1.25 trillion valuation led by UAE investors',
        note='CNBC 본문은 403으로 열리지 않아 검색 결과에서 제목, 날짜, URL을 확인했다. 1.25조 달러는 새 투자금을 넣기 전 가치다.',
        url='https://www.cnbc.com/2026/10/22/openai-funding-round-uae-investors.html', urlLabel='CNBC (2026-10-22)'),
    'news-imf-2026': dict(ext=True, label='경향신문', head='경향신문 · 2026-10-13',
        claim='IMF 10월 세계경제전망은 2026년 한국 명목 GDP를 2조 2,459억 달러로 전망했다. S-1 밖 정보다.',
        quote='명목GDP는 올해 2조2459억달러로 사상 첫 2조달러를 돌파할 것으로 예상했다.',
        note='경향신문 김경민 기자 기사를 직접 열어 확인했다.', url='https://khan.co.kr/article/202610131103001', urlLabel='경향신문 (2026-10-13)'),
    'news-krx-1028': dict(ext=True, label='서울신문', head='서울신문 · 2026-10-28',
        claim='2026년 10월 28일 삼성전자는 9.01% 오른 24만 2,000원, SK하이닉스는 10.89% 오른 148만 7,000원에 마감했다.',
        quote='삼성전자(005930)는 9.01% 오른 242,000원, SK하이닉스(000660)는 10.89% 오른 1,487,000원에 마감했다.',
        note='서울신문 정연호 기자 기사를 직접 열어 확인했다.', url='https://www.seoul.co.kr/news/economy/securities/2026/10/28/20261028500293', urlLabel='서울신문 (2026-10-28)'),
    'news-fx-1028': dict(ext=True, label='뉴시스', head='뉴시스 · 2026-10-28',
        claim='2026년 10월 28일 원·달러 환율은 14.0원 오른 1,337.7원에 마감했다.',
        quote='원·달러 환율, 14.0원 오른 1337.7원 마감', note='뉴시스 김래현 기자 기사를 직접 열어 확인했다.',
        url='https://www.newsis.com/view/NISX20261028_0003845022', urlLabel='뉴시스 (2026-10-28)'),
    'dart-shares': dict(ext=True, label='DART', head='DART · 2026년 반기보고서',
        claim='2026년 6월 30일 기준 발행주식 수는 삼성전자 보통주 5,846,278,608주, SK하이닉스 보통주 712,702,365주다. 시가총액은 10월 28일 종가에 이 주식 수를 곱해 계산했다(삼성전자 약 1,414.8조 원, SK하이닉스 약 1,059.8조 원).',
        quote='삼성전자 보통주 발행주식총수 5,846,278,608 · SK하이닉스 보통주 발행주식총수 712,702,365',
        note='DART 반기보고서 주식의 총수 현황에서 직접 확인했다. 우선주와 이후 자사주 소각은 반영하지 않았다.',
        url='https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260814003699', urlLabel='DART 삼성전자 반기보고서 (SK하이닉스: rcpNo 20260814003509)'),
    'news-hk-skt': dict(ext=True, label='한국경제', head='한국경제 · 2026-06-03',
        claim='SK텔레콤은 2023년 8월 앤트로픽에 1억 달러(당시 약 1,320억 원)를 투자했다. 당시 앤트로픽 기업가치는 41억 달러였고 지분은 약 2%였으나 이후 신주 발행으로 약 0.3%로 낮아졌다. 지난해 사업보고서의 앤트로픽 지분 가치는 1조 3,782억 원이다.',
        quote='2023년 8월 1억달러(당시 환율로 1320억원)를 앤스로픽에 투자했다. 당시 앤스로픽의 기업 가치는 41억달러로 평가받았다.',
        note='한국경제 김인엽 특파원·박한신 기자 기사를 직접 열어 확인했다. 지분율 0.3%는 기사 수치다.',
        url='https://www.hankyung.com/article/2026060236331', urlLabel='한국경제 (2026-06-03)'),
    'news-elec-h': dict(ext=True, label='디일렉', head='디일렉 · 2026-05-29',
        claim='삼성전자와 SK하이닉스는 마이크론과 함께 앤트로픽 시리즈 H(650억 달러, 투자 후 기업가치 9,650억 달러)에 참여했다. 개별 투자 금액은 공개되지 않았다.',
        quote='삼성전자와 SK하이닉스가 인공지능(AI) 기업 앤트로픽의 시리즈 투자에 참가했다.',
        note='디일렉 이준 기자 기사를 직접 열어 확인했다.', url='https://www.thelec.kr/news/articleView.html?idxno=57382', urlLabel='디일렉 (2026-05-29)'),
    'news-khan-h': dict(ext=True, label='경향신문', head='경향신문 · 2026-05-31',
        claim='업계에 따르면 삼성전자와 SK하이닉스의 시리즈 H 투자금은 각각 조 단위로 알려졌다. 정확한 금액은 공개되지 않았다.',
        quote='삼성전자와 SK하이닉스의 투자금은 각각 조 단위로 알려졌다.',
        note='경향신문 김유진 기자 기사를 직접 열어 확인했다. 업계 전언이며 공시된 금액이 아니다.', url='https://www.khan.co.kr/article/202605311352001', urlLabel='경향신문 (2026-05-31)'),
}

# 언론 카드: news.json의 검증·tier1 기사에 짧은 대조 메모를 붙인다(인덱스는 news.json 순서).
CHECK = {
    # 0, 3, 5: 메인 세션이 원문을 직접 열지 못해(403) 제외
    # 0: ('2026.10.26', False, '순손실 807억 달러는 S-1과 일치. 4,170억 달러는 2025년 말 이후 새로 맺은 계약분이다.'),
    1: ('2026.10.26', False, '티커 ANT, 나스닥 글로벌 셀렉트, 인수단 "GS·MS 외 20곳"이 S-1 표지와 일치한다.'),
    2: ('2026.10.26', True, '제출 직전 예고 기사. 제출 시각과 공모 규모 기대는 소식통 기반이라 S-1로 대조할 수 없다.'),
    # 3: ('2026.10.26', False, '예측시장 반응을 다룬 기사. S-1과 대조할 숫자는 없다.'),
    4: ('2026.09.28', True, '비공개본 단독. 2025년 매출·순손실은 공개 S-1과 일치하지만 5,180억 달러 총액은 공개본에 없다.'),
    # 5: ('2026.06.01', True, '비공개 제출(DRS) 보도. S-1 이전 기사다.'),
    6: ('2026.06.01', True, 'DRS 보도. 전재본으로 확인했다. 연환산 매출 470억 달러는 S-1 숫자가 아니다.'),
    7: ('2026.05.28', True, '마지막 사모 라운드 9,650억 달러. S-1에는 없는 숫자다.'),
    8: ('2026.10.26', False, '매출, 순손실, 영업현금흐름이 S-1과 일치한다. 컴퓨트 1달러당 2.08달러는 기자 계산이다.'),
    9: ('2026.10.26', False, '4,170억 달러의 시점 표현과 5,420억~5,670억 달러 합산은 S-1 원문과 다르다.'),
    10: ('2026.10.26', False, '존망 위험 문구는 일치. "halted training"은 원문 "delay pre-training"과 다르다.'),
    11: ('2026.10.26', False, '인용문은 S-1과 일치. "R&D용 컴퓨트 97억 달러"는 기능별 R&D 비용 총액이다.'),
    12: ('2026.10.26', False, '매출, 영업손실, 고객 구간, 50.1%가 모두 S-1과 일치한다.'),
    13: ('2026.10.26', False, 'NRR 900%는 일치. 20배 비교의 단위는 고객사가 아니라 사용자다.'),
    14: ('2026.10.26', False, 'Class F 1주 50.1%는 일치. "94쪽이 AI 위험"은 위험요인 섹션 전체 분량이다.'),
}
URL_FIX = {2: 'https://finance.yahoo.com/technology/ai/articles/anthropic-said-plan-public-filing-115338000.html'}
HEADLINE_FIX = {  # 검증자가 본문 제목을 확인한 경우 본문 제목을 쓴다
    10: "Anthropic's risk factors include the end of humanity, a feud with the Pentagon, and CEO Dario Amodei's reputation",
}

def main():
    tpl = open(D('src', 'template.html'), encoding='utf-8').read()
    ids = list(dict.fromkeys(re.findall(r'data-f="([^"]+)"', tpl)))
    facts = {f['id']: f for f in json.load(open(D('data', 'facts.json'), encoding='utf-8'))}
    for f in json.load(open(D('data', 'manual_facts.json'), encoding='utf-8')):
        facts[f['id']] = f
    s1 = norm(open(D('data', 's1.txt'), encoding='utf-8').read())

    # 윤문본(합쇼체) 표시 문구가 있으면 쓴다. 숫자 보존은 tools/apply_ko.py가 확인했다.
    kof = D('data', 'ko', 'facts_display.json'); kom = D('data', 'ko', 'misc_display.json')
    KO_F = json.load(open(kof, encoding='utf-8')) if os.path.exists(kof) else {}
    KO_M = json.load(open(kom, encoding='utf-8')) if os.path.exists(kom) else {}
    out, missing, badquote = {}, [], []
    for i in ids:
        if i in EXTERNAL:
            e = dict(EXTERNAL[i]); ek = 'ext' + str(list(EXTERNAL).index(i))
            if ek in KO_M: e['claim'] = KO_M[ek]
            out[i] = e; continue
        f = facts.get(i)
        if not f:
            missing.append(i); continue
        q = norm(f['quote'])
        if q[:200] not in s1:
            badquote.append(i)
        out[i] = dict(line=f['line'], claim=KO_F.get(i, {}).get('claim', f['claim_ko']), quote=f['quote'].replace('&amp;', '&'),
                      note=KO_F.get(i, {}).get('note', f.get('verify_note', '')))
    if missing or badquote:
        print('MISSING', missing, 'BADQUOTE', badquote); sys.exit(1)

    news = json.load(open(D('data', 'news.json'), encoding='utf-8'))['articles']
    cards = []
    for idx, a in enumerate(news):
        if idx not in CHECK or not a.get('verified') or not a.get('tier1'):
            continue
        date, pre, check = CHECK[idx]
        cards.append(dict(outlet=a['outlet'], date=date, headline=HEADLINE_FIX.get(idx, a['headline']), url=URL_FIX.get(idx, a['url']),
                          angle=KO_M.get('angle' + str(idx), a['angle_ko']), check='S-1 대조 · ' + KO_M.get('check' + str(idx), check), pre=pre))
    cards.sort(key=lambda c: (c['pre'], c['date']), reverse=False)
    post = [c for c in cards if not c['pre']]; prev = sorted([c for c in cards if c['pre']], key=lambda c: c['date'], reverse=True)
    cards = post + prev

    total = len(facts)
    n_agent = len(json.load(open(D('data', 'facts.json'), encoding='utf-8')))
    n_manual = total - n_agent
    html = (tpl.replace('/*__FACTS__*/{}', json.dumps(out, ensure_ascii=False))
               .replace('/*__NEWS__*/[]', json.dumps(cards, ensure_ascii=False))
               .replace('__TOTAL__', f'{total:,}').replace('__MANUAL__', str(n_manual)).replace('__AGENT__', str(n_agent)))
    # 완성 문서 하나로 쓴다: 머리(제목·메타·스타일)는 <head>에, 나머지는 <body>에 넣는다
    cut = html.index('</style>') + len('</style>')
    doc = ('<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
           '<style>:root{padding-top:env(safe-area-inset-top);padding-bottom:env(safe-area-inset-bottom)}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n'
           + html[:cut] + '\n</head>\n<body>\n' + html[cut:].lstrip('\n') + '\n</body>\n</html>\n')
    os.makedirs(D('docs'), exist_ok=True)
    open(D('docs', 'index.html'), 'w', encoding='utf-8').write(doc)
    # 아티팩트 발행용 본문 조각: 발행 서버가 문서 골격을 직접 씌우므로 골격 없이 둔다
    os.makedirs(D('build'), exist_ok=True)
    open(D('build', 'artifact.html'), 'w', encoding='utf-8').write(html)
    print(f'ids={len(ids)} facts_db={total} news_cards={len(cards)} size={len(html.encode())/1024:.0f}KB')

if __name__ == '__main__':
    main()
