"""휴대폰 폭 넘침 검사.

사용법: python3 -I tools/overflow_probe.py
- docs/index.html 전체(장 숨김 없이)를 360·390·768·820px 틀(iframe)에 넣어 헤드리스 Chrome으로 연다.
- 4초 뒤 두 가지를 잰다.
  1) 페이지 가로 넘침: documentElement.scrollWidth - clientWidth
  2) 카드 밖으로 나간 줄바꿈 금지 묶음: .nw, .cg 가운데 오른쪽 끝이 감싼 카드(.panel/.prose/.km/.bl/.chfoot/.mcard 등)의 오른쪽 안쪽 경계를 넘는 것
  7) 글자 사이 간격: gap이 있는 flex 상자 안에서 낱말이 따로 flex 항목이 되어 띄어쓰기가 벌어지는 것
  6) 범례 항목과 차트 SVG 글자가 패널 안쪽 경계를 넘는 것(카드가 잘라 내서 페이지 넘침으로는 안 잡힌다)
  5) 태그라인 고정: 태그라인 구간 안으로 스크롤했을 때 .pin이 화면 맨 위(top 0)에 붙어 있는지
  4) 히어로 옆 숫자의 단위(.u)나 '약'이 숫자 묶음(b.vv) 밖에 남아 따로 줄을 차지하는 것
  3) 글자 크기 어긋남: 문단 안의 줄바꿈 묶음(.amt, .nw)이 부모 문단과 다른 크기·굵기로 그려지는 것(늦게 붙인 전역 규칙이 묶음에 새는 사고를 막는다)
- 하나라도 있으면 목록을 출력하고 종료 코드 1로 끝난다. 없으면 'overflow ok'를 출력한다.
캡처(capture.py)는 장을 하나씩 떼어 찍기 때문에 이런 넘침을 놓친다. 디자인 라운드마다 캡처와 함께 돌린다.
"""
import os, sys, json, subprocess, re, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

