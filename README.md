# PDF Part Dimensions Extractor

A Python tool that extracts part dimensions from technical drawings in PDF files. It identifies and categorizes different types of dimensions (linear, radius, angle) from the drawing area while filtering out non-part information.

## Features

- Extracts dimensions from PDF technical drawings
- Categorizes dimensions by type (Linear, Radius, Angle)
- Filters out non-part information (title blocks, notes, etc.)
- Focuses on the actual drawing area
- Provides clean, organized output
- Saves results to a text file

## Requirements

- Python 3.x
- PyMuPDF (fitz)
- A PDF file containing technical drawings

## Installation

1. Clone this repository:
```bash
git clone [your-repository-url]
```

2. Install the required package:
```bash
pip install PyMuPDF
```

## Usage

1. Place your PDF file in the same directory as the script
2. Update the `pdf_path` in the script to point to your PDF file
3. Run the script:
```bash
python pdf_annotations.py
```

The script will:
- Extract all part dimensions from the PDF
- Display them in the terminal, grouped by type
- Save a detailed report to `part_dimensions_report.txt`

## Output Format

Dimensions are grouped by type and sorted numerically:

```
Part Dimensions:
========================================

Linear:
--------------------
1,500
3,00
4,50
...

Radius:
--------------------
2,250
2,500
...

Angle:
--------------------
22,5
60
100
...
```

## License

[Your chosen license]

## Author

[Your name] 