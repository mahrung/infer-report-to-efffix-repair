import os
from algorithm.components.run_case import run_case
from algorithm.projects.registry import get_project_config
from algorithm.projects.base import ConfigSource

GREEN = "\033[92m"
RESET = "\033[0m"

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
GENERATED_CONFIGS_DIR = os.path.join(BASE_DIR, "generated_configs")
INPUT_DIR = os.path.join(BASE_DIR, "algorithm", "input")


def get_generated_cases(project_name):
    """Get list of cases from generated_configs directory.

    Looks for directories with EffFix/repair.conf structure.
    Skips directories starting with '_' (like _source).
    """
    project_dir = os.path.join(GENERATED_CONFIGS_DIR, project_name)
    if not os.path.exists(project_dir):
        return []

    cases = []
    for item in os.listdir(project_dir):
        if item.startswith('_'):  # Skip _source directory
            continue
        item_path = os.path.join(project_dir, item)
        if os.path.isdir(item_path):
            config_path = os.path.join(item_path, "EffFix", "repair.conf")
            if os.path.exists(config_path):
                cases.append(item)
    return sorted(cases)


def get_project_cases(project_name):
    """Get list of cases for a project based on its config_source.

    For ConfigSource.CONTAINER:
        - Returns None to indicate "discover at runtime from container"

    For ConfigSource.GENERATE:
        - Checks generated_configs directory
        - Returns empty list if no cases found (caller should validate)
    """
    project_config = get_project_config(project_name)
    if not project_config:
        return []

    if project_config.config_source == ConfigSource.CONTAINER:
        # Container-based: cases discovered at runtime
        return None

    elif project_config.config_source == ConfigSource.GENERATE:
        # Generate-based: check generated_configs directory
        return get_generated_cases(project_name)

    return []


def discover_container_cases(session, project_name, project_config):
    """Discover null-ptr cases inside the container by listing directories.

    Lists directories in /effFix-experiment/effFix-benchmark/{project}/
    that contain EffFix/repair.conf files (nilguard image format).
    Only returns null-ptr cases since that's what we're interested in.
    Case names are like: null-ptr-1-openssl-1
    """
    benchmark_path = project_config.container_benchmark_path
    project_path = f"{benchmark_path}/{project_name}"

    # List directories in project path
    result = session.exec(f"ls -1 {project_path} 2>/dev/null || echo ''", capture=True)
    if not result:
        return []

    # Filter to only null-ptr directories containing EffFix/repair.conf
    potential_cases = result.strip().split('\n')
    cases = []
    for case in potential_cases:
        if not case or case.startswith('.'):
            continue
        # Only include null-ptr cases (format: null-ptr-X-project)
        if not case.startswith('null-ptr-'):
            continue
        # Check if this directory has EffFix/repair.conf
        check_result = session.exec(
            f"test -f {project_path}/{case}/EffFix/repair.conf && echo 'yes' || echo 'no'",
            capture=True
        )
        if check_result and check_result.strip() == 'yes':
            cases.append(case)

    return sorted(cases)


def run_project(session, project_name, repair_only=False):
    """Run a project by name (e.g., 'lxc', 'openssl-1').

    Args:
        session: Container session
        project_name: Name of the project
        repair_only: If True, only run repair stage (skip pre-analysis)
    """
    print(f"\n{'='*60}")
    print(f"PROJECT: {project_name}")
    if repair_only:
        print("MODE: repair-only")
    print(f"{'='*60}")

    project_config = get_project_config(project_name)
    if not project_config:
        print(f"Error: Unknown project: {project_name}")
        return session

    cases = get_project_cases(project_name)

    # If cases is None, it means we need to discover from container
    if cases is None:
        print("Discovering cases from container...")
        cases = discover_container_cases(session, project_name, project_config)

    if not cases:
        print(f"Warning: No cases found for project: {project_name}")
        if project_config.config_source == ConfigSource.GENERATE:
            print(f"  Looking in: {os.path.join(GENERATED_CONFIGS_DIR, project_name)}")
            print(f"  Run with --generate-config to generate configs from report.txt")
        else:
            print(f"  Looking in container at: {project_config.container_benchmark_path}/{project_name}")
        return session

    print(f"Found {len(cases)} case(s)")

    for i, case in enumerate(cases, 1):
        print(f"\n[{i}/{len(cases)}] {case}")
        run_case(session, project_name, case, repair_only=repair_only)

    print(f"\n{GREEN}COMPLETED: {project_name}{RESET}")
    return session
