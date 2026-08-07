import pytest
from unittest.mock import patch, MagicMock
import pdf_to_yaml

def test_should_ignore_chapter():
    assert pdf_to_yaml.should_ignore_chapter("Table of Contents") == True
    assert pdf_to_yaml.should_ignore_chapter("Chapter 1: The Beginning") == False

def test_should_ignore_subheading():
    assert pdf_to_yaml.should_ignore_subheading("Exercise 1") == True
    assert pdf_to_yaml.should_ignore_subheading("Core Concepts") == False

def test_is_structural_grouping():
    assert pdf_to_yaml.is_structural_grouping("Part I") is not None
    assert pdf_to_yaml.is_structural_grouping("Section 3") is not None
    assert pdf_to_yaml.is_structural_grouping("Chapter 1") is None

def test_simplify_leaf_nodes():
    nodes = [
        {"title": "Leaf 1", "subheadings": []},
        {"title": "Branch 1", "subheadings": [{"title": "Leaf 2", "subheadings": []}]}
    ]
    simplified = pdf_to_yaml.simplify_leaf_nodes(nodes)
    assert simplified[0] == "Leaf 1"
    assert simplified[1]["title"] == "Branch 1"
    assert simplified[1]["subheadings"][0] == "Leaf 2"

@patch('pdf_to_yaml.pymupdf.open')
def test_extract_structure(mock_open):
    mock_doc = MagicMock()
    mock_doc.metadata = {"title": "Test Book", "author": "Test Author"}
    mock_doc.get_toc.return_value = [
        [1, "Part I", 1],
        [1, "Chapter 1", 2],
        [2, "Subheading 1", 3]
    ]
    mock_doc.page_count = 10
    
    mock_page = MagicMock()
    mock_page.get_text.return_value = "ISBN: 1234567890\nFirst Edition"
    mock_doc.__getitem__.return_value = mock_page
    
    mock_open.return_value = mock_doc
    
    result = pdf_to_yaml.extract_structure("dummy.pdf")
    assert result["metadata"]["title"] == "Test Book"
    assert result["metadata"]["isbn"] == "1234567890"
    assert result["chapters"][0]["title"] == "Chapter 1"
    assert result["chapters"][0]["subheadings"][0] == "Subheading 1"

@patch('pdf_to_yaml.pymupdf.open')
def test_extract_structure_unknown_title(mock_open):
    mock_doc = MagicMock()
    mock_doc.metadata = {"title": "", "author": "Test Author"}
    mock_doc.get_toc.return_value = []
    mock_doc.page_count = 1
    
    mock_page = MagicMock()
    mock_page.get_text.return_value = " \n \nValid Title\n "
    mock_doc.__getitem__.return_value = mock_page
    mock_open.return_value = mock_doc
    
    result = pdf_to_yaml.extract_structure("dummy.pdf")
    assert result["metadata"]["title"] == "Unknown Title"
    assert result["metadata"]["short_title"] == "Valid Title"

@patch('pdf_to_yaml.pymupdf.open')
def test_extract_structure_unknown_title_exception(mock_open):
    mock_doc = MagicMock()
    mock_doc.metadata = {"title": "", "author": "Test Author"}
    mock_doc.get_toc.return_value = []
    mock_doc.page_count = 1
    
    mock_doc.__getitem__.side_effect = Exception("Page error")
    mock_open.return_value = mock_doc
    
    result = pdf_to_yaml.extract_structure("dummy.pdf")
    assert result["metadata"]["short_title"] == "Unknown Title"

@patch('pdf_to_yaml.pymupdf.open')
def test_extract_structure_complex_toc(mock_open):
    mock_doc = MagicMock()
    mock_doc.metadata = {"title": "Test Book"}
    mock_doc.get_toc.return_value = [
        [1, "Chapter 1", 1],
        [2, "Sub 1", 2],
        [2, "Exercise 1", 3],
        [3, "Deep ignore", 4],
        [1, "Chapter 2", 5],
        [1, "Index", 6],
        [2, "Index sub", 7],
    ]
    mock_doc.page_count = 10
    
    mock_page = MagicMock()
    mock_page.get_text.return_value = ""
    mock_doc.__getitem__.return_value = mock_page
    mock_open.return_value = mock_doc
    
    result = pdf_to_yaml.extract_structure("dummy.pdf")
    chapters = result["chapters"]
    
    assert len(chapters) == 2
    assert chapters[0]["title"] == "Chapter 1"
    assert chapters[0]["length_pages"] == 4
    assert len(chapters[0]["subheadings"]) == 1
    assert chapters[0]["subheadings"][0] == "Sub 1"
    
    assert chapters[1]["title"] == "Chapter 2"
    assert chapters[1]["length_pages"] == 5

@patch('pdf_to_yaml.sys.argv', ['pdf_to_yaml.py'])
def test_main_no_args(capsys):
    with pytest.raises(SystemExit):
        pdf_to_yaml.main()
    captured = capsys.readouterr()
    assert "Usage: python pdf_to_yaml.py" in captured.out

@patch('pdf_to_yaml.sys.argv', ['pdf_to_yaml.py', 'test.pdf'])
@patch('pdf_to_yaml.extract_structure')
@patch('builtins.open')
@patch('pdf_to_yaml.yaml.dump')
def test_main_success(mock_dump, mock_open, mock_extract, capsys):
    mock_extract.return_value = {"metadata": {}, "chapters": []}
    pdf_to_yaml.main()
    mock_dump.assert_called_once()
    captured = capsys.readouterr()
    assert "Extraction complete" in captured.out
