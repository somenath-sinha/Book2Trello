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
