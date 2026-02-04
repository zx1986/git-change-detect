# main.py
import click
import git
import re
from ruamel.yaml import YAML
from git_change_detect.core import get_file_content_from_commit, parse_yaml_content, deep_diff

@click.command()
@click.option('--repo-path', default='.', help='Path to the git repository.')
@click.option('--base-ref', required=True, help='The base git ref (e.g., origin/main).')
@click.option('--head-ref', required=True, help='The head git ref (e.g., HEAD).')
@click.option('--pattern', required=True, help='Regex pattern to filter file paths.')
def main(repo_path, base_ref, head_ref, pattern):
    """
    Detects changes in YAML files between two git refs.
    """
    repo = git.Repo(repo_path)
    
    # Get the diff between the two commits with status
    diff_index = repo.git.diff(f'{base_ref}...{head_ref}', name_status=True)
    
    # Compile the regex pattern
    try:
        path_pattern = re.compile(pattern)
    except re.error as e:
        click.echo(f"Error: Invalid regex pattern: {e}", err=True)
        return

    detected_changes = []

    for diff_line in diff_index.splitlines():
        status, file_path = diff_line.split('\t')
        
        if path_pattern.match(file_path):
            change_type = ""
            diff_details = []

            if status == 'A': # Added
                change_type = "ADD"
                new_content = get_file_content_from_commit(repo_path, head_ref, file_path)
                new_data = parse_yaml_content(new_content)
                # For ADD, we treat all keys as added
                diff_details = deep_diff({}, new_data)

            elif status == 'D': # Deleted
                change_type = "DELETE"
                # No diff details needed for DELETE as per PRD

            elif status == 'M': # Modified
                change_type = "UPDATE"
                old_content = get_file_content_from_commit(repo_path, base_ref, file_path)
                new_content = get_file_content_from_commit(repo_path, head_ref, file_path)
                old_data = parse_yaml_content(old_content)
                new_data = parse_yaml_content(new_content)
                diff_details = deep_diff(old_data, new_data)

            else: # Renamed, Copied, etc. - not handled yet
                continue

            if change_type:
                change_entry = {
                    "file_path": file_path,
                    "change_type": change_type,
                }
                if diff_details:
                    change_entry["diffs"] = diff_details
                
                detected_changes.append(change_entry)

    # Output the results as YAML
    yaml = YAML()
    output_data = {"detected_changes": detected_changes}
    yaml.dump(output_data, click.get_text_stream('stdout'))

if __name__ == '__main__':
    main()
