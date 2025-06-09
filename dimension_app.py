import tkinter as tk
from tkinter import filedialog, scrolledtext
from extractor import extract_dimensions_from_pdf
import os # Import the os module

# Global variable for the file name label
file_name_label = None

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if file_path:
        # Extract just the filename from the full path
        display_file_name = os.path.basename(file_path)
        file_name_label.config(text=f"Selected PDF: {display_file_name}")

        try:
            dims = extract_dimensions_from_pdf(file_path)
            if not dims:
                text_box.delete(1.0, tk.END)
                text_box.insert(tk.END, "No dimensions found in this PDF.")
            else:
                output_lines = []
                
                if dims["drawing_dimensions"]:
                    output_lines.append("--- Drawing Dimensions ---")
                    for idx, dim_line in enumerate(dims["drawing_dimensions"], 1):
                        output_lines.append(f"{idx:02d}. {dim_line}")
                    output_lines.append("")
                
                if dims["part_numbers"]:
                    output_lines.append("--- Part Numbers ---")
                    for idx, pn in enumerate(dims["part_numbers"], 1):
                        output_lines.append(f"{idx:02d}. [{pn['type']}] {pn['value']}")
                    output_lines.append("")

                if dims["general_tolerances"]:
                    output_lines.append("--- General Tolerances ---")
                    for idx, tol in enumerate(dims["general_tolerances"], 1):
                        output_lines.append(f"{idx:02d}. [{tol['type']}] {tol['value']}")
                    output_lines.append("")

                if not output_lines:
                    output_lines.append("No dimensions, part numbers, or general tolerances found in this PDF.")

                text_box.delete(1.0, tk.END)
                text_box.insert(tk.END, "\n".join(output_lines))
        except Exception as e:
            text_box.delete(1.0, tk.END)
            text_box.insert(tk.END, f"Error: {e}")

# Create the main window
root = tk.Tk()
root.title("PDF Dimension Extractor")

# Create a label to display the selected file name
file_name_label = tk.Label(root, text="No PDF selected", font=("Consolas", 12, "bold"))
file_name_label.pack(pady=5)

# Create a button to select file
btn = tk.Button(root, text="Select PDF and Extract Dimensions", command=select_file)
btn.pack(pady=10)

# Create a scrolled text box for output
text_box = scrolledtext.ScrolledText(root, width=80, height=20, font=("Consolas", 10))
text_box.pack(padx=10, pady=10)

# Run the application
root.mainloop()
