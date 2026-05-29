# PptxGenJS Tutorial

## Setup & Basic Structure

```javascript
const PptxGenJS = require("pptxgenjs");
const pres = new PptxGenJS();
pres.layout = "LAYOUT_WIDE";

const slide = pres.addSlide();
slide.addText("Hello", { x: 1, y: 1, w: 8, h: 1, fontSize: 48 });

await pres.writeFile({ fileName: "output.pptx" });
```

## Common Patterns

- **Title slide**: dark background, large title (60pt+), short subtitle
- **Content slide**: 2-column grid, bullet list left, image right
- **Chart**: `slide.addChart(pres.ChartType.bar, data, opts)`
- **Image**: `slide.addImage({ path: "img.png", x, y, w, h })`
