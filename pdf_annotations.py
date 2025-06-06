import fitz  # PyMuPDF
import re

def extract_dimensions_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    dimensions = []
    
    # Patterns for all common dimension types
    patterns = [
        # Diameter: Ø.201, ⌀.201, 8X Ø.201, 8X⌀.201, etc.
        r'(\d+X)?\s*[Ø⌀]\s*([0-9]+[.,]?[0-9]*|[0-9]+/[0-9]+)',
        # Radius: R2.250, R17/32
        r'R\s*([0-9]+[.,]?[0-9]*|[0-9]+/[0-9]+)',
        # Angles: 60°, 100°
        r'([0-9]+[.,]?[0-9]*)\s*°',
        # Linear: 4.50, 1,500, 3/16, .750, 10,06
        r'(?<![A-Za-z0-9])([0-9]+[.,][0-9]+|[0-9]+/[0-9]+|[0-9]+)(?![A-Za-z0-9])',
        # Thread callouts: 10-32 UNF, etc.
        r'([0-9]+-[0-9]+)\s*[A-Za-z]+',
    ]
    
    compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text:
                            continue
                        for pattern in compiled_patterns:
                            for match in pattern.finditer(text):
                                raw = match.group(0)
                                # Determine type
                                if "Ø" in raw or "⌀" in raw:
                                    dim_type = "Diameter"
                                elif "R" in raw:
                                    dim_type = "Radius"
                                elif "°" in raw:
                                    dim_type = "Angle"
                                elif "-" in raw and any(x in raw for x in ["UNF", "UNC", "M"]):
                                    dim_type = "Thread"
                                elif "/" in raw:
                                    dim_type = "Fraction"
                                else:
                                    dim_type = "Linear"
                                value = raw.replace("Ø", "").replace("⌀", "").replace("R", "").replace("°", "").strip()
                                dimensions.append({
                                    'type': dim_type,
                                    'value': value,
                                    'raw': raw
                                })

    # Remove duplicates (by raw string)
    seen = set()
    unique_dimensions = []
    for d in dimensions:
        if d['raw'] not in seen:
            unique_dimensions.append(d)
            seen.add(d['raw'])

    return unique_dimensions

if __name__ == "__main__":
    pdf_path = r"C:\Users\Maxime Dumas\.cursor\PRT-044-0100-01.pdf"
    dimensions = extract_dimensions_from_pdf(pdf_path)

    print("\nExtracted Dimensions:")
    print("=" * 40)
    for idx, dim in enumerate(dimensions, 1):
        print(f"{idx:02d}. [{dim['type']}] {dim['value']}")

    print(f"\nTotal unique dimensions found: {len(dimensions)}")
    
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