import pytest
from unittest.mock import patch, MagicMock
import yaml_to_trello

@patch('yaml_to_trello.os.getenv')
def test_trello_manager_init_missing_keys(mock_getenv, capsys):
    mock_getenv.return_value = None
    with pytest.raises(SystemExit):
        yaml_to_trello.TrelloManager()
    captured = capsys.readouterr()
    assert "Missing keys" in captured.out

@patch('yaml_to_trello.os.getenv')
def test_trello_manager_init_success(mock_getenv):
    mock_getenv.side_effect = lambda key: "val" if key in ["TRELLO_API_KEY", "TRELLO_TOKEN"] else None
    tm = yaml_to_trello.TrelloManager()
    assert tm.api_key == "val"
    assert tm.token == "val"

@patch('yaml_to_trello.requests.get')
@patch('yaml_to_trello.requests.post')
@patch('yaml_to_trello.os.getenv')
def test_get_or_create_label_existing(mock_getenv, mock_post, mock_get):
    mock_getenv.side_effect = lambda key: "val"
    tm = yaml_to_trello.TrelloManager()
    
    mock_response = MagicMock()
    mock_response.json.return_value = [{"id": "label_123", "name": "DevOps"}]
    mock_get.return_value = mock_response
    
    label_id = tm.get_or_create_label("board_123", "DevOps")
    assert label_id == "label_123"
    mock_post.assert_not_called()

@patch('yaml_to_trello.requests.get')
@patch('yaml_to_trello.requests.post')
@patch('yaml_to_trello.os.getenv')
def test_get_or_create_label_new(mock_getenv, mock_post, mock_get):
    mock_getenv.side_effect = lambda key: "val"
    tm = yaml_to_trello.TrelloManager()
    
    mock_get_response = MagicMock()
    mock_get_response.json.return_value = []
    mock_get.return_value = mock_get_response
    
    mock_post_response = MagicMock()
    mock_post_response.json.return_value = {"id": "label_456"}
    mock_post.return_value = mock_post_response
    
    label_id = tm.get_or_create_label("board_123", "NewTag")
    assert label_id == "label_456"
    mock_post.assert_called_once()

@patch('yaml_to_trello.os.getenv')
def test_flatten_subheadings(mock_getenv):
    mock_getenv.side_effect = lambda key: "val"
    tm = yaml_to_trello.TrelloManager()
    
    subheadings = [
        "Leaf 1",
        {"title": "Branch 1", "subheadings": ["Leaf 2"]}
    ]
    flat = tm._flatten_subheadings(subheadings)
    assert flat == ["Leaf 1", "Branch 1", "Branch 1 > Leaf 2"]

@patch('yaml_to_trello.requests.get')
@patch('yaml_to_trello.os.getenv')
def test_get_existing_card_names(mock_getenv, mock_get):
    mock_getenv.side_effect = lambda key: "val"
    tm = yaml_to_trello.TrelloManager()
    
    mock_response = MagicMock()
    mock_response.json.return_value = [{"name": "Card 1"}, {"name": "Card 2"}]
    mock_get.return_value = mock_response
    
    names = tm.get_existing_card_names("list_123")
    assert names == {"Card 1", "Card 2"}

@patch('yaml_to_trello.requests.post')
@patch('yaml_to_trello.os.getenv')
def test_create_card(mock_getenv, mock_post):
    mock_getenv.side_effect = lambda key: "val"
    tm = yaml_to_trello.TrelloManager()
    
    mock_post_response = MagicMock()
    mock_post_response.json.side_effect = [{"id": "card_123"}, {"id": "checklist_123"}]
    mock_post.return_value = mock_post_response
    
    tm.create_card("list_123", "Card Name", "label_123", "Comment text", ["Sub 1"])
    assert mock_post.call_count == 4

@patch('yaml_to_trello.sys.argv', ['yaml_to_trello.py'])
def test_main_no_args(capsys):
    with pytest.raises(SystemExit):
        yaml_to_trello.main()
    captured = capsys.readouterr()
    assert "Usage: python yaml_to_trello.py" in captured.out

@patch('yaml_to_trello.sys.argv', ['yaml_to_trello.py', 'test.yaml'])
@patch('builtins.open')
@patch('yaml_to_trello.yaml.safe_load')
@patch('yaml_to_trello.os.getenv')
@patch('builtins.input')
@patch('yaml_to_trello.TrelloManager')
def test_main_success(mock_trello_manager_class, mock_input, mock_getenv, mock_safe_load, mock_open):
    mock_getenv.return_value = "val"
    mock_input.side_effect = ["DevOps", ""]
    
    mock_safe_load.return_value = {
        "metadata": {"title": "Full Book Title", "author": "John Doe", "edition": "1st", "isbn": "1234"},
        "chapters": [
            {"title": "Chapter 1: Intro", "part": "1", "length_pages": 10, "subheadings": ["Sub 1"]},
            {"title": "Chapter 2: Outro", "part": "1", "length_pages": 15, "subheadings": []}
        ]
    }
    
    mock_trello_manager = MagicMock()
    mock_trello_manager.get_existing_card_names.return_value = {"Full Book Title: 1.1. Intro"}
    mock_trello_manager_class.return_value = mock_trello_manager
    
    yaml_to_trello.main()
    
    mock_trello_manager.create_card.assert_called_once()
    args, kwargs = mock_trello_manager.create_card.call_args
    assert kwargs["name"] == "Full Book Title: 1.2. Outro"