PROBE = r"""<!doctype html><meta charset="utf-8"><body style="margin:0">
<iframe id="f" src="../docs/index.html" style="width:__W__px;height:844px;border:0"></iframe>
<pre id="out">pending</pre>
<script>
const f=document.getElementById('f');
f.addEventListener('load',()=>setTimeout(()=>{
 f.contentDocument.querySelectorAll('.rv').forEach(e=>e.classList.add('in'));
},3000));
f.addEventListener('load',()=>setTimeout(()=>{
 const d=f.contentDocument, de=d.documentElement, W=f.contentWindow;
 const res={page:de.scrollWidth-de.clientWidth, groups:[]};
 const cardSel='.panel,.prose,.km,.bl,.chfoot,.mcard,.vs,.kband .herostats>div,.filings .wrap,.court>div,.bigstat .k';
 d.querySelectorAll('main .nw, main .cg').forEach(s=>{
  if(s.closest('.mwall')&&!s.closest('.mcard')) return;
  if(s.closest('.sr,.kbn')) return;
  if(s.closest('.rv:not(.in)')) { s.closest('.rv').classList.add('in'); }
  const r=s.getBoundingClientRect(); if(!r.width) return;
  const c=s.closest(cardSel); if(!c) return;
  const cr=c.getBoundingClientRect(), pr=parseFloat(W.getComputedStyle(c).paddingRight)||0;
  if(r.right>cr.right-pr+1) res.groups.push(s.textContent.trim().slice(0,40)+' @'+(c.className||c.tagName)+' '+Math.round(r.left)+'-'+Math.round(r.right)+' card '+Math.round(cr.right-pr)+' in '+(s.closest('section')||{}).id);
 });
 d.querySelectorAll('main .ch .bigstat .v .sharel>span').forEach(e=>{const r=e.getBoundingClientRect(); if(!r.width) return; const b=e.closest('.bigstat').getBoundingClientRect(); if(r.right>b.right+1) res.groups.push('hero label past edge: '+e.textContent.trim().slice(0,30)+' '+Math.round(r.right)+' > '+Math.round(b.right)+' in '+(e.closest('section')||{}).id);});
 res.type=[];
 d.querySelectorAll('main *').forEach(e=>{
  const cs=W.getComputedStyle(e); if(!/flex/.test(cs.display)) return; const g=parseFloat(cs.columnGap)||0; if(g<=0) return;
  if(!e.getBoundingClientRect().width) return;
  let words=0; e.childNodes.forEach(n=>{ if(n.nodeType===3&&n.textContent.trim()) words++; else if(n.nodeType===1&&n.tagName==='SPAN'&&(n.className==='nw'||n.className==='amt')) words++; });
  if(words>=2) res.type.push('words split into flex items (gap '+g+'px): '+e.textContent.trim().slice(0,30)+' in '+(e.closest('section')||{}).id);
 });
 d.querySelectorAll('main .panel .sub.lgs .lg, main .panel .vlegend>*, main .panel svg text').forEach(e=>{
  if(e.closest('.sr')) return; const r=e.getBoundingClientRect(); if(!r.width||!r.height) return;
  if(W.getComputedStyle(e).visibility==='hidden'||W.getComputedStyle(e).display==='none') return;
  const c=e.closest('.panel'), cr=c.getBoundingClientRect(), cs=W.getComputedStyle(c);
  const R=cr.right-(parseFloat(cs.paddingRight)||0)+3, L=cr.left+(parseFloat(cs.paddingLeft)||0)-3;
  if(r.right>R||r.left<L) res.groups.push('label past panel edge: '+e.textContent.trim().slice(0,30)+' '+Math.round(r.left)+'-'+Math.round(r.right)+' card '+Math.round(L)+'-'+Math.round(R)+' in '+(e.closest('section')||{}).id);
 });
 d.querySelectorAll('main .bigstat .k .amt, main .bigstat .k .nw, main .prose p .nw, main .panel .cap .nw, main .panel .sub .nw').forEach(e=>{
  const a=W.getComputedStyle(e), b=W.getComputedStyle(e.parentElement);
  if(Math.abs(parseFloat(a.fontSize)-parseFloat(b.fontSize))>0.5 || (e.classList.contains('amt') && a.fontWeight!==b.fontWeight))
   res.type.push(e.textContent.trim().slice(0,30)+' '+a.fontSize+'/'+a.fontWeight+' vs '+b.fontSize+'/'+b.fontWeight+' in '+(e.closest('section')||{}).id);
 });
 d.querySelectorAll('.bigstat .k .v2>small.u, .bigstat .k .v2>.approx').forEach(e=>res.type.push('unit outside figure: '+e.textContent.trim()+' in '+(e.closest('section')||{}).id));
 d.querySelectorAll('main small.u:not(.sp)').forEach(u=>{const p=u.previousSibling; if(p&&p.nodeType===3&&/[만억조]\s*$/.test(p.textContent)) res.type.push('unit needs word space: '+p.textContent.trim().slice(-8)+u.textContent);});
 const pw=d.querySelector('.tagline.pinwrap'), pin=pw&&pw.querySelector('.pin');
 if(pin){ const y=pw.getBoundingClientRect().top+W.scrollY+200; d.documentElement.style.scrollBehavior='auto'; d.documentElement.scrollTop=y;
  setTimeout(()=>{ const t=Math.round(pin.getBoundingClientRect().top); if(Math.abs(t)>1) res.type.push('tagline not pinned: top='+t); document.getElementById('out').textContent='RESULT'+JSON.stringify(res); },400);
 } else document.getElementById('out').textContent='RESULT'+JSON.stringify(res);
},4000));
</script>"""


def run(width):
    probe = os.path.join(ROOT, 'build', f'zz_overflow_probe_{width}.html')
    with open(probe, 'w', encoding='utf-8') as fh:
        fh.write(PROBE.replace('__W__', str(width)))
    out = subprocess.run([CHROME, '--headless=new', '--blink-settings=primaryPointerType=2,availablePointerTypes=2,primaryHoverType=1,availableHoverTypes=1', '--disable-gpu', '--allow-file-access-from-files',
                          '--virtual-time-budget=9000', f'--window-size={width + 210},900', '--dump-dom', 'file://' + probe],
                         capture_output=True, text=True, timeout=120).stdout
    m = re.search(r'RESULT(\{.*?\})</pre>', out, re.S)
    if not m:
        print(f'[{width}] probe failed: no result'); return True
    res = json.loads(html.unescape(m.group(1)))
    bad = res['page'] > 0 or res['groups'] or res.get('type')
    print(f"[{width}] page overflow: {res['page']}px, groups beyond card edge: {len(res['groups'])}, type mismatches: {len(res.get('type', []))}")
    for g in res['groups'] + res.get('type', []):
        print('  -', g)
    return bad


def main():
    # 휴대폰(390)과 태블릿(768, 820) 폭을 모두 터치 기기로 검사한다.
    os.makedirs(os.path.join(ROOT, 'build'), exist_ok=True)
    bad = False
    for w in (360, 390, 768, 820):
        bad = run(w) or bad
    if bad:
        sys.exit(1)
    print('overflow ok')


if __name__ == '__main__':
    main()
