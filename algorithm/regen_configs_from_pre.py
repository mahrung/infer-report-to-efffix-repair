#!/usr/bin/env python3
"""
Regenerate EffFix configs from pre-analysis Infer output.

After running `effFix --stage pre`, this script reads the infer-out-whole/report.json
and creates proper configs for each bug that effFix can repair.

Usage:
    python regen_configs_from_pre.py --project lxc --case null-ptr-1-lxc
    python regen_configs_from_pre.py --project lxc  # regenerate all cases
"""

import argparse
import json
import os
from pathlib import Path


# Bug types supported by effFix
SUPPORTED_BUG_TYPES = {
    "NULLPTR_DEREFERENCE": "null-ptr",
    "MEMORY_LEAK_C": "memory-leak",
    "USE_AFTER_FREE": "use-after-free",
}

GENERATED_CONFIGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_configs")


def load_infer_report(case_path: str) -> list[dict]:
    """Load report.json from pre-analysis output."""
    report_path = os.path.join(case_path, "pre", "infer-out-whole", "report.json")
    if not os.path.exists(report_path):
        print(f"Report not found: {report_path}")
        return []

    with open(report_path, 'r') as f:
        return json.load(f)


def filter_bugs(bugs: list[dict], bug_type: str = None) -> list[dict]:
    """Filter bugs to supported types."""
    filtered = []
    for bug in bugs:
        if bug['bug_type'] in SUPPORTED_BUG_TYPES:
            if bug_type is None or bug['bug_type'] == bug_type:
                filtered.append(bug)
    return filtered


def extract_start_end_lines(bug: dict) -> tuple[int, int]:
    """Extract start and end lines from bug_trace like effFix does."""
    trace = bug.get('bug_trace', [])
    if len(trace) > 0:
        start_line = trace[0].get('line_number', bug['line'])
        end_line = trace[-1].get('line_number', bug['line'])
        return start_line, end_line
    return bug['line'], bug['line']


def create_config_content(
    bug: dict,
    tag_id: str,
    container_base: str,
    config_cmd: str,
    build_cmd: str,
    clean_cmd: str,
) -> str:
    """Generate repair.conf content from Infer bug report."""
    case_path = f"{container_base}/{tag_id}"

    # Extract start/end lines from bug_trace (how effFix does it)
    start_line, end_line = extract_start_end_lines(bug)

    lines = [
        f"tag_id:{tag_id}",
        f"config_command:{config_cmd}",
        f"build_command:{build_cmd}",
        f"build_command_repair:{build_cmd}",
        f"clean_command:{clean_cmd}",
        f"src_dir:{case_path}/src",
        f"bug_type:{bug['bug_type']}",
        f"bug_file:{bug['file']}",
        f"bug_procedure:{bug['procedure']}",
        f"bug_start_line:{start_line}",
        f"bug_end_line:{end_line}",
        f"runtime_dir_pre:{case_path}/pre",
        f"runtime_dir_repair:{case_path}/repair",
    ]

    return '\n'.join(lines) + '\n'


def regenerate_case(project: str, case_name: str, bug_type: str = "NULLPTR_DEREFERENCE"):
    """Regenerate config for a single case based on pre-analysis results."""
    case_path = os.path.join(GENERATED_CONFIGS_DIR, project, case_name)

    if not os.path.exists(case_path):
        print(f"Case not found: {case_path}")
        return False

    # Load Infer report from pre-analysis
    bugs = load_infer_report(case_path)
    if not bugs:
        print(f"No Infer report found for {case_name}")
        return False

    # Filter to supported bug type
    bugs = filter_bugs(bugs, bug_type)
    if not bugs:
        print(f"No {bug_type} bugs found in {case_name}")
        return False

    print(f"\nFound {len(bugs)} {bug_type} bug(s) in {case_name}:")
    for i, bug in enumerate(bugs, 1):
        start, end = extract_start_end_lines(bug)
        print(f"  {i}. {bug['file']}:{bug['line']} in {bug['procedure']} (trace: {start}-{end})")

    # Read existing config to get build commands
    config_path = os.path.join(case_path, "EffFix", "repair.conf")
    config_cmd = "true"
    build_cmd = "make -j4"
    clean_cmd = "make clean || true"

    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            for line in f:
                if line.startswith("config_command:"):
                    config_cmd = line.split(":", 1)[1].strip()
                elif line.startswith("build_command:"):
                    build_cmd = line.split(":", 1)[1].strip()
                elif line.startswith("clean_command:"):
                    clean_cmd = line.split(":", 1)[1].strip()

    # Use first bug to update the config
    bug = bugs[0]
    container_base = f"/opt/effFix-benchmark/{project}"

    config_content = create_config_content(
        bug=bug,
        tag_id=case_name,
        container_base=container_base,
        config_cmd=config_cmd,
        build_cmd=build_cmd,
        clean_cmd=clean_cmd,
    )

    # Backup old config
    if os.path.exists(config_path):
        backup_path = config_path + ".bak"
        os.rename(config_path, backup_path)
        print(f"Backed up: {backup_path}")

    # Write new config
    with open(config_path, 'w') as f:
        f.write(config_content)
    print(f"Updated: {config_path}")

    return True


def regenerate_project(project: str, bug_type: str = "NULLPTR_DEREFERENCE"):
    """Regenerate configs for all cases in a project."""
    project_path = os.path.join(GENERATED_CONFIGS_DIR, project)

    if not os.path.exists(project_path):
        print(f"Project not found: {project_path}")
        return

    cases = [d for d in os.listdir(project_path)
             if os.path.isdir(os.path.join(project_path, d))]

    print(f"Found {len(cases)} cases in {project}")

    success = 0
    for case_name in sorted(cases):
        if regenerate_case(project, case_name, bug_type):
            success += 1

    print(f"\nRegenerated {success}/{len(cases)} cases")


def main():
    parser = argparse.ArgumentParser(
        description="Regenerate EffFix configs from pre-analysis Infer output"
    )
    parser.add_argument("--project", required=True, help="Project name (e.g., lxc)")
    parser.add_argument("--case", help="Case name (e.g., null-ptr-1-lxc)")
    parser.add_argument(
        "--bug-type",
        choices=list(SUPPORTED_BUG_TYPES.keys()),
        default="NULLPTR_DEREFERENCE",
        help="Filter by bug type"
    )

    args = parser.parse_args()

    if args.case:
        regenerate_case(args.project, args.case, args.bug_type)
    else:
        regenerate_project(args.project, args.bug_type)


if __name__ == "__main__":
    main()
