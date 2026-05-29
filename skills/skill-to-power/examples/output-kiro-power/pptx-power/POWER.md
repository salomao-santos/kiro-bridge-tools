---
name: "pptx"
displayName: "PPTX"
description: "Create, read, edit, parse, or extract content from .pptx slide decks. Covers templates, layouts, speaker notes, and from-scratch deck generation."
keywords: ["pptx", "powerpoint", "slides", "deck", "presentation", "slide", "template", "pptxgenjs"]
author: "Salomão Santos"
---

# PPTX

## Overview

Comprehensive Power for any task involving `.pptx` files: reading, editing, creating from scratch, working with templates, layouts, speaker notes, and comments.

## Steering Files

- [steering/quick-reference.md](steering/quick-reference.md) — task → command lookup table
- [steering/reading-content.md](steering/reading-content.md) — text extraction, thumbnails, raw XML
- [steering/editing-workflow.md](steering/editing-workflow.md) — template-based editing (unpack → manipulate → pack)
- [steering/creating-from-scratch.md](steering/creating-from-scratch.md) — pptxgenjs tutorial for blank-slate decks
- [steering/design-ideas.md](steering/design-ideas.md) — color palettes, layout principles, visual motifs

## Scripts

| Script | Description |
|---|---|
| `scripts/thumbnail.py` | Render slide thumbnails as PNG grid |
| `scripts/office/unpack.py` | Extract `.pptx` archive to directory |
| `scripts/office/pack.py` | Repack directory into `.pptx` archive |

Licensed under Anthropic terms. See source skill `LICENSE.txt`.
