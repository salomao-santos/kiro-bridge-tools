---
name: pptx
description: "Use this skill any time a .pptx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations; reading, parsing, or extracting text from any .pptx file; editing, modifying, or updating existing presentations; combining or splitting slide files; working with templates, layouts, speaker notes, or comments. Trigger whenever the user mentions \"deck,\" \"slides,\" \"presentation,\" or references a .pptx filename."
license: Proprietary. LICENSE.txt has complete terms
---

# PPTX Skill

## Quick Reference

| Task | Guide |
|------|-------|
| Read/analyze content | `python -m markitdown presentation.pptx` |
| Edit or create from template | Read [editing.md](editing.md) |
| Create from scratch | Read [pptxgenjs.md](pptxgenjs.md) |

## Reading Content

```bash
python -m markitdown presentation.pptx       # text extraction
python scripts/thumbnail.py presentation.pptx # visual overview
python scripts/office/unpack.py presentation.pptx unpacked/ # raw XML
```

## Editing Workflow

Read [editing.md](editing.md) for full details.

1. Analyze template with `thumbnail.py`
2. Unpack → manipulate slides → edit content → clean → pack

## Creating from Scratch

Read [pptxgenjs.md](pptxgenjs.md) for full details. Use when no template or reference presentation is available.

## Design Ideas

Don't create boring slides. Plain bullets on a white background won't impress anyone.

### Before Starting

- Pick a bold, content-informed color palette
- Dominance over equality: one color 60-70% visual weight
- Dark/light contrast: dark titles + conclusions, light content
- Commit to a visual motif and repeat it across every slide

### Color Palettes

| Theme | Primary | Secondary | Accent |
|-------|---------|-----------|--------|
| Midnight Executive | `1E2761` | `CADCFC` | `FFFFFF` |
| Forest & Moss | `2C5F2D` | `97BC62` | `F5F5F5` |
| Coral Energy | `F96167` | `F9E795` | `2F3C7E` |
| Charcoal Minimal | `36454F` | `F2F2F2` | `212121` |
| Cherry Bold | `990011` | `FCF6F5` | `2F3C7E` |
