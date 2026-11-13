// Packages the rendered slides into a .pptx: one full-bleed 3200x1800 image per slide, speaker notes, clickable link areas.
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const man = JSON.parse(fs.readFileSync("build/manifest.json"));
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";               // 10 x 5.625 in
pres.title = "Under Pressure Rating · SupeRR Selector Season 2";
pres.subject = "Most reliable players under pressure and an IPL 2027 plan for Rajasthan Royals";
const k = 10 / 1600;
for (const s of man) {
  const slide = pres.addSlide();
  slide.background = { color: "120C1A" };
  slide.addImage({ path: s.img, x: 0, y: 0, w: 10, h: 5.625, altText: s.title });
  for (const [x, y, w, h, url] of s.links) {
    slide.addShape(pres.shapes.RECTANGLE, { x: x * k, y: y * k, w: w * k, h: h * k, fill: { color: "FFFFFF", transparency: 100 }, line: { type: "none" }, hyperlink: { url, tooltip: url } });
  }
  slide.addNotes(`${s.title}\n\n${s.notes}`);
}
pres.writeFile({ fileName: process.argv[2] || "build/Under_Pressure_Rating_SupeRR_S2.pptx" }).then(f => console.log("wrote", f));
