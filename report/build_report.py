"""Build the end-to-end guide:  python3 report/build_report.py  ->  report/build/Under_Pressure_Rating_Complete_Guide.pdf"""
import asyncio, os, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from rlib import css, ROOT
import ch_a, ch_b, ch_c

B = ROOT / "build"
B.mkdir(exist_ok=True)
PDF = B / "Under_Pressure_Rating_Complete_Guide.pdf"


def html():
    parts = [ch_a.cover(), ch_a.contents(), ch_a.ch1(), ch_a.ch2(), ch_a.ch3(), ch_a.ch4(), ch_a.ch5(), ch_a.ch6(), ch_a.ch7(),
             ch_b.ch8(), ch_b.ch9(), ch_b.ch10(), ch_b.ch11(), ch_b.ch12(), ch_b.ch13(), ch_b.ch14(), ch_b.ch15(),
             ch_c.ch16(), ch_c.ch17(), ch_c.ch18(), ch_c.ch19(), ch_c.ch20(), ch_c.ch21(), ch_c.ch22(), ch_c.appendix()]
    return f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Under Pressure Rating: the complete guide</title><style>{css()}</style></head><body>{"".join(parts)}</body></html>'


CHAPTER_KEYS = {"1": "The question, in plain words", "2": "Opening the data for the first", "3": "Cleaning: rebuilding every ball", "4": "The plan before any modelling",
                "5": "What is pressure? Three", "6": "Leverage and the Pressure", "7": "Checking the definition", "8": "Valuing every ball fairly", "9": "Small samples: shrinkage",
                "10": "Usual level, consistency and", "11": "The refinement journey: 12", "12": "A second, independent", "13": "The held-out tournament", "14": "The final recipe, step by step",
                "15": "How sure are we?", "16": "Results: the top 10 batters", "17": "From a ranking to a plan for", "18": "The player pick we are", "19": "War-room moments",
                "20": "Why this approach, and what", "21": "Limitations, and how", "22": "Architecture and reproducing", "A–D": "Glossary"}


def page_map(pdf):
    from pypdf import PdfReader
    pages = [p.extract_text() or "" for p in PdfReader(str(pdf)).pages]
    out = {}
    for k, key in CHAPTER_KEYS.items():
        for i, t in enumerate(pages):
            if i > 1 and key in " ".join(t.split()):
                out[k] = i + 1
                break
    return out


async def render():
    from playwright.async_api import async_playwright
    from pypdf import PdfReader, PdfWriter
    await render_once()
    ch_a.PAGES.update(page_map(PDF))          # second pass: fill in the contents page numbers
    await render_once()
    print("contents pages:", ch_a.PAGES)


async def render_once():
    from playwright.async_api import async_playwright
    from pypdf import PdfReader, PdfWriter
    (B / "guide.html").write_text(html())
    async with async_playwright() as p:
        exe = os.environ.get("CHROME") or next((c for c in ("/usr/bin/google-chrome", "/usr/bin/chromium") if os.path.exists(c)), None)
        br = await p.chromium.launch(**({"executable_path": exe} if exe else {}), args=["--no-sandbox"])
        pg = await br.new_page()
        await pg.goto((B / "guide.html").as_uri())
        await pg.evaluate("document.fonts.ready")
        await pg.wait_for_timeout(500)
        bad = await pg.evaluate("""() => [...document.querySelectorAll('foreignObject > div')].filter(d => d.scrollHeight > d.clientHeight + 1 || d.scrollWidth > d.clientWidth + 1)
                                     .map(d => d.innerText.replace(/\\n/g, ' ').slice(0, 60))""")
        print("diagram text overflow:", bad if bad else "none")
        foot = ('<div style="width:100%;font-size:7.5pt;color:#8a7f9c;font-family:Inter,sans-serif;padding:0 15mm;display:flex;justify-content:space-between">'
                '<span>Under Pressure Rating · the complete guide · Prashast Sidhant, NIT Raipur</span><span class="pageNumber"></span></div>')
        await pg.pdf(path=str(B / "_body.pdf"), format="A4", print_background=True, prefer_css_page_size=True, display_header_footer=True,
                     header_template="<div></div>", footer_template=foot)
        await pg.pdf(path=str(B / "_cover.pdf"), format="A4", print_background=True, prefer_css_page_size=True, page_ranges="1")
        await br.close()
    w = PdfWriter()
    w.add_page(PdfReader(str(B / "_cover.pdf")).pages[0])
    for p in PdfReader(str(B / "_body.pdf")).pages[1:]:
        w.add_page(p)
    w.add_metadata({"/Title": "Under Pressure Rating: the complete guide", "/Author": "Prashast Sidhant, National Institute of Technology Raipur"})
    with open(PDF, "wb") as f:
        w.write(f)
    print("wrote", PDF)


if __name__ == "__main__":
    asyncio.run(render())
