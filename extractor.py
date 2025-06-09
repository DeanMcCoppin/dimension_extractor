import fitz
import re

def find_table_region(page, keywords, search_quadrant=None, padding=10):
    """
    Dynamically finds a table region based on keywords within a specified quadrant.
    Returns a fitz.Rect or None if not found.
    """
    found_rects = []
    page_width = page.rect.width
    page_height = page.rect.height

    # Define a rough quadrant bbox for initial keyword search if specified
    quadrant_bbox = None
    if search_quadrant == 'bottom_right':
        quadrant_bbox = fitz.Rect(page_width * 0.5, page_height * 0.5, page_width, page_height)
    elif search_quadrant == 'bottom_left':
        quadrant_bbox = fitz.Rect(0, page_height * 0.5, page_width * 0.5, page_height)

    for keyword in keywords:
        text_instances = page.search_for(keyword)
        for inst in text_instances:
            if quadrant_bbox and not inst.intersects(quadrant_bbox): # Filter by quadrant if specified
                continue
            found_rects.append(inst)

    if not found_rects:
        return None # Return None if no keywords found

    # Combine all found keyword rects into one large bounding box
    union_rect = fitz.Rect()
    for rect in found_rects:
        union_rect |= rect

    # Add some padding around the found union rect
    union_rect.x0 = max(0, union_rect.x0 - padding)
    union_rect.y0 = max(0, union_rect.y0 - padding)
    union_rect.x1 = min(page_width, union_rect.x1 + padding)
    union_rect.y1 = min(page_height, union_rect.y1 + padding)

    return union_rect

def extract_dimensions_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    
    drawing_dimensions = []
    part_numbers = []
    general_tolerances = []

    # Set a reasonable max length for linear numeric values to filter noise (adjustable parameter)
    MAX_LINEAR_NUMERIC_LENGTH = 15

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_width = page.rect.width
        page_height = page.rect.height

        # Dynamically find Title Block and Material Table regions
        title_block_keywords = ["PRT-", "DRAWN BY", "APPROVED BY", "SCALE", "SHEET", "REV", "DWG NO."]

        title_block_bbox = find_table_region(page, title_block_keywords, 'bottom_right')
        if not title_block_bbox:
            # Fallback if keywords not found: standard bottom-right area
            title_block_bbox = fitz.Rect(page_width * 0.60, page_height * 0.75, page_width * 0.95, page_height * 0.95)

        # Material/Finish Table (bottom-left)
        material_table_keywords = ["MATERIAL", "FINISH", "EXTENSION", "TRAITEMENT DE SURFACE", "TREATMENT"]
        material_table_bbox = find_table_region(page, material_table_keywords, 'bottom_left')
        # Note: If material_table_bbox is None, it means the table wasn't found, which is fine; it won't be excluded.

        # --- Regex Patterns for specific dimension types (ordered by specificity) ---
        patterns = [
            # 1. Diameter (e.g., Ø.201, ⌀.201, 8X Ø.201, 8X⌀.201, 02.13, O2.13)
            # This regex looks for:
            # - Optional multiplier (e.g., "8X", "8 X")
            # - Diameter symbol (Ø or ⌀) OR common OCR misinterpretations like '0' or 'O'
            # - Optional whitespace after the symbol/character
            # - The numeric value (decimal or fraction)
            # - Optional units (e.g., ", 'in", "mm", "cm")
            (re.compile(r'(\d*\s*[Xx])?[\s]*[Ø⌀0O][\s]*([0-9]+[.,]?[0-9]*|[0-9]+/[0-9]+)(?:["\'in]*|mm|cm)?', re.IGNORECASE), "Diameter"),
            # 2. Radius (e.g., R2.250, R17/32) - prioritize fraction over decimal
            (re.compile(r'R\s*([0-9]+/[0-9]+|[0-9]+[.,]?[0-9]*)(?:["\'in]*|mm|cm)?', re.IGNORECASE), "Radius"),
            # 3. Angles (e.g., 60°, 100°)
            (re.compile(r'([0-9]+[.,]?[0-9]*)\s*°', re.IGNORECASE), "Angle"),
            # 4. Thread/Bolt Callouts (e.g., 10-32 UNF)
            (re.compile(r'([0-9]+-[0-9]+(?:\s*[A-Z]{2,4})?)', re.IGNORECASE), "Thread"),
            # 5. Linear Fractions (e.g., 3/16, 1/2)
            (re.compile(r'([0-9]+/[0-9]+)(?:["\'in]*|mm|cm)?', re.IGNORECASE), "Fraction"),
            # 6. Basic Linear Dimensions (e.g., 4.50, 1,500, .750, 8.89, 10,06) - broad, so last
            (re.compile(r'(?<![A-Za-z0-9])([0-9]*[.,][0-9]+|[0-9]+)(?:["\'in]*|mm|cm)?(?![A-Za-z0-9])', re.IGNORECASE), "Linear"),
        ]

        # --- Patterns for Part Number and General Tolerances in Title Block ---
        part_number_pattern = re.compile(r'(PRT-[0-9]{3}-[0-9]{4}-[0-9]{2})', re.IGNORECASE)
        tolerance_pattern = re.compile(r'[\+\-±][\s]*([0-9]+[.,]?[0-9]*|[0-9]+/[0-9]+)(?:["\'in]*|mm|cm)?', re.IGNORECASE)

        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            # Process text line by line within each block
            if "lines" in block:
                for line in block["lines"]:
                    line_text = "".join(span["text"] for span in line["spans"]).strip()
                    if not line_text:
                        continue

                    # Determine if this line's bounding box is within the title block or material table
                    line_bbox = fitz.Rect()
                    for span in line["spans"]:
                        line_bbox |= fitz.Rect(span["bbox"])

                    is_in_title_block = line_bbox.intersects(title_block_bbox)
                    is_in_material_table = material_table_bbox and line_bbox.intersects(material_table_bbox)

                    # Only process drawing area for drawing dimensions
                    temp_line_dimensions = []
                    if not is_in_title_block and not is_in_material_table:
                        for compiled_pattern, dim_type in patterns:
                            if compiled_pattern.search(line_text):
                                # If any pattern matches, consider the entire line as a relevant dimension line
                                temp_line_dimensions.append(line_text)
                                break # Move to the next pattern once a measurement is found on this line
                    
                    # Add the identified measurement lines to the global list
                    drawing_dimensions.extend(temp_line_dimensions)

                # --- Extract Part Number and General Tolerances (only from Title Block Area) ---
            elif is_in_title_block:
                    pn_match = part_number_pattern.search(line_text)
                    if pn_match and pn_match.group(0) not in [pn['value'] for pn in part_numbers]:
                        part_numbers.append({
                            'type': 'Part Number',
                                'value': pn_match.group(0)
                            })
                    
                    for tol_match in tolerance_pattern.finditer(line_text):
                        tol_value = tol_match.group(0).strip()
                        if tol_value not in [gt['value'] for gt in general_tolerances]:
                            general_tolerances.append({
                                'type': 'General Tolerance',
                                'value': tol_value
                            })

    # Final de-duplication of unique lines for drawing dimensions
    unique_drawing_dimensions = sorted(list(set(drawing_dimensions)))

    return {
        "drawing_dimensions": unique_drawing_dimensions,
        "part_numbers": part_numbers,
        "general_tolerances": general_tolerances
    }

