# tests/test_core.py
import pytest
from git_change_detect.core import parse_yaml_content, deep_diff, get_file_content_from_commit

# Tests for parse_yaml_content
def test_parse_valid_yaml():
    content = "key: value\nnested:\n  key2: value2"
    expected = {"key": "value", "nested": {"key2": "value2"}}
    assert parse_yaml_content(content) == expected

def test_parse_invalid_yaml():
    content = "key: 'unclosed quote"
    assert parse_yaml_content(content) == {}

def test_parse_empty_yaml():
    content = ""
    assert parse_yaml_content(content) == {}

# Tests for deep_diff
def test_deep_diff_added():
    old_dict = {"a": 1}
    new_dict = {"a": 1, "b": 2}
    diff = deep_diff(old_dict, new_dict)
    assert len(diff) == 1
    assert diff[0]["action"] == "ADD"
    assert diff[0]["key_path"] == "b"
    assert diff[0]["value"] == 2

def test_deep_diff_deleted():
    old_dict = {"a": 1, "b": 2}
    new_dict = {"a": 1}
    diff = deep_diff(old_dict, new_dict)
    assert len(diff) == 1
    assert diff[0]["action"] == "DELETE"
    assert diff[0]["key_path"] == "b"

def test_deep_diff_edited():
    old_dict = {"a": 1}
    new_dict = {"a": 2}
    diff = deep_diff(old_dict, new_dict)
    assert len(diff) == 1
    assert diff[0]["action"] == "EDIT"
    assert diff[0]["key_path"] == "a"
    assert diff[0]["value"] == 2

def test_deep_diff_nested():
    old_dict = {"a": {"b": 1}}
    new_dict = {"a": {"b": 2, "c": 3}}
    diff = deep_diff(old_dict, new_dict)
    assert len(diff) == 2
    # The order of diffs is not guaranteed, so we check for presence
    expected_diffs = [
        {"action": "EDIT", "key_path": "a.b", "value": 2},
        {"action": "ADD", "key_path": "a.c", "value": 3}
    ]
    for d in diff:
        assert d in expected_diffs

# Tests for get_file_content_from_commit
def test_get_file_content_from_commit(mocker):
    mock_repo = mocker.MagicMock()
    mock_repo.git.show.return_value = "file content"
    mocker.patch('git.Repo', return_value=mock_repo)

    content = get_file_content_from_commit("fake/path", "some_hash", "file.txt")

    assert content == "file content"
    mock_repo.git.show.assert_called_once_with('some_hash:file.txt')

def test_get_file_content_from_commit_error(mocker):
    mock_repo = mocker.MagicMock()
    # Simulate GitCommandError by raising it
    import git
    mock_repo.git.show.side_effect = git.exc.GitCommandError('show', 'error')
    mocker.patch('git.Repo', return_value=mock_repo)

    content = get_file_content_from_commit("fake/path", "some_hash", "file.txt")

    assert content == ""
