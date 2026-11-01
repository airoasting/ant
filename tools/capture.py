"""디자인 평가용 화면 캡처.

사용법: python3 -I tools/capture.py <라운드 이름>     예) python3 -I tools/capture.py r1
- docs/index.html을 복사해 build/capture.html을 만든다. 복사본은 '움직임 줄이기' 모드로 열려 등장 효과가 멈춘 흐린 화면이 없다.
- 헤드리스 Chrome은 스크롤한 위치를 제대로 그리지 못하므로, ?sel= 로 지정한 장만 남기고 나머지를 숨긴 채 찍는다.
  이때 상단 바는 스크롤한 상태(흰 띠)로 두고, 화면 아래 띠의 캐릭터는 &buddy=1 일 때만 그린다.
- 휴대폰 화면은 헤드리스 창이 500px보다 좁아지지 않아서, 390px 폭 틀(iframe)에 넣어 찍은 뒤 가운데를 잘라낸다.
- 결과는 build/review/<라운드>/ 에 PNG로 저장한다. 데스크톱 1440x900, 휴대폰 390x844.
"""
import os, sys, shutil, subprocess, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
INJECT = r"""<script>
(function(){var st=document.createElement('style');st.textContent='*,*::before,*::after{transition-duration:0s!important;transition-delay:0s!important}';document.documentElement.appendChild(st);})();
window.matchMedia=(function(m){return function(q){if(/reduce/.test(q))return {matches:true,media:q,addListener(){},removeListener(){},addEventListener(){},removeEventListener(){}};return m.call(window,q)}})(window.matchMedia);
document.addEventListener('DOMContentLoaded',function(){var p=new URLSearchParams(location.search),sel=p.get('sel'),toc=p.get('toc');
 if(sel){var el=document.querySelector(sel); if(el){var sec=el.closest('section,footer')||el, main=document.getElementById('main');
  [...main.children].forEach(function(x){ if(!x.contains(sec)) x.style.display='none'; });
  var part=sec.closest('.part'); if(part) [...part.children].forEach(function(x){ if(x!==sec) x.style.display='none'; });
  if(sec.tagName!=='FOOTER'){ var f=document.querySelector('footer'); if(f) f.style.display='none'; } else { main.style.display='none'; }
  if(p.get('only')){ var keep=el.closest('.panel')||el; var n=keep; while(n&&n!==sec){ [...n.parentNode.children].forEach(function(x){ if(x!==n) x.style.display='none'; }); n=n.parentNode; } }
  sec.style.paddingTop=p.get('pad')||'96px'; if(part) part.style.paddingBottom='24px';
  var tb=document.querySelector('.topbar'); if(tb){ tb.classList.add('docked'); var cl=tb.classList, tg=DOMTokenList.prototype.toggle; cl.toggle=function(k,f){ return k==='docked'?true:tg.call(cl,k,f); }; } var st=document.createElement('style'); st.textContent='.topbar .cite-tog,.topbar .nav .now{color:#4f5b6e!important}.topbar .sitebrand .pg{color:#2d3748!important}.topbar .sitebrand .ar{color:#5B62D8!important}.topbar{top:0!important;background:rgba(255,255,255,.94)!important;opacity:1!important;transform:none!important}'; document.head.appendChild(st);
  if(!p.get('buddy')){ var c=document.getElementById('field'); if(c) c.style.display='none'; }
  var n=document.getElementById('navnow'); if(n&&sec.dataset&&sec.dataset.ch) setTimeout(function(){n.textContent=(sec.dataset.no?'사실 '+sec.dataset.no+' / 12 · ':'')+sec.dataset.ch; n.dataset.short=sec.dataset.no?sec.dataset.no+' / 12':(sec.dataset.sts||sec.dataset.ch||sec.dataset.st||'')},60);}}
 if(toc) setTimeout(function(){var b=document.getElementById('menuBtn'); if(b) b.click();},200);
 var ck=p.get('click'); if(ck) setTimeout(function(){var b=document.querySelector(ck); if(b) b.click();},400);});
</script>"""

