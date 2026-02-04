# core.py

# core.py

from typing import Any, Dict, List
import git
from ruamel.yaml import YAML, YAMLError
from deepdiff import DeepDiff

def deep_diff(old_dict: Dict[str, Any], new_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Compares two dictionaries using DeepDiff and formats the output.

    Args:
        old_dict: The old dictionary.
        new_dict: The new dictionary.

    Returns:
        A list of dictionaries, where each dictionary represents a change.
    """
    diffs = []
    ddiff = DeepDiff(old_dict, new_dict, ignore_order=True, view='tree')

    def get_path(item):
        # The path method on a tree item returns a list of path components.
        # We need to format it into a dot-separated string.
        path_list = item.path(output_format='list')
        return ".".join(str(p) for p in path_list)


    if 'values_changed' in ddiff:
        for item in ddiff['values_changed']:
            diffs.append({
                "action": "EDIT",
                "key_path": get_path(item),
                "value": item.t2
            })
            
    if 'dictionary_item_added' in ddiff:
        for item in ddiff['dictionary_item_added']:
            diffs.append({
                "action": "ADD",
                "key_path": get_path(item),
                "value": item.t2
            })

    if 'dictionary_item_removed' in ddiff:
        for item in ddiff['dictionary_item_removed']:
            diffs.append({
                "action": "DELETE",
                "key_path": get_path(item)
            })
            
    return diffs

def get_file_content_from_commit(repo_path: str, commit_hash: str, file_path: str) -> str:
    """
    Retrieves the content of a file from a specific git commit.

    Args:
        repo_path: The path to the git repository.
        commit_hash: The commit hash.
        file_path: The path to the file.

    Returns:
        The content of the file as a string.
    """
    try:
        repo = git.Repo(repo_path)
        content = repo.git.show(f'{commit_hash}:{file_path}')
        return content
    except git.exc.GitCommandError as e:
        # Handle cases where the file might not exist in the commit
        return ""

def parse_yaml_content(content: str) -> Dict[str, Any]:
    """
    Parses YAML content into a Python dictionary.

    Args:
        content: The YAML content as a string.

    Returns:
        A dictionary representing the YAML content.
    """
    if not content:
        return {}
    yaml = YAML(typ='safe') # Use safe_load to avoid arbitrary code execution
    try:
        data = yaml.load(content)
        if not isinstance(data, dict):
            return {}
        return data
    except YAMLError as e:
        # Handle YAML parsing errors
        return {}
