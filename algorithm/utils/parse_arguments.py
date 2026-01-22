import argparse


def parse_arguments():
    """Parse command line arguments for effFix repair tool."""
    parser = argparse.ArgumentParser(description="Run effFix repairs on Docker containers")
    parser.add_argument("target", nargs="?", help="Project/case to run (e.g., 'lxc' or 'lxc/null-ptr-1-lxc')")
    parser.add_argument("--start-new", "-s", action="store_true",
                        help="Start a new container with volume mount for generated configs")
    parser.add_argument("--repair-only", "-r", action="store_true",
                        help="Only run repair stage (skip pre-analysis and config regeneration)")
    parser.add_argument("--generate-config", "-g", action="store_true",
                        help="Generate config from report.txt file")
    args = parser.parse_args()
    print(f"args.target: {args.target}")
    print(f"args.start_new: {args.start_new}")
    print(f"args.repair_only: {args.repair_only}")
    print(f"args.generate_config: {args.generate_config}")
    return args
