import pymupdf as fitz
import yaml
import sys

# Level 1: Entire chapters to drop
CHAPTER_IGNORE = [
    "cover", "copyright", "table of contents", "colophon", 
    "acknowledgment", "acknowledgements", "dedication", 
    "preface", "index", "appendix", "bibliography", "about the author"
]

# Level 2: Subheadings to drop from valid chapters
SUBHEADING_IGNORE = [
    "exercise", "case study question", "examples", 
    "learning assessment", "challenge", "capstone project"
]

def should_ignore_chapter(title):
    title_lower = title.strip().lower()
    # Check if any fluff keyword is in the chapter title
    return any(ignore in title_lower for ignore in CHAPTER_IGNORE)

def should_ignore_subheading(title):
    title_lower = title.strip().lower()
    # Check if any fluff keyword is in the subheading
    return any(ignore in title_lower for ignore in SUBHEADING_IGNORE)

def extract_structure(pdf_path):
    doc = fitz.open(pdf_path)
    toc = doc.get_toc() 
    
    book_structure = []
    current_chapter = None
    
    for item in toc:
        level, title, page = item
        
        if level == 1:
            if should_ignore_chapter(title):
                # Nullify current_chapter so its subheadings are also skipped
                current_chapter = None 
                continue
                
            current_chapter = {
                "title": title.strip(),
                "page": page,
                "subheadings": []
            }
            book_structure.append(current_chapter)
            
        elif level == 2 and current_chapter is not None:
            if not should_ignore_subheading(title):
                current_chapter["subheadings"].append(title.strip())
            
    # Calculate chapter lengths
    for i in range(len(book_structure)):
        start_page = book_structure[i]["page"]
        
        # If there's a next chapter, use its start page to calculate length
        if i + 1 < len(book_structure):
            end_page = book_structure[i+1]["page"]
            length = end_page - start_page
        else:
            # For the final chapter, use the total page count of the PDF
            length = doc.page_count - start_page 
            
        book_structure[i]["length_pages"] = max(1, length)
        del book_structure[i]["page"] # Clean up the page number from the final YAML
        
    return book_structure

def main():
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_yaml.py <path_to_pdf>")
        sys.exit(1)
        
    pdf_file = sys.argv[1]
    structure = extract_structure(pdf_file)
    
    output_file = "book_structure.yaml"
    with open(output_file, "w", encoding="utf-8") as f:
        yaml.dump(structure, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
    print(f"Extraction complete! Filtered out non-content chapters and exercises.")
    print(f"Please review '{output_file}' before pushing to Trello.")

if __name__ == "__main__":
    main()