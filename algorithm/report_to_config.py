#!/usr/bin/env python3
"""
Convert Infer text report to EffFix config files.

Parses Infer's text report format and generates repair.conf files
for NULLPTR_DEREFERENCE bugs that can be used with effFix.

Usage:
    python report_to_config.py --report input/lxc/report.txt --subject lxc \
        --config-cmd "./autogen.sh && ./configure" --build-cmd "make -j32"
"""

import argparse
import os
import re
from pathlib import Path


# Bug types supported by effFix
SUPPORTED_BUG_TYPES = {
    "NULLPTR_DEREFERENCE": "null-ptr",
    "MEMORY_LEAK_C": "memory-leak",
    "USE_AFTER_FREE": "use-after-free",
}


def parse_report(report_path: str) -> list[dict]:
    """
    Parse Infer text report and extract bug information.

    Format:
        #<index>
        <file>:<line>: error: <Bug Type>(<BUG_TYPE_ID>)
          <description>
          <line_num>. <code>
          ...
    """
    bugs = []
    current_bug = None

    # Regex patterns
    bug_start_pattern = re.compile(r'^#(\d+)$')
    bug_info_pattern = re.compile(r'^(.+):(\d+): error: (.+)\((\w+)\)$')
    code_line_pattern = re.compile(r'^\s*(\d+)\.\s*(.*)$')

    with open(report_path, 'r') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        # Check for bug start marker (#0, #1, etc.)
        match = bug_start_pattern.match(line)
        if match:
            # Save previous bug if exists
            if current_bug:
                bugs.append(current_bug)

            current_bug = {
                'index': int(match.group(1)),
                'file': None,
                'line': None,
                'bug_type': None,
                'bug_type_id': None,
                'description': None,
                'code_lines': [],
                'procedure': 'unknown',  # Will try to extract later
            }
            i += 1
            continue

        # Check for bug info line (file:line: error: Type(TYPE_ID))
        if current_bug and current_bug['file'] is None:
            match = bug_info_pattern.match(line)
            if match:
                current_bug['file'] = match.group(1)
                current_bug['line'] = int(match.group(2))
                current_bug['bug_type'] = match.group(3)
                current_bug['bug_type_id'] = match.group(4)
                i += 1
                continue

        # Check for description (indented line after bug info)
        if current_bug and current_bug['file'] and current_bug['description'] is None:
            if line.startswith('  ') and not code_line_pattern.match(line):
                current_bug['description'] = line.strip()
                i += 1
                continue

        # Check for code lines (e.g., "  123. 	code here")
        if current_bug:
            match = code_line_pattern.match(line)
            if match:
                current_bug['code_lines'].append({
                    'line_num': int(match.group(1)),
                    'code': match.group(2),
                })

        i += 1

    # Don't forget the last bug
    if current_bug:
        bugs.append(current_bug)

    return bugs


def filter_supported_bugs(bugs: list[dict], bug_type_filter: str = None) -> list[dict]:
    """Filter bugs to only supported types."""
    filtered = []
    for bug in bugs:
        if bug['bug_type_id'] in SUPPORTED_BUG_TYPES:
            if bug_type_filter is None or bug['bug_type_id'] == bug_type_filter:
                filtered.append(bug)
    return filtered


def find_procedure_name(source_file: str, bug_line: int) -> str:
    """Find the function name containing the given line number.

    Parses C source code to find function definitions and returns
    the name of the function that contains the bug line.
    """
    if not os.path.exists(source_file):
        return "unknown"

    try:
        with open(source_file, 'r', errors='ignore') as f:
            lines = f.readlines()
    except Exception:
        return "unknown"

    # Pattern to match C function definitions
    # Matches: return_type function_name(params) {
    # Also handles multi-line definitions
    func_pattern = re.compile(
        r'^[a-zA-Z_][a-zA-Z0-9_\s\*]*\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{?\s*$'
    )

    current_function = "unknown"
    brace_depth = 0
    in_function = False

    for i, line in enumerate(lines, 1):
        # Count braces to track scope
        brace_depth += line.count('{') - line.count('}')

        # Check for function definition
        match = func_pattern.match(line.strip())
        if match and brace_depth <= 1:
            current_function = match.group(1)
            in_function = True

        # Also try to match function with opening brace on next line
        if not match and '{' in line and brace_depth == 1:
            # Look back for function signature
            for j in range(max(0, i-5), i):
                prev_line = lines[j].strip()
                # Match function name with params but no brace
                sig_match = re.match(
                    r'^[a-zA-Z_][a-zA-Z0-9_\s\*]*\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*$',
                    prev_line
                )
                if sig_match:
                    current_function = sig_match.group(1)
                    in_function = True
                    break

        # If we've reached the bug line, return current function
        if i == bug_line:
            return current_function

        # Reset when exiting function scope
        if in_function and brace_depth == 0:
            in_function = False

    return current_function


def generate_tag_id(bug_type_id: str, index: int, subject: str) -> str:
    """Generate tag ID like 'null-ptr-1-lxc'."""
    prefix = SUPPORTED_BUG_TYPES.get(bug_type_id, 'bug')
    return f"{prefix}-{index}-{subject}"


