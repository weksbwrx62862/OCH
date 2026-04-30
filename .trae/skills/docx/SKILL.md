---
name: docx
description: "Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction. When Claude needs to work with professional documents (.docx files) for: (1) Creating new documents, (2) Modifying or editing content, (3) Working with tracked changes, (4) Adding comments, or any other document tasks"
license: Proprietary. LICENSE.txt has complete terms
---

# DOCX creation, editing, and analysis

## Overview

A user may ask you to create, edit, or analyze the contents of a .docx file. A .docx file is essentially a ZIP archive containing XML files and other resources that you can read or edit. You have different tools and workflows available for different tasks.

## Workflow Decision Tree

### Reading/Analyzing Content
Use "Text extraction" or "Raw XML access" sections below

### Creating New Document
Use "Creating a new Word document" workflow

### Editing Existing Document
- **Your own document + simple changes**
  Use "Basic OOXML editing" workflow

- **Someone else's document**
  Use **"Redlining workflow"** (recommended default)

- **Legal, academic, business, or government docs**
  Use **"Redlining workflow"** (required)

## Reading and analyzing content

### Text extraction
If you just need to read the text contents of a document, you should convert the document to markdown using pandoc:

```bash
pandoc --track-changes=all path-to-file.docx -o output.md
```

### Raw XML access
You need raw XML access for: comments, complex formatting, document structure, embedded media, and metadata.

#### Unpacking a file
`python ooxml/scripts/unpack.py <office_file> <output_directory>`

## Creating a new Word document

When creating a new Word document from scratch, use **docx-js**.

### Workflow
1. Read docx-js.md completely
2. Create a JavaScript/TypeScript file using Document, Paragraph, TextRun components
3. Export as .docx using Packer.toBuffer()

## Editing an existing Word document

When editing an existing Word document, use the **Document library** (a Python library for OOXML manipulation).

### Workflow
1. Read ooxml.md completely
2. Unpack the document
3. Create and run a Python script using the Document library
4. Pack the final document

## Redlining workflow for document review

This workflow allows you to plan comprehensive tracked changes using markdown before implementing them in OOXML.

### Tracked changes workflow

1. **Get markdown representation**: Convert document to markdown with tracked changes preserved
2. **Identify and group changes**: Review the document and identify ALL changes needed
3. **Read documentation and unpack**
4. **Implement changes in batches**: Group changes logically
5. **Pack the document**
6. **Final verification**

## Dependencies

Required dependencies:
- **pandoc**: for text extraction
- **docx**: for creating new documents
- **LibreOffice**: for PDF conversion
- **Poppler**: for pdftoppm to convert PDF to images
- **defusedxml**: for secure XML parsing
