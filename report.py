import csv
import io

from fpdf import FPDF


def generate_csv(summaries: list[dict]) -> str:
    """Generate CSV content from summaries.

    Each dict has keys: name, summary.
    Returns CSV as a string.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["File Name", "Summary"])
    for item in summaries:
        writer.writerow([item["name"], item["summary"]])
    return output.getvalue()


def generate_pdf(summaries: list[dict]) -> bytes:
    """Generate a PDF report from summaries.

    Returns PDF content as bytes.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 15, "Document Summary Report", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(10)

    for item in summaries:
        pdf.set_font("Helvetica", "B", 13)
        # Handle encoding issues for file names
        file_name = item.get("name", "Unknown").encode('latin-1', errors='ignore').decode('latin-1')
        pdf.cell(0, 8, file_name, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 11)
        # Handle encoding issues for summary text
        summary_text = item.get("summary", "").encode('latin-1', errors='ignore').decode('latin-1')
        pdf.multi_cell(0, 6, summary_text)
        pdf.ln(8)

    return pdf.output()