D, M, T = (1440, 900), (390, 844), (768, 1024)
SHOTS = [
    ('d01_cover', '', D), ('d01b_key', '?sel=%23key&pad=72px', D), ('d02_kpi', '?sel=.kband&pad=96px', D), ('d03_part1', '?sel=%23act1&pad=96px', D), ('m30_method', '?sel=%23method&pad=72px', M), ('m31_touch_key', '?sel=%23key&pad=64px', M), ('m32_touch_fact01', '?sel=%23c2%20.prose&only=1&pad=72px', M), ('m33_touch_drawer', '?sel=%23c2&click=%23c2%20.prose%20.cite', M), ('d36_part2', '?sel=%23c3&pad=420px', D),
    ('d04_fact01', '?sel=%23c2', D), ('d05_fact03', '?sel=%23c1', D), ('d06_fact04', '?sel=%23c3', D),
    ('d07_fact05', '?sel=%23c4', D), ('d08_tagline', '?sel=.tagline&pad=0', D), ('d09_fact07', '?sel=%23c7', D),
    ('d10_fact08', '?sel=%23c8', D), ('d11_fact10', '?sel=%23c10', D), ('d12_fact12', '?sel=%23c12', D),
    ('d13_press', '?sel=%23c11', D), ('d14_method', '?sel=%23method', D), ('d15_footer', '?sel=footer&pad=0&buddy=1', D),
    ('d16_toc', '?toc=1', D),
    ('d19_fact02', '?sel=%23c5', D), ('d20_fact06', '?sel=%23c6', D), ('d21_fact09', '?sel=%23c9', D), ('d22_fact06_net', '?sel=%23net&only=1&pad=96px', D), ('d23_stair', '?sel=%23stair&only=1&pad=96px', D), ('d24_fbars', '?sel=%23fbars&only=1&pad=96px', D), ('d26_pyr', '?sel=%23pyr&only=1&pad=200px', D), ('d27_opq', '?sel=%23opq&only=1&pad=96px', D), 
    ('d28_chfoot', '?sel=%23c3%20.chfoot&only=1&pad=96px', D), ('d29_factcheck', '?sel=.vs&only=1&pad=96px', D), ('d30_fbzoom', '?sel=%23fbars&only=1&pad=96px&click=%23zoomTog', D), ('d33_fbpledge', '?sel=%23fbars&only=1&pad=96px&click=%23pledgeTog', D), ('m15_fbzoom', '?sel=%23fbars&only=1&pad=72px&click=%23zoomTog', M), ('m16_fact03', '?sel=%23c1', M), ('m17_kpis', '?sel=%23c1%20.kpis&only=1&pad=72px', M), ('m18_fact06', '?sel=%23c6', M), ('m19_fact10', '?sel=%23c10', M), ('m27_kband', '?sel=.kband', M), ('d31_squares', '?sel=.panel%3Ahas(%23squares)&only=1&pad=96px', D), ('m22_squares', '?sel=.panel%3Ahas(%23squares)&only=1&pad=72px', M), ('m23_opq', '?sel=.panel%3Ahas(%23opq)&only=1&pad=72px', M), ('d32_timeline', '?sel=.panel%3Ahas(.tl)&only=1&pad=96px', D), ('d34_fact11', '?sel=%23c13', D), ('d35_korea', '?sel=%23cval%20.wrap%3Ahas(%3E.korea)&only=1&pad=96px', D), ('m29_korea', '?sel=%23cval%20.wrap%3Ahas(%3E.korea)&only=1&pad=72px', M), ('m24_steps', '?sel=.panel%3Ahas(%23steps)&only=1&pad=72px', M), ('m20_filings', '?sel=.filings&only=1&pad=72px', M), ('m21_hero01', '?sel=%23c2', M), ('t01_fact03', '?sel=%23c1', T), ('t02_fact09', '?sel=%23c9', T), ('d17_valuation', '?sel=%23cval', D), ('d18_valuation_tab', '?sel=.kinv&only=1&pad=96px', D),
    ('m01_cover', '', M), ('m01b_key', '?sel=%23key&pad=64px', M), ('m01c_key2', '?sel=.km-g&pad=64px', M), ('m02_fact01', '?sel=%23c2', M), ('m03_fact07', '?sel=%23c7', M), ('m04_toc', '?toc=1', M),
    ('m05_chart01', '?sel=%23qchart&only=1&pad=72px', M), ('m06_chart04', '?sel=%23wf&only=1&pad=72px', M), ('m07_chart07', '?sel=%23vote&only=1&pad=72px', M), ('m08_chart08', '?sel=%23board&only=1&pad=72px', M), ('m09_valuation', '?sel=%23cval&only=1&pad=72px', M), ('m10_valuation_tab', '?sel=.kinv&only=1&pad=72px', M), ('m11_stair', '?sel=%23stair&only=1&pad=72px', M), ('m12_net', '?sel=%23net&only=1&pad=72px', M), ('m13_cust', '?sel=%23cust&only=1&pad=72px', M), ('m14_cratio', '?sel=%23cratio&only=1&pad=72px', M),
]

# 폭 1023px 이하(휴대폰, 태블릿) 캡처는 터치 기기로 흉내 낸다. 마우스 환경으로 찍으면
# (pointer:coarse)/(hover:none) 규칙이 빠져 실제 휴대폰과 다른 화면을 검토하게 된다.
TOUCH = '--blink-settings=primaryPointerType=2,availablePointerTypes=2,primaryHoverType=1,availableHoverTypes=1'

def shoot(url, w, h, path):
    args = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
            f'--window-size={w},{h}', '--virtual-time-budget=7000', f'--screenshot={path}', url]
    if w < 1024:
        args.insert(1, TOUCH)
    subprocess.run(args, capture_output=True, timeout=120)

def main():
    rnd = sys.argv[1] if len(sys.argv) > 1 else 'r1'
    only = sys.argv[2:]
    src = open(os.path.join(ROOT, 'docs', 'index.html'), encoding='utf-8').read()
    i = src.index('<head>') + len('<head>')
    b = os.path.join(ROOT, 'build'); os.makedirs(b, exist_ok=True)
    fs, fd = os.path.join(ROOT, 'docs', 'fonts'), os.path.join(b, 'fonts')
    if os.path.isdir(fs): shutil.copytree(fs, fd, dirs_exist_ok=True)  # 캡처 복사본도 같은 폰트를 쓴다
    cap = os.path.join(b, 'capture.html'); open(cap, 'w', encoding='utf-8').write(src[:i] + INJECT + src[i:])
    out = os.path.join(b, 'review', rnd); os.makedirs(out, exist_ok=True)
    for name, q, (w, h) in SHOTS:
        if only and name not in only: continue
        path = os.path.join(out, name + '.png')
        if w < 500:
            frame = os.path.join(b, 'mframe.html')
            open(frame, 'w', encoding='utf-8').write(
                f'<!doctype html><html><body style="margin:0;background:#000;display:flex;justify-content:center">'
                f'<iframe src="capture.html{q}" style="width:{w}px;height:{h}px;border:0;display:block"></iframe></body></html>')
            shoot('file://' + urllib.parse.quote(frame), 600, h, path)
            subprocess.run(['sips', '-c', str(h), str(w), path], capture_output=True)
        else:
            shoot('file://' + urllib.parse.quote(cap) + q, w, h, path)
        print(name, 'ok' if os.path.exists(path) else 'FAILED')

if __name__ == '__main__':
    main()
