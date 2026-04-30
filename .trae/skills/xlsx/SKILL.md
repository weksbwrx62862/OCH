---
name: xlsx
description: "Comprehensive spreadsheet creation, editing, and analysis with support for formulas, formatting, data analysis, and visualization. When Claude needs to work with spreadsheets (.xlsx, .xlsm, .csv, .tsv, etc) for: (1) Creating new spreadsheets with formulas and formatting, (2) Reading or analyzing data, (3) Modify existing spreadsheets while preserving formulas, (4) Data analysis and visualization in spreadsheets, or (5) Recalculating formulas"
license: Proprietary. LICENSE.txt has complete terms
---

# Requirements for Outputs

## All Excel files

### Zero Formula Errors
- Every Excel model MUST be delivered with ZERO formula errors (#REF!, #DIV/0!, #VALUE!, #N/A, #NAME?)

### preserve Existing Templates (when updating templates)
- Study and EXACTLY match existing format, style, and conventions when modifying files

## Financial models

### Color Coding Standards
- **Blue text**: Hardcoded inputs
- **Black text**: ALL formulas and calculations
- **Green text**: Links pulling from other worksheets within same workbook
- **Red text**: External links to other files

### Number Formatting Standards
- **Years**: Format as text strings
- **Currency**: Use $#,##0 format
- **Zeros**: Use number formatting to make all zeros "-"
- **Percentages**: Default to 0.0% format
- **Negative numbers**: Use parentheses

# XLSX creation, editing, and analysis

## Overview

A user may ask you to create, edit, or analyze the contents of an .xlsx file.

## Reading and analyzing data

### Data analysis with pandas
```python
import pandas as pd
df = pd.read_excel('file.xlsx')
df.to_excel('output.xlsx', index=False)
```

## CRITICAL: Use Formulas, Not Hardcoded Values

**Always use Excel formulas instead of calculating values in Python and hardcoding them.**

### Creating new Excel files

```python
from openpyxl import Workbook
wb = Workbook()
sheet = wb.active
sheet['B2'] = '=SUM(A1:A10)'
wb.save('output.xlsx')
```

### Editing existing Excel files

```python
from openpyxl import load_workbook
wb = load_workbook('existing.xlsx')
sheet = wb.active
sheet['A1'] = 'New Value'
wb.save('modified.xlsx')
```

## Recalculating formulas

Excel files created or modified by openpyxl contain formulas as strings but not calculated values. Use the provided `recalc.py` script:

```bash
python recalc.py output.xlsx
```

The script:
- Recalculates all formulas in all sheets
- Scans ALL cells for Excel errors
- Returns JSON with detailed error locations and counts
