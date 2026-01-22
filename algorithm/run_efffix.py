import subprocess
import os

from algorithm.components.run_project import get_project_cases, get_generated_cases
from algorithm.components.generate_configs_from_report import generate_configs_from_report
from algorithm.components.clone_project_source import clone_project_source
from algorithm.utils.container.start_container_with_volume import start_container_with_volume
from algorithm.utils.container.start_container_for_existing_project import start_container_for_existing_project
from algorithm.utils.container.stop_container import stop_container
from algorithm.projects.registry import get_project_config
from algorithm.projects.base import ConfigSource, CodeSource

# Directory paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
GENERATED_CONFIGS_DIR = os.path.join(BASE_DIR, "generated_configs")
INPUT_DIR = os.path.join(BASE_DIR, "algorithm", "input")

# Container paths
CONTAINER_BENCHMARK = "/opt/effFix-benchmark"
CONTAINER_ARCHIVES = f"{CONTAINER_BENCHMARK}/archives"


def copy_source_from_container(container_id, project):
    """Copy source code from container archive to each case's src directory.

    Extracts from /opt/effFix-benchmark/archives/<project>.tar.gz
    to each case's src/ directory in the mounted volume.

    Args:
        container_id: Docker container ID
        project: Project name (e.g., 'x264')

    Returns:
        True if successful, False otherwise
    """
    cases = get_generated_cases(project)
    if not cases:
        print(f"No cases found for {project}")
        return False

    print(f"\n--- Copying source from container to {len(cases)} case(s) ---")

    archive_path = f"{CONTAINER_ARCHIVES}/{project}.tar.gz"

    for case_name in cases:
        case_src = f"{CONTAINER_BENCHMARK}/{project}/{case_name}/src"

        # Extract archive to case src directory
        cmd = f"mkdir -p {case_src} && tar -xzf {archive_path} -C {case_src} --strip-components=1"
        result = subprocess.run(
            ["docker", "exec", container_id, "bash", "-c", cmd],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            print(f"  Error extracting to {case_name}: {result.stderr}")
            return False

        print(f"  Extracted: {case_name}/src")

    return True


def validate_project_configs(project, generate_config):
    """Validate that project can run with current configuration.

    Args:
        project: Project name
        generate_config: Whether --generate-config flag was passed

    Returns:
        (is_valid, error_message) tuple
    """
    project_config = get_project_config(project)
    if not project_config:
        return False, f"Unknown project: {project}"

    if project_config.config_source == ConfigSource.GENERATE:
        # Check if generated configs exist
        cases = get_generated_cases(project)
        null_ptr_cases = [c for c in cases if c.startswith('null-ptr-')]

        if not null_ptr_cases and not generate_config:
            report_path = os.path.join(INPUT_DIR, project, "report.txt")
            has_report = os.path.exists(report_path)

            error_msg = f"""
Error: No null-ptr-* configs found for project '{project}'.

The project is configured with config_source=GENERATE, which means
configs must be generated from a report.txt file.

Generated configs directory: {os.path.join(GENERATED_CONFIGS_DIR, project)}
"""
            if has_report:
                error_msg += f"""
A report.txt file exists at: {report_path}

To generate configs, run with --generate-config flag:
  python main.py --start-new {project} --generate-config
"""
            else:
                error_msg += f"""
No report.txt file found at: {report_path}

Please create a report.txt file first, then run with --generate-config.
"""
            return False, error_msg

    return True, None


def copy_source_to_cases(project):
    """Copy source code from _source to each case's src directory.

    Args:
        project: Project name (e.g., 'lxc')

    Returns:
        True if source was copied successfully, False otherwise
    """
    project_dir = os.path.join(GENERATED_CONFIGS_DIR, project)
    shared_src_dir = os.path.join(project_dir, "_source")

    if not os.path.exists(shared_src_dir):
        print(f"Error: Source not found at {shared_src_dir}")
        return False

    cases = get_project_cases(project)
    if not cases:
        print(f"Warning: No cases found for {project}")
        return True

    print(f"\n--- Copying source to {len(cases)} case(s) ---")

    for case_name in cases:
        case_src_dir = os.path.join(project_dir, case_name, "src")

        # Check if already has source files
        if os.path.exists(case_src_dir) and os.listdir(case_src_dir):
            continue

        # Copy source (use cp -a to preserve structure)
        os.makedirs(case_src_dir, exist_ok=True)
        result = subprocess.run(
            ["cp", "-a", f"{shared_src_dir}/.", case_src_dir],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  Error copying to {case_name}: {result.stderr}")
        else:
            print(f"  Copied: {case_name}/src")

    return True


def run_effix(container, project=None, case=None, start_new=False,
               repair_only=False, generate_config=False):
    """Run effix operations on the given container.

    Args:
        container: Container dict with 'id' and 'name'. Can be None if start_new=True.
        project: Optional project name (e.g., 'lxc').
        case: Optional case name (e.g., 'null-ptr-1-lxc').
        start_new: If True, start a new container with volume mount.
        repair_only: If True, only run repair stage (skip pre-analysis).
        generate_config: If True, generate configs from report.txt before running.
    """
    from algorithm.utils.exec_in_container import ContainerSession
    from algorithm.components.run_project import run_project
    from algorithm.components.run_case import run_case

    own_container = False

    if start_new and project:
        project_config = get_project_config(project)

        if not project_config:
            print(f"Error: Unknown project: {project}")
            return

        # Validate configs for GENERATE projects
        if project_config.config_source == ConfigSource.GENERATE:
            is_valid, error_msg = validate_project_configs(project, generate_config)
            if not is_valid:
                print(error_msg)
                return

        # Handle source code based on code_source
        if project_config.code_source == CodeSource.CONTAINER:
            # Source code is in container
            print(f"\n--- Project {project} uses container source ---")

            # Generate configs from report.txt if requested (for GENERATE config_source)
            if generate_config and project_config.config_source == ConfigSource.GENERATE:
                report_path = os.path.join(INPUT_DIR, project, "report.txt")
                if os.path.exists(report_path):
                    generate_configs_from_report(project)
                else:
                    print(f"Warning: No report.txt found at {report_path}")

            # For GENERATE + CONTAINER: use volume mount and copy source from container
            if project_config.config_source == ConfigSource.GENERATE:
                # Start container with volume mount for generated configs
                container = start_container_with_volume(project)
                if not container:
                    return
                own_container = True

                # Copy source from container to mounted volume
                if not copy_source_from_container(container['id'], project):
                    print("Warning: Failed to copy source from container")
            else:
                # For CONTAINER + CONTAINER: use nilguard image with pre-configured cases
                container = start_container_for_existing_project(project)
                if not container:
                    return
                own_container = True

        elif project_config.code_source == CodeSource.GIT:
            # Clone source from git, generate configs, copy to cases
            # Step 1: Clone source code first (needed for procedure name extraction)
            src_dir = clone_project_source(project)
            if not src_dir:
                print("Error: Failed to clone project source")
                return

            # Step 2: Generate configs from report.txt if requested
            if generate_config:
                report_path = os.path.join(INPUT_DIR, project, "report.txt")
                if os.path.exists(report_path):
                    generate_configs_from_report(project, src_dir=src_dir)
                else:
                    print(f"Warning: No report.txt found at {report_path}")

            # Step 3: Copy source code to each case
            if not copy_source_to_cases(project):
                print("Error: Failed to copy source to cases")
                return

            # Step 4: Start container with volume mount
            container = start_container_with_volume(project)
            if not container:
                return
            own_container = True

    if not container:
        print("No container available")
        return

    print(f"\nContainer: {container['name']}")
    session = ContainerSession(container['id'])

    try:
        # Run specific case
        if project and case:
            print(f"Running single case: {project}/{case}")
            run_case(session, project, case, repair_only=repair_only)
            return

        # Run specific project (all its cases)
        if project:
            print(f"Running project: {project}")
            run_project(session, project, repair_only=repair_only)
            return

        # Run all projects from generated_configs
        print("Running all projects...")
        projects = [d for d in os.listdir(GENERATED_CONFIGS_DIR)
                    if os.path.isdir(os.path.join(GENERATED_CONFIGS_DIR, d))]
        for project_name in sorted(projects):
            if get_project_cases(project_name):  # Only run if has cases
                run_project(session, project_name, repair_only=repair_only)

    finally:
        if own_container:
            stop_container(container)
