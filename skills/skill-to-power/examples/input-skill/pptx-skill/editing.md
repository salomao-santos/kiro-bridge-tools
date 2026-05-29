# Editing Presentations

## Template-Based Workflow

When using an existing presentation as a template:

1. **Analyze** the template structure with `scripts/thumbnail.py template.pptx`
2. **Unpack** the .pptx archive: `python scripts/office/unpack.py template.pptx unpacked/`
3. **Manipulate** slides — duplicate, reorder, delete by editing `unpacked/ppt/presentation.xml`
4. **Edit content** in each `unpacked/ppt/slides/slideN.xml`
5. **Clean** unused media + relationships
6. **Pack** back: `python scripts/office/pack.py unpacked/ output.pptx`

## Common Edits

- **Text**: replace `<a:t>` element content
- **Image swap**: drop new file in `unpacked/ppt/media/`, update `slideN.xml.rels`
- **Speaker notes**: edit `unpacked/ppt/notesSlides/notesSlideN.xml`
- **Slide reorder**: rearrange `<p:sldId>` entries in `presentation.xml`
