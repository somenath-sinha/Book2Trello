"""
Extracts the table of contents and structure from a PDF file
and outputs it as a YAML file, filtering out unwanted chapters.
"""

import pymupdf
import yaml
import sys
import re

CHAPTER_IGNORE = [
    "cover", "copyright", "table of contents", "colophon", 
    "acknowledgment", "acknowledgements", "dedication", 
    "preface", "index", "appendix", "bibliography", "about the author"
]

SUBHEADING_IGNORE = [
    "exercise", "case study question", "examples", 
    "learning assessment", "challenge", "capstone project"
]

def should_ignore_chapter(title):
    """
    Checks if a chapter title should be ignored based on a predefined list
    (e.g., prefaces, indices, appendices).
    """
    return any(ignore in title.strip().lower() for ignore in CHAPTER_IGNORE)

def should_ignore_subheading(title):
    """
    Checks if a subheading should be ignored based on a predefined list
    (e.g., exercises, case studies).
    """
    return any(ignore in title.strip().lower() for ignore in SUBHEADING_IGNORE)

def is_structural_grouping(title):
    """
    Identifies structural groupings like 'Part I' or 'Section 3'.
    Returns the regex match object if found.
    """
    # Catches "Part I", "Part 1", "Section IV", "Unit 3", etc.
    return re.match(r'^(part|section|unit)\s+([ivx]+|\d+)', title.strip(), re.IGNORECASE)

def simplify_leaf_nodes(nodes):
    """
    Simplifies nodes with empty subheadings into a flat string list.
    """
    simplified = []
    for n in nodes:
        if not n["subheadings"]:
            simplified.append(n["title"])
        else:
            n["subheadings"] = simplify_leaf_nodes(n["subheadings"])
            simplified.append(n)
    return simplified

def extract_structure(pdf_path):
    """
    Extracts metadata and the structural hierarchy of the book from a PDF.
    Returns a dictionary containing the extracted data.
    """
    doc = pymupdf.open(pdf_path)
    
    meta = doc.metadata
    full_title = meta.get("title") or "Unknown Title"
    
    if full_title != "Unknown Title":
        short_title = re.split(r'[:\-]', full_title)[0].strip()
    else:
        try:
            first_page_lines = doc[0].get_text().strip().split('\n')
            short_title = next((line.strip() for line in first_page_lines if len(line.strip()) > 3), "Unknown Title")
        except Exception:
            short_title = "Unknown Title"

    metadata_dict = {
        "title": full_title,
        "short_title": short_title,
        "author": meta.get("author") or "Unknown Author"
    }
    
    toc = doc.get_toc() 
    book_structure = []
    stack = []
    ignore_threshold = float('inf')
    current_part = ""
    
    for item in toc:
        level, title_text, page = item
        
        if level > ignore_threshold:
            continue
        else:
            ignore_threshold = float('inf')
            
        title_clean = title_text.strip()
        
        # Identify the active Part/Section prefix (e.g., "I", "II", "1")
        part_match = is_structural_grouping(title_clean)
        if part_match:
            current_part = part_match.group(2).upper()
            stack.clear()
            continue
            
        while stack and stack[-1][0] >= level:
            stack.pop()
            
        is_root = len(stack) == 0
        
        if is_root and should_ignore_chapter(title_clean):
            ignore_threshold = level
            continue
        elif not is_root and should_ignore_subheading(title_clean):
            ignore_threshold = level
            continue
            
        node = {"title": title_clean, "page": page, "subheadings": []}
        
        # Tag root chapters with their governing Part
        if is_root and current_part:
            node["part"] = current_part
        
        if is_root:
            book_structure.append(node)
        else:
            stack[-1][1]["subheadings"].append(node)
            
        stack.append((level, node))
        
    first_chapter_page = book_structure[0]["page"] if book_structure else 0
    front_matter_text = ""
    for p_num in range(min(first_chapter_page - 1, doc.page_count)):
        front_matter_text += doc[p_num].get_text()
        
    isbn_match = re.search(r'ISBN(?:-1[03])?(?:\s*:\s*|\s+)([0-9-]{10,17}[Xx]?)', front_matter_text, re.IGNORECASE)
    edition_match = re.search(r'((?:\d+(?:st|nd|rd|th)|[Ff]irst|[Ss]econd|[Tt]hird|[Ff]ourth|[Ff]ifth|[Ss]ixth|[Ss]eventh|[Ee]ighth|[Nn]inth|[Tt]enth)\s+[Ee]dition)', front_matter_text)
    
    if isbn_match:
        metadata_dict["isbn"] = isbn_match.group(1).strip()
    if edition_match:
        metadata_dict["edition"] = edition_match.group(1).strip()

    for i in range(len(book_structure)):
        start_page = book_structure[i]["page"]
        if i + 1 < len(book_structure):
            length = book_structure[i+1]["page"] - start_page
        else:
            length = doc.page_count - start_page 
            
        book_structure[i]["length_pages"] = max(1, length)
        if "page" in book_structure[i]:
            del book_structure[i]["page"]
        book_structure[i]["subheadings"] = simplify_leaf_nodes(book_structure[i]["subheadings"])
        
    return {
        "metadata": metadata_dict,
        "chapters": book_structure
    }

def main():
    """
    Main entry point. Parses command-line arguments and triggers
    extraction and YAML saving.
    """
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_yaml.py ")
        sys.exit(1)
        
    pdf_file = sys.argv[1]
    structure = extract_structure(pdf_file)
    
    output_file = "book_structure.yaml"
    with open(output_file, "w", encoding="utf-8") as f:
        yaml.dump(structure, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
    print(f"Extraction complete! Metadata and structure saved to '{output_file}'.")

if __name__ == "__main__":
    main()