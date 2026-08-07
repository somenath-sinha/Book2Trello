import fitz  # PyMuPDF
import yaml
import sys

# Sections to ignore (case-insensitive)
IGNORE_LIST = [
    "acknowledgment", "acknowledgements", "dedication", 
    "preface", "index", "appendix", "bibliography", "about the author"
]

def should_ignore(title):
    title_lower = title.strip().lower()
    return any(ignore_word in title_lower for ignore_word in IGNORE_LIST)

def extract_structure(pdf_path):
    doc = fitz.open(pdf_path)
    toc = doc.get_toc() # Returns a list: [level, title, page_number]
    
    book_structure = []
    current_chapter = None
    
    for item in toc:
        level, title, page = item
        
        if should_ignore(title):
            continue
            
        if level == 1:
            current_chapter = {
                "title": title.strip(),
                "page": page,
                "subheadings": []
            }
            book_structure.append(current_chapter)
        elif level == 2 and current_chapter is not None:
            current_chapter["subheadings"].append(title.strip())
            
    # Calculate chapter lengths (assuming next chapter's start page - current start page)
    for i in range(len(book_structure)):
        start_page = book_structure[i]["page"]
        if i + 1 < len(book_structure):
            end_page = book_structure[i+1]["page"]
            length = end_page - start_page
        else:
            length = doc.page_count - start_page # Last chapter goes to end of book
            
        book_structure[i]["length_pages"] = max(1, length)
        del book_structure[i]["page"] # Clean up the YAML
        
    return book_structure

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_yaml.py <path_to_pdf>")
        sys.exit(1)
        
    pdf_file = sys.argv[1]
    structure = extract_structure(pdf_file)
    
    output_file = "book_structure.yaml"
    with open(output_file, "w", encoding="utf-8") as f:
        yaml.dump(structure, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
    print(f"Extraction complete! Please review '{output_file}' and remove any unwanted items before proceeding.")