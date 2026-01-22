from concurrent.futures import ThreadPoolExecutor, as_completed
from algorithm.utils.exec_in_container import ContainerSession
from algorithm.components.run_case import run_case

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def run_projects_parallel(container_id, projects, max_workers=4):
    """Run multiple projects in parallel.

    Args:
        container_id: Docker container ID
        projects: Dict of {project_name: [case_names]}
        max_workers: Max parallel workers (default 4)
    """
    # Flatten all cases into (project, case) tuples
    all_cases = []
    for project_name, cases in projects.items():
        for case_name in cases:
            all_cases.append((project_name, case_name))

    print(f"\nRunning {len(all_cases)} cases across {len(projects)} projects")
    print(f"Max parallel workers: {max_workers}")
    print("=" * 60)

    results = {"success": [], "failed": []}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all cases
        futures = {}
        for project_name, case_name in all_cases:
            # Each worker gets its own session
            session = ContainerSession(container_id)
            future = executor.submit(run_case, session, project_name, case_name)
            futures[future] = (project_name, case_name)

        # Collect results as they complete
        for future in as_completed(futures):
            project_name, case_name = futures[future]
            try:
                future.result()
                results["success"].append(f"{project_name}/{case_name}")
                print(f"{GREEN}OK{RESET} {project_name}/{case_name}")
            except Exception as e:
                results["failed"].append(f"{project_name}/{case_name}")
                print(f"{RED}FAIL{RESET} {project_name}/{case_name}: {e}")

    # Summary
    print("\n" + "=" * 60)
    print(f"COMPLETED: {len(results['success'])} success, {len(results['failed'])} failed")
    if results["failed"]:
        print(f"{RED}Failed cases:{RESET}")
        for case in results["failed"]:
            print(f"  - {case}")

    return results
