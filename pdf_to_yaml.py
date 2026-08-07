import pymupdf  # Modern PyMuPDF import
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
    return any(ignore in title.strip().lower() for ignore in CHAPTER_IGNORE)

def should_ignore_subheading(title):
    return any(ignore in title.strip().lower() for ignore in SUBHEADING_IGNORE)

def simplify_leaf_nodes(nodes):
    """Cleans up the YAML by turning empty dictionaries into simple strings."""
    simplified = []
    for n in nodes:
        if not n["subheadings"]:
            simplified.append(n["title"])
        else:
            n["subheadings"] = simplify_leaf_nodes(n["subheadings"])
            simplified.append(n)
    return simplified

def extract_structure(pdf_path):
    # Updated to use the modern pymupdf namespace
    doc = pymupdf.open(pdf_path)
    toc = doc.get_toc() 
    
    book_structure = []
    stack = []
    ignore_threshold = float('inf')
    
    for item in toc:
        level, title, page = item
        
        # If we are deeper than an ignored parent, skip this item entirely
        if level > ignore_threshold:
            continue
        else:
            ignore_threshold = float('inf') # Reset threshold when we go back up the tree
            
        title_clean = title.strip()
        
        # Check if THIS node should trigger an ignore threshold
        if level == 1 and should_ignore_chapter(title_clean):
            ignore_threshold = level
            continue
        elif level > 1 and should_ignore_subheading(title_clean):
            ignore_threshold = level
            continue
            
        node = {"title": title_clean, "page": page, "subheadings": []}
        
        # Pop items off the stack until we find our true parent
        while stack and stack[-1][0] >= level:
            stack.pop()
            
        if not stack:
            # Level 1 items have no parent, add to root
            book_structure.append(node)
        else:
            # Append this node to its parent's subheadings list
            stack[-1][1]["subheadings"].append(node)
            
        stack.append((level, node))
        
    # Calculate lengths and clean up temporary 'page' data
    for i in range(len(book_structure)):
        start_page = book_structure[i]["page"]
        if i + 1 < len(book_structure):
            length = book_structure[i+1]["page"] - start_page
        else:
            length = doc.page_count - start_page 
            
        book_structure[i]["length_pages"] = max(1, length)
        del book_structure[i]["page"]
        
        # Clean up the nested leaf nodes for a prettier YAML
        book_structure[i]["subheadings"] = simplify_leaf_nodes(book_structure[i]["subheadings"])
        
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
        
    print(f"Extraction complete! Deeply nested structure saved to '{output_file}'.")

if __name__ == "__main__":
    main()