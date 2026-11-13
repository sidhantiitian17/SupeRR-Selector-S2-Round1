"""Render build/deck.html: one PNG per slide (2x) and a vector PDF.  python3 render.py [png|pdf|all] [slide numbers...]"""
import asyncio, sys, pathlib
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).parent
B = ROOT / "build"


async def main(mode, only):
    async with async_playwright() as p:
        import os
        exe = os.environ.get("CHROME") or next((c for c in ("/usr/bin/google-chrome", "/usr/bin/chromium") if os.path.exists(c)), None)
        br = await p.chromium.launch(**({"executable_path": exe} if exe else {}), args=["--no-sandbox"])
        pg = await br.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=2)
        await pg.goto((B / "deck.html").as_uri())
        await pg.evaluate("document.fonts.ready")
        await pg.wait_for_timeout(400)
        if mode in ("png", "all"):
            (B / "png").mkdir(exist_ok=True)
            secs = await pg.query_selector_all("section.slide")
            for el in secs:
                n = int(await el.get_attribute("data-n"))
                if only and n not in only:
                    continue
                await el.screenshot(path=str(B / "png" / f"slide-{n:02d}.png"))
            # overflow check: any .abs element whose content overflows its box, or that leaves the slide
            issues = await pg.evaluate("""() => {
              const out=[];
              document.querySelectorAll('section.slide').forEach(s=>{
                const n=s.dataset.n, sb=s.getBoundingClientRect();
                s.querySelectorAll('.node,.card,.pill').forEach(e=>{
                  if(e.scrollHeight>e.clientHeight+2||e.scrollWidth>e.clientWidth+2) out.push(`slide ${n}: overflow in ${e.className} "${e.innerText.slice(0,50).replace(/\\n/g,' ')}" (${e.scrollWidth}x${e.scrollHeight} > ${e.clientWidth}x${e.clientHeight})`);
                  const r=e.getBoundingClientRect(); if(r.right>sb.right+1||r.bottom>sb.bottom+1) out.push(`slide ${n}: off-slide ${e.className} "${e.innerText.slice(0,40)}"`);
                });
              }); return out; }""")
            print("\n".join(issues) if issues else "no overflow detected")
        if mode in ("pdf", "all"):
            await pg.pdf(path=str(B / "deck.pdf"), width="1600px", height="900px", print_background=True, prefer_css_page_size=True)
            print("pdf ok")
        await br.close()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "png"
    only = set(map(int, sys.argv[2:]))
    asyncio.run(main(mode, only))
