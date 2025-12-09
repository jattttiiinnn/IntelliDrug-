from fpdf import FPDF
import os

def create_pdf_with_bullets():
    # Create PDF object
    pdf = FPDF()
    
    # Add a page
    pdf.add_page()
    
    # Method 1: Using Arial (usually available on Windows)
    try:
        pdf.add_font('Arial', '', 'arial.ttf', uni=True)
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, 'Using Arial font:', ln=True)
        pdf.cell(0, 10, '• First item with Arial', ln=True)
        pdf.cell(0, 10, '• Second item with Arial', ln=True)
        pdf.ln(10)
    except Exception as e:
        print(f"Arial font not available: {e}")
    
    # Method 2: Using DejaVu (needs to be downloaded if not available)
    try:
        # Check if DejaVu font is available in the current directory
        dejavu_path = 'DejaVuSansCondensed.ttf'
        if os.path.exists(dejavu_path):
            pdf.add_font('DejaVu', '', dejavu_path, uni=True)
            pdf.set_font('DejaVu', '', 12)
            pdf.cell(0, 10, 'Using DejaVu font:', ln=True)
            pdf.cell(0, 10, '• First item with DejaVu', ln=True)
            pdf.cell(0, 10, '• Second item with DejaVu', ln=True)
            pdf.cell(0, 10, '• Special characters: áéíóú ñ ç © ®', ln=True)
        else:
            print("DejaVu font not found. Download it from: https://dejavu-fonts.github.io/")
    except Exception as e:
        print(f"Error with DejaVu font: {e}")
    
    # Save the PDF
    output_file = 'output_with_bullets.pdf'
    pdf.output(output_file)
    print(f"PDF created successfully: {os.path.abspath(output_file)}")
    print("\nNote: If you see empty boxes instead of bullet points, please download the DejaVu font from:")
    print("https://dejavu-fonts.github.io/")
    print("And place the .ttf file in the same directory as this script.")

if __name__ == "__main__":
    create_pdf_with_bullets()
