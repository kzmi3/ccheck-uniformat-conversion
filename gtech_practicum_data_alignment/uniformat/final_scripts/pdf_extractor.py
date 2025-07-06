import fitz # PyMuPDF

def extract_text_from_pdf_pages(pdf_path, start_page, end_page):
    text = ""
    try:
        doc = fitz.open(pdf_path)
        # PyMuPDF pages are 0-indexed, so adjust accordingly
        for page_num in range(start_page - 1, end_page):
            if page_num < len(doc):
                page = doc.load_page(page_num)
                text += page.get_text()
            else:
                print(f"Warning: Page {page_num + 1} is out of bounds.")
                break # Stop if we hit end of document
    except FileNotFoundError:
        print(f"Error: PDF file not found at '{pdf_path}'")
        return None
    except Exception as e:
        print(f"An error occurred during PDF text extraction: {e}")
        return None
    finally:
        if 'doc' in locals() and doc:
            doc.close()
    return text