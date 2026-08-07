import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Import the module. We need to mock os.getenv and requests.
import nuke_trello_list

@patch('nuke_trello_list.os.getenv')
def test_missing_env_vars(mock_getenv, capsys):
    mock_getenv.return_value = None
    with pytest.raises(SystemExit) as e:
        nuke_trello_list.main()
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Error: Missing API Key" in captured.out

@patch('nuke_trello_list.os.getenv')
@patch('nuke_trello_list.requests.get')
def test_empty_list(mock_get, mock_getenv, capsys):
    mock_getenv.side_effect = ["key", "token", "list_id"]
    
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_get.return_value = mock_response
    
    nuke_trello_list.main()
    captured = capsys.readouterr()
    assert "already completely empty" in captured.out

@patch('nuke_trello_list.os.getenv')
@patch('nuke_trello_list.requests.get')
@patch('builtins.input')
def test_abort_sequence(mock_input, mock_get, mock_getenv, capsys):
    mock_getenv.side_effect = ["key", "token", "list_id"]
    
    mock_response = MagicMock()
    mock_response.json.return_value = [{"id": "1", "name": "Card 1"}]
    mock_get.return_value = mock_response
    
    mock_input.return_value = "n"
    
    nuke_trello_list.main()
    captured = capsys.readouterr()
    assert "Abort sequence confirmed" in captured.out

@patch('nuke_trello_list.os.getenv')
@patch('nuke_trello_list.requests.get')
@patch('nuke_trello_list.requests.delete')
@patch('builtins.input')
def test_purge_sequence(mock_input, mock_delete, mock_get, mock_getenv, capsys):
    mock_getenv.side_effect = ["key", "token", "list_id"]
    
    mock_response = MagicMock()
    mock_response.json.return_value = [{"id": "1", "name": "Card 1"}]
    mock_get.return_value = mock_response
    
    mock_input.return_value = "y"
    
    nuke_trello_list.main()
    captured = capsys.readouterr()
    assert "Purge complete" in captured.out
    mock_delete.assert_called_once()