def create_config_content(
    bug: dict,
    tag_id: str,
    subject: str,
    container_base: str,
    config_cmd: str,
    build_cmd: str,
    build_cmd_repair: str,
    clean_cmd: str,
    pulse_args: str,
) -> str:
    """Generate repair.conf content."""
    case_path = f"{container_base}/{subject}/{tag_id}"

    lines = []
    if pulse_args:
        lines.append(f"pulse_extra_command:{pulse_args}")
    lines.extend([
        f"tag_id:{tag_id}",
        f"config_command:{config_cmd}",
        f"build_command:{build_cmd}",
        f"build_command_repair:{build_cmd_repair}",
        f"clean_command:{clean_cmd}",
        f"src_dir:{case_path}/src",
        f"bug_type:{bug['bug_type_id']}",
        f"bug_file:{bug['file']}",
        f"bug_procedure:{bug['procedure']}",
        f"bug_start_line:{bug['line']}",
        f"bug_end_line:{bug['line']}",  # Same as start for text reports
        f"runtime_dir_pre:{case_path}/pre",
        f"runtime_dir_repair:{case_path}/repair",
    ])

    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(
        description="Convert Infer text report to EffFix config files"
    )
    parser.add_argument("--report", required=True, help="Path to Infer report.txt")
    parser.add_argument("--subject", required=True, help="Project name (e.g., lxc)")
    parser.add_argument("--config-cmd", default="true", help="Configuration command (default: 'true' no-op)")
    parser.add_argument("--build-cmd", required=True, help="Build command")
    parser.add_argument("--build-cmd-repair", default="", help="Build command for repair (defaults to build-cmd)")
    parser.add_argument("--clean-cmd", default="make clean", help="Clean command")
    parser.add_argument("--pulse-args", default="", help="Additional Pulse arguments")
    parser.add_argument(
        "--output-dir",
        default="./generated_configs",
        help="Output directory for generated configs"
    )
    parser.add_argument(
        "--container-base",
        default="/opt/effFix-benchmark",
        help="Base path in container"
    )
    parser.add_argument(
        "--bug-type",
        choices=list(SUPPORTED_BUG_TYPES.keys()),
        default="NULLPTR_DEREFERENCE",
        help="Filter by bug type (default: NULLPTR_DEREFERENCE)"
    )
    parser.add_argument("--list-only", action="store_true", help="Only list bugs")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created")
    parser.add_argument(
        "--src-dir",
        default="",
        help="Path to source directory (to extract procedure names from source files)"
    )

    args = parser.parse_args()

    # Parse report
    if not os.path.exists(args.report):
        print(f"Error: Report file not found: {args.report}")
        return 1

    bugs = parse_report(args.report)
    print(f"Found {len(bugs)} total bugs in report")

    # Filter to supported types
    bugs = filter_supported_bugs(bugs, args.bug_type)
    print(f"After filtering for {args.bug_type}: {len(bugs)} bugs")

    if not bugs:
        print("No bugs to process")
        return 0

    # List-only mode
    if args.list_only:
        print("\nBugs found:")
        for i, bug in enumerate(bugs, 1):
            print(f"  {i}. [{bug['bug_type_id']}] {bug['file']}:{bug['line']}")
            if bug['description']:
                print(f"      {bug['description'][:80]}...")
        return 0

    # Generate configs
    build_cmd_repair = args.build_cmd_repair or args.build_cmd
    output_dir = Path(args.output_dir)

    bug_counts = {}
    for bug in bugs:
        # Count bugs per type for unique naming
        bug_type = bug['bug_type_id']
        bug_counts[bug_type] = bug_counts.get(bug_type, 0) + 1
        index = bug_counts[bug_type]

        tag_id = generate_tag_id(bug_type, index, args.subject)

        # Try to find procedure name from source file
        if args.src_dir and bug['procedure'] == 'unknown':
            source_file = os.path.join(args.src_dir, bug['file'])
            procedure = find_procedure_name(source_file, bug['line'])
            bug['procedure'] = procedure
            if procedure != 'unknown':
                print(f"  Found procedure: {bug['file']}:{bug['line']} -> {procedure}")

        # Generate config content
        config_content = create_config_content(
            bug=bug,
            tag_id=tag_id,
            subject=args.subject,
            container_base=args.container_base,
            config_cmd=args.config_cmd,
            build_cmd=args.build_cmd,
            build_cmd_repair=build_cmd_repair,
            clean_cmd=args.clean_cmd,
            pulse_args=args.pulse_args,
        )

        # Output paths
        case_dir = output_dir / args.subject / tag_id
        efffix_dir = case_dir / "EffFix"
        config_path = efffix_dir / "repair.conf"

        if args.dry_run:
            print(f"\n{'='*60}")
            print(f"Would create: {config_path}")
            print(f"{'='*60}")
            print(config_content)
        else:
            # Create directories
            efffix_dir.mkdir(parents=True, exist_ok=True)
            (case_dir / "pre").mkdir(exist_ok=True)
            (case_dir / "src").mkdir(exist_ok=True)

            # Write config
            with open(config_path, 'w') as f:
                f.write(config_content)

            print(f"Created: {config_path}")

    if not args.dry_run:
        print(f"\nGenerated {len(bugs)} config(s) in {output_dir / args.subject}")
        print(f"\nTo copy to container:")
        print(f"  docker cp {output_dir / args.subject}/. <container>:{args.container_base}/{args.subject}/")

    return 0


if __name__ == "__main__":
    exit(main())
