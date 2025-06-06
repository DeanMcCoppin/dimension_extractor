import fitz  # PyMuPDF
import re

def extract_dimensions_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    dimensions = []
    
    # Patterns specifically for part dimensions
    patterns = [
        # Basic dimensions with decimal point or comma
        r'(?<![A-Za-z])(\d+[.,]\d+|\d+)(?:\s*(?:mm|in|"|°|deg))?',
        # Radius dimensions
        r'R\s*(\d+[.,]\d+|\d+)',
        # Diameter dimensions (multiple symbols)
        r'[Ø⌀]\s*(\d+[.,]\d+|\d+)',
        # Dimensions with text context
        r'(?:THRU|THROUGH|TYP|TYPICAL|REF|REFERENCE)\s*(\d+[.,]\d+|\d+)',
        # Dimensions with ±
        r'[±]\s*(\d+[.,]\d+|\d+)',
        # Dimensions in parentheses
        r'\((\d+[.,]\d+|\d+)\)',
        # Multiple instances (e.g., "2X 1.5")
        r'(\d+)\s*[Xx]\s*(\d+[.,]\d+|\d+)',
        # Angular dimensions
        r'(\d+[.,]?\d*)\s*°',
    ]
    
    compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    # Keywords to identify dimension types
    dimension_keywords = {
        'R': 'Radius',
        'Ø': 'Diameter',
        '⌀': 'Diameter',
        'THRU': 'Through',
        'THROUGH': 'Through',
        'TYP': 'Typical',
        'TYPICAL': 'Typical',
        'REF': 'Reference',
        'REFERENCE': 'Reference',
        '°': 'Angle'
    }
    
    # Keywords to exclude (title block, notes, etc.)
    exclude_keywords = [
        'DATE', 'REV', 'SCALE', 'SHEET', 'DWG', 'PART', 'MATERIAL', 'TOLERANCE',
        'FINISH', 'FORMAT', 'PROJECT', 'APPROVED', 'DRAWN', 'CHECKED', 'TITLE',
        'ECO', 'PRT', 'SERIES', 'NORME', 'ASME', 'Y14.5M', 'NOTES', 'REMARKS',
        'DIMENSIONS', 'TOLERANCES', 'SURFACE', 'FINISH', 'MATERIAL', 'DRAWING',
        'REVISION', 'CHANGE', 'APPROVAL', 'SIGNATURE', 'DRAWN BY', 'CHECKED BY',
        'APPROVED BY', 'DATE', 'SCALE', 'SHEET', 'OF', 'TITLE', 'PART', 'NUMBER',
        'DESCRIPTION', 'MATERIAL', 'FINISH', 'TOLERANCE', 'NOTES', 'REMARKS',
        'DIMENSIONS', 'TOLERANCES', 'SURFACE', 'FINISH', 'MATERIAL', 'DRAWING',
        'REVISION', 'CHANGE', 'APPROVAL', 'SIGNATURE', 'DRAWN BY', 'CHECKED BY',
        'APPROVED BY', 'DATE', 'SCALE', 'SHEET', 'OF', 'TITLE', 'PART', 'NUMBER',
        'DESCRIPTION', 'MATERIAL', 'FINISH', 'TOLERANCE', 'NOTES', 'REMARKS'
    ]
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Get the page dimensions
        page_width = page.rect.width
        page_height = page.rect.height
        
        # Define the drawing area (excluding title block and notes)
        # Typically, the drawing area is in the middle of the page
        # Adjust these values based on your drawing layout
        drawing_area = {
            'x_min': page_width * 0.1,  # 10% from left
            'x_max': page_width * 0.9,  # 10% from right
            'y_min': page_height * 0.1,  # 10% from top
            'y_max': page_height * 0.8   # 20% from bottom
        }
        
        # Get text blocks with their positions
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text:
                            continue
                        
                        # Get position
                        x, y = span["origin"]
                        
                        # Skip if outside drawing area
                        if (x < drawing_area['x_min'] or x > drawing_area['x_max'] or
                            y < drawing_area['y_min'] or y > drawing_area['y_max']):
                            continue
                        
                        # Skip if text contains exclude keywords
                        if any(keyword in text.upper() for keyword in exclude_keywords):
                            continue
                        
                        # Try each pattern
                        for pattern in compiled_patterns:
                            matches = pattern.finditer(text)
                            for match in matches:
                                # Get the full match and its context
                                full_match = match.group(0)
                                value = match.group(1) if len(match.groups()) > 0 else full_match
                                
                                # Determine dimension type
                                dim_type = "Linear"
                                for key, type_name in dimension_keywords.items():
                                    if key in full_match.upper():
                                        dim_type = type_name
                                        break
                                
                                # Clean up the value
                                value = value.strip()
                                if value.replace(',', '').replace('.', '').isdigit():
                                    # Get more context (surrounding text)
                                    context_start = max(0, match.start() - 30)
                                    context_end = min(len(text), match.end() + 30)
                                    context = text[context_start:context_end].strip()
                                    
                                    dimensions.append({
                                        'value': value,
                                        'type': dim_type,
                                        'context': context,
                                        'page': page_num + 1,
                                        'position': (x, y)
                                    })
    
    return dimensions

if __name__ == "__main__":
    pdf_path = r"C:\Users\Maxime Dumas\.cursor\PRT-044-0100-01.pdf"
    dimensions = extract_dimensions_from_pdf(pdf_path)
    
    # Group dimensions by type
    dim_by_type = {}
    for dim in dimensions:
        dim_type = dim['type']
        if dim_type not in dim_by_type:
            dim_by_type[dim_type] = []
        dim_by_type[dim_type].append(dim['value'])
    
    # Print dimensions in a clean format
    print("\nPart Dimensions:")
    print("=" * 40)
    
    # Print each type of dimension
    for dim_type, values in dim_by_type.items():
        print(f"\n{dim_type}:")
        print("-" * 20)
        # Sort values for better readability
        sorted_values = sorted(values, key=lambda x: float(x.replace(',', '.')))
        for value in sorted_values:
            print(f"{value}")
    
    print(f"\nTotal dimensions found: {len(dimensions)}")
    
    # Save to file in the same clean format
    with open('part_dimensions_report.txt', 'w', encoding='utf-8') as f:
        f.write("Part Dimensions Report\n")
        f.write("=" * 40 + "\n\n")
        
        for dim_type, values in dim_by_type.items():
            f.write(f"{dim_type}:\n")
            f.write("-" * 20 + "\n")
            sorted_values = sorted(values, key=lambda x: float(x.replace(',', '.')))
            for value in sorted_values:
                f.write(f"{value}\n")
            f.write("\n")
        
        f.write(f"\nTotal dimensions found: {len(dimensions)}\n") 