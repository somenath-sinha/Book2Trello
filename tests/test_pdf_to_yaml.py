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
