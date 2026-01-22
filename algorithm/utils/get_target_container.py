from get_running_containers import get_running_containers


def get_target_container(args):
    """
    Parse target argument and get container based on args.

    Returns tuple of (target_container, project, case, should_start_new, should_exit).
    If should_exit is True, caller should return early.
    """
    # Parse target argument
    project = None
    case = None
    if args.target:
        if "/" in args.target:
            project, case = args.target.split("/", 1)
        else:
            project = args.target

    # If starting new container, don't need existing containers
    if args.start_new:
        if not project:
            print("Error: --start-new requires a project name")
            print("Usage: python main.py --start-new <project>")
            return None, None, None, False, True
        return None, project, case, True, False

    # Otherwise, use existing container
    containers = get_running_containers()

    if not containers:
        # No running container - auto-start one if we have a project
        if project:
            print("No running containers found, starting one...")
            return None, project, case, True, False
        print("No running containers found")
        print("Use --start-new to start a new container with volume mount")
        return None, None, None, False, True

    target_container = containers[0]
    return target_container, project, case, False, False