# The main execution block (for direct testing or app integration)
if __name__ == "__main__":
    pdf_path = r"Test Drawing\PRT-044-0110-01.pdf"
    results = extract_dimensions_from_pdf(pdf_path)

    print("\n--- Drawing Dimensions ---\n")
    if results["drawing_dimensions"]:
        for idx, dim in enumerate(results["drawing_dimensions"], 1):
            print(f"{idx:02d}. {dim}")
    else:
        print("No drawing dimensions found.\n")

    print("\n--- Part Numbers ---\n")
    if results["part_numbers"]:
        for idx, pn in enumerate(results["part_numbers"], 1):
            print(f"{idx:02d}. [{pn['type']}] {pn['value']}")
    else:
        print("No part numbers found.\n")

    print("\n--- General Tolerances ---\n")
    if results["general_tolerances"]:
        for idx, tol in enumerate(results["general_tolerances"], 1):
            print(f"{idx:02d}. [{tol['type']}] {tol['value']}")
    else:
        print("No general tolerances found.\n")

    total_found = len(results["drawing_dimensions"]) + len(results["part_numbers"]) + len(results["general_tolerances"])
    print(f"\nTotal items extracted: {total_found}\n")

    # Optional: Save to a text file for easier review
    with open('categorized_dimensions_report.txt', 'w', encoding='utf-8') as f:
        f.write("Categorized Dimensions Report\n")
        f.write("=" * 40 + "\n\n")
        
        f.write("--- Drawing Dimensions ---\n")
        if results["drawing_dimensions"]:
            for idx, dim in enumerate(results["drawing_dimensions"], 1):
                f.write(f"{idx:02d}. {dim}\n")
        else:
            f.write("No drawing dimensions found.\n")
        f.write("\n")

        f.write("--- Part Numbers ---\n")
        if results["part_numbers"]:
            for idx, pn in enumerate(results["part_numbers"], 1):
                f.write(f"{idx:02d}. [{pn['type']}] {pn['value']}\n")
        else:
            f.write("No part numbers found.\n")
        f.write("\n")

        f.write("--- General Tolerances ---\n")
        if results["general_tolerances"]:
            for idx, tol in enumerate(results["general_tolerances"], 1):
                f.write(f"{idx:02d}. [{tol['type']}] {tol['value']}\n")
        else:
            f.write("No general tolerances found.\n")
        f.write("\n")
        f.write(f"Total items extracted: {total_found}\n")