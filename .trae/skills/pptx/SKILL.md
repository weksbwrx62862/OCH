---
name: pptx
description: "Presentation creation, editing, and analysis. When Claude needs to work with presentations (.pptx files) for: (1) Creating new presentations, (2) Modifying or editing content, (3) Working with layouts, (4) Adding comments or speaker notes, or any other presentation tasks"
license: Proprietary. LICENSE.txt has complete terms
---

# PPTX creation, editing, and analysis

## Overview

A user may ask you to create, edit, or analyze the contents of a .pptx file.

## Reading and analyzing content

### Text extraction
```bash
python -m markitdown path-to-file.pptx
```

### Raw XML access
`python ooxml/scripts/unpack.py <office_file> <output_dir>`

## Creating a new PowerPoint presentation

When creating a new PowerPoint presentation from scratch, use the **html2pptx** workflow to convert HTML slides to PowerPoint with accurate positioning.

### Design Principles

**CRITICAL**: Before creating any presentation, analyze the content and choose appropriate design elements:
1. **Consider the subject matter**: What is this presentation about?
2. **Check for branding**: If the user mentions a company/organization, consider their brand colors and identity
3. **Match palette to content**: Select colors that reflect the subject

### Workflow
1. Read html2pptx.md completely
2. Create an HTML file for each slide with proper dimensions
3. Create and run a JavaScript file using html2pptx.js library
4. Visual validation

## Editing an existing PowerPoint presentation

1. Read ooxml.md completely
2. Unpack the presentation
3. Edit the XML files
4. Validate after each edit
5. Pack the final presentation

## Dependencies

- **markitdown**: for text extraction from presentations
- **pptxgenjs**: for creating presentations via html2pptx
- **playwright**: for HTML rendering in html2pptx
- **sharp**: for SVG rasterization and image processing
- **LibreOffice**: for PDF conversion
- **Poppler**: for pdftoppm
