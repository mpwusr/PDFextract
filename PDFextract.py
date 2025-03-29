import zipfile
from pathlib import Path
import PyPDF2
import shutil
from reportlab.pdfgen import canvas
import io
from dotenv import load_dotenv
import os

load_dotenv()


def extract_and_convert_to_pdf():
    zip_path = os.getenv("ZIP_PATH")
    file_extension = os.getenv("FILE_EXTENSION")
    output_pdf_path = os.getenv("OUTPUT_PDF_PATH")

    if not all([zip_path, file_extension, output_pdf_path]):
        raise ValueError("Missing required environment variables in .env file")

    if not file_extension.startswith('.'):
        file_extension = f".{file_extension}"

    temp_dir = Path("temp_extract")
    temp_dir.mkdir(exist_ok=True)

    try:
        if not Path(zip_path).exists():
            raise FileNotFoundError(f"ZIP file not found at: {zip_path}")

        pdf_writer = PyPDF2.PdfWriter()
        files_processed = 0

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            matching_files = [f for f in zip_ref.infolist()
                              if f.filename.lower().endswith(file_extension.lower())]

            if not matching_files:
                raise ValueError(f"No files with extension {file_extension} found in ZIP")

            print(f"Found {len(matching_files)} matching files")

            for file_info in matching_files:
                print(f"Processing: {file_info.filename}")
                zip_ref.extract(file_info, temp_dir)
                extracted_file = temp_dir / file_info.filename

                # Handle .kt files (and .txt) as text-based files
                if file_extension.lower() in ['.txt', '.kt']:
                    try:
                        pdf_buffer = convert_text_to_pdf(str(extracted_file))
                        pdf_reader = PyPDF2.PdfReader(pdf_buffer)
                        for i in range(len(pdf_reader.pages)):
                            pdf_writer.add_page(pdf_reader.pages[i])
                        files_processed += 1
                        print(f"Added {len(pdf_reader.pages)} page(s) from {file_info.filename}")
                    except Exception as e:
                        print(f"Error processing {file_info.filename}: {str(e)}")

        if files_processed == 0:
            raise ValueError("No files were successfully processed")

        print(f"Total files processed: {files_processed}")
        print(f"Total pages in PDF: {len(pdf_writer.pages)}")

        with open(output_pdf_path, 'wb') as output_pdf:
            pdf_writer.write(output_pdf)
            print(f"PDF written to: {output_pdf_path}")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def convert_text_to_pdf(text_path):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)

    try:
        with open(text_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        raise ValueError(f"Failed to read file {text_path}: {str(e)}")

    if not text.strip():
        raise ValueError(f"File {text_path} is empty")

    text_lines = text.split('\n')
    y = 750
    for line in text_lines:
        # Handle longer lines by splitting them
        while len(line) > 90:  # Assuming ~90 chars fit on a line
            c.drawString(100, y, line[:90])
            line = line[90:]
            y -= 15
            if y < 50:
                c.showPage()
                y = 750
        if line:
            c.drawString(100, y, line)
            y -= 15
        if y < 50:
            c.showPage()
            y = 750

    c.save()
    buffer.seek(0)
    return buffer


if __name__ == "__main__":
    try:
        extract_and_convert_to_pdf()
        print("PDF conversion completed successfully!")
    except Exception as e:
        print(f"An error occurred: {str(e)}")