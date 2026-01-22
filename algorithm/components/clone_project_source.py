import subprocess
import os

from algorithm.projects.registry import get_project_config

# Directory paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
GENERATED_CONFIGS_DIR = os.path.join(BASE_DIR, "generated_configs")


def clone_project_source(project):
    """Clone source code for a project (without copying to cases).

    Args:
        project: Project name (e.g., 'lxc')

    Returns:
        Path to cloned source directory, or None on failure
    """
    project_config = get_project_config(project)
    if not project_config:
        print(f"Error: No project config found for {project}")
        return None

    project_dir = os.path.join(GENERATED_CONFIGS_DIR, project)
    os.makedirs(project_dir, exist_ok=True)

    shared_src_dir = os.path.join(project_dir, "_source")

    if not os.path.exists(shared_src_dir):
        print(f"\n--- Cloning {project} source ---")
        print(f"  Repo: {project_config.git_repo}")
        print(f"  Commit: {project_config.git_commit}")

        result = subprocess.run(
            ["git", "clone", project_config.git_repo, shared_src_dir],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Error cloning: {result.stderr}")
            return None

        result = subprocess.run(
            ["git", "-C", shared_src_dir, "checkout", project_config.git_commit],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Error checking out commit: {result.stderr}")
            return None

        print(f"  Cloned to: {shared_src_dir}")
    else:
        print(f"\n--- Using existing source: {shared_src_dir} ---")

    return shared_src_dir
