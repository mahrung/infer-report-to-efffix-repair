import os

from algorithm.projects.registry import get_project_config

# Directory paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
GENERATED_CONFIGS_DIR = os.path.join(BASE_DIR, "generated_configs")
INPUT_DIR = os.path.join(BASE_DIR, "algorithm", "input")
CONTAINER_BASE = "/opt/effFix-benchmark"


def generate_configs_from_report(project, src_dir=None):
    """Generate configs from input report.txt file.

    Args:
        project: Project name (e.g., 'lxc')
        src_dir: Optional path to source directory for procedure name extraction

    Returns:
        True if configs were generated, False otherwise
    """
    report_path = os.path.join(INPUT_DIR, project, "report.txt")

    if not os.path.exists(report_path):
        print(f"No report.txt found at {report_path}")
        return False

    # Get project config for build commands
    project_config = get_project_config(project)
    if not project_config:
        print(f"Warning: No project config found for {project}, using defaults")

    print(f"\n--- Generating Configs from {report_path} ---")

    # Import and run report_to_config
    from algorithm.report_to_config import parse_report, filter_supported_bugs, generate_tag_id, create_config_content, find_procedure_name

    # Parse report
    bugs = parse_report(report_path)
    print(f"Found {len(bugs)} total bugs in report")

    # Filter to NULLPTR_DEREFERENCE
    bugs = filter_supported_bugs(bugs, "NULLPTR_DEREFERENCE")
    print(f"After filtering for NULLPTR_DEREFERENCE: {len(bugs)} bugs")

    if not bugs:
        print("No bugs to process")
        return False

    # Generate configs
    output_dir = os.path.join(GENERATED_CONFIGS_DIR, project)
    os.makedirs(output_dir, exist_ok=True)

    # Use provided src_dir or try to find one
    if not src_dir:
        possible_src_paths = [
            os.path.join(output_dir, "_source"),
            os.path.join(BASE_DIR, "src", project),
        ]
        for path in possible_src_paths:
            if os.path.exists(path):
                src_dir = path
                break

    # Get build commands from project config or use defaults
    config_cmd = project_config.config_cmd if project_config else "./autogen.sh && ./configure"
    build_cmd = project_config.build_cmd if project_config else "make -j4"
    build_cmd_repair = project_config.build_cmd_repair if project_config else "make -j4"
    clean_cmd = project_config.clean_cmd if project_config else "make clean || true"
    pulse_args = project_config.pulse_args if project_config else ""

    bug_counts = {}
    for bug in bugs:
        bug_type = bug['bug_type_id']
        bug_counts[bug_type] = bug_counts.get(bug_type, 0) + 1
        index = bug_counts[bug_type]

        tag_id = generate_tag_id(bug_type, index, project)

        # Try to find procedure name
        if src_dir and bug['procedure'] == 'unknown':
            source_file = os.path.join(src_dir, bug['file'])
            procedure = find_procedure_name(source_file, bug['line'])
            bug['procedure'] = procedure

        # Create config content
        config_content = create_config_content(
            bug=bug,
            tag_id=tag_id,
            subject=project,
            container_base=CONTAINER_BASE,
            config_cmd=config_cmd,
            build_cmd=build_cmd,
            build_cmd_repair=build_cmd_repair,
            clean_cmd=clean_cmd,
            pulse_args=pulse_args,
        )

        # Create directories
        case_dir = os.path.join(output_dir, tag_id)
        efffix_dir = os.path.join(case_dir, "EffFix")
        os.makedirs(efffix_dir, exist_ok=True)
        os.makedirs(os.path.join(case_dir, "pre"), exist_ok=True)
        os.makedirs(os.path.join(case_dir, "src"), exist_ok=True)

        # Write config
        config_path = os.path.join(efffix_dir, "repair.conf")
        with open(config_path, 'w') as f:
            f.write(config_content)

        print(f"  Created: {tag_id}")

    print(f"\nGenerated {len(bugs)} config(s) in {output_dir}")
    return True
