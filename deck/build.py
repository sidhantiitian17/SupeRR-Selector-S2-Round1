"""Assemble build/deck.html (all slides, print-ready) and build/viewer.html (keyboard/click slideshow for the web)."""
import pathlib, sys
from lib import css, ROOT, esc, logo
import deck


def build(only=None):
    secs = []
    for i, fn in enumerate(deck.SLIDES, 1):
        if only and i not in only:
            continue
        secs.append(fn(i))
    style = css()
    page = (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Under Pressure Rating · SupeRR Selector S2</title><link rel="icon" type="image/png" href="{logo()}"/>'
            f'<style>{style}@page{{size:1600px 900px;margin:0}}</style></head><body>{"".join(secs)}</body></html>')
    out = ROOT / "build" / "deck.html"
    out.write_text(page)
    print("slides:", len(secs), "->", out, f"{out.stat().st_size / 1e6:.1f} MB")
    return out


VIEWER_CSS = """
html,body{height:100%;overflow:hidden;background:#0b0610}
#stage{position:fixed;inset:0 0 56px 0;display:grid;place-items:center}
#stage .slide{display:none;position:absolute;left:50%;top:50%;transform-origin:center center;box-shadow:0 20px 60px rgba(0,0,0,.5);border-radius:6px}
#stage .slide.on{display:block}
#bar{position:fixed;left:0;right:0;bottom:0;height:56px;display:flex;align-items:center;justify-content:center;gap:10px;background:#120c1a;border-top:1px solid #2c2438;font:600 14px Inter,Arial;color:#f5f3f8}
#bar button,#bar a{background:#221b30;color:#f5f3f8;border:1px solid #3a3048;border-radius:10px;height:36px;min-width:40px;padding:0 12px;font:700 13px Inter,Arial;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;gap:6px}
#bar button:hover,#bar a:hover{border-color:#f5008f}
#bar .pri{background:#c4007a;border-color:#c4007a}
#count{min-width:90px;text-align:center;color:#a39bb3}
#ttl{color:#a39bb3;max-width:36vw;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
@media (max-width:700px){#ttl,#fs,#bar a{display:none}#bar{gap:6px}}
"""
VIEWER_JS = """
(function(){const S=[...document.querySelectorAll('#stage .slide')];let i=0;
function fit(){const st=document.getElementById('stage');const k=Math.min(st.clientWidth/1600,st.clientHeight/900)*0.98;S.forEach(s=>s.style.transform=`translate(-50%,-50%) scale(${k})`);}
function go(n){i=Math.max(0,Math.min(S.length-1,n));S.forEach((s,j)=>s.classList.toggle('on',j===i));document.getElementById('count').textContent=`${i+1} / ${S.length}`;document.getElementById('ttl').textContent=S[i].dataset.title;try{history.replaceState(null,'','#'+(i+1))}catch(e){}try{parent.postMessage({deckSlide:i+1},'*')}catch(e){}}
document.getElementById('prev').onclick=()=>go(i-1);document.getElementById('next').onclick=()=>go(i+1);
document.getElementById('fs').onclick=()=>{const d=document.documentElement;document.fullscreenElement?document.exitFullscreen():d.requestFullscreen&&d.requestFullscreen()};
addEventListener('keydown',e=>{if(['ArrowRight','PageDown',' '].includes(e.key)){go(i+1);e.preventDefault()}if(['ArrowLeft','PageUp'].includes(e.key)){go(i-1);e.preventDefault()}if(e.key==='Home')go(0);if(e.key==='End')go(S.length-1)});
let x0=null;addEventListener('touchstart',e=>x0=e.touches[0].clientX,{passive:true});addEventListener('touchend',e=>{if(x0==null)return;const dx=e.changedTouches[0].clientX-x0;if(Math.abs(dx)>40)go(i+(dx<0?1:-1));x0=null});
addEventListener('message',e=>{if(e.data&&e.data.goSlide)go(e.data.goSlide-1)});
addEventListener('hashchange',()=>go((parseInt(location.hash.slice(1))||1)-1));
addEventListener('resize',fit);fit();go((parseInt(location.hash.slice(1))||1)-1);})();
"""


def build_viewer(deck_html, out_dir, pdf_name, pptx_name):
    """Slideshow page for the web (embedded in the dashboard): one slide at a time, scaled to fit."""
    import re
    head, body = deck_html.split("<body>", 1)
    body = body.replace("</body></html>", "")
    bar = (f'<div id="bar"><button id="prev" aria-label="Previous slide">&#8592;</button><span id="count"></span><button id="next" aria-label="Next slide">&#8594;</button>'
           f'<span id="ttl"></span><button id="fs">Full screen</button><a href="{pdf_name}" download>PDF</a><a class="pri" href="{pptx_name}" download>PPTX</a></div>')
    page = head.replace("</style>", VIEWER_CSS + "</style>") + f'<body><div id="stage">{body}</div>{bar}<script>{VIEWER_JS}</script></body></html>'
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(page)
    print("viewer ->", out_dir / "index.html")


if __name__ == "__main__":
    if sys.argv[1:2] == ["viewer"]:
        out = pathlib.Path(sys.argv[2])
        build_viewer((ROOT / "build" / "deck.html").read_text(), out, sys.argv[3], sys.argv[4])
    else:
        only = set(map(int, sys.argv[1:])) if len(sys.argv) > 1 else None
        build(only)
