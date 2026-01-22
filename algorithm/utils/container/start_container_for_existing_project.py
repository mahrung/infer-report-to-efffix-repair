import subprocess

# Docker image for container-based projects (has pre-configured benchmarks)
NILGUARD_IMAGE = "nilguard-experiments:latest"


def start_container_for_existing_project(project):
    """Start a new container for a project that uses container source.

    Uses nilguard-experiments image which has pre-configured benchmarks
    at /effFix-experiment/effFix-benchmark/ with EffFix/repair.conf files.
    """
    container_name = f"efffix-{project}"

    # Stop and remove existing container with same name
    subprocess.run(["docker", "rm", "-f", container_name],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"\n--- Starting Container (container-based project) ---")
    print(f"  Project: {project}")
    print(f"  Image: {NILGUARD_IMAGE}")

    result = subprocess.run([
        "docker", "run", "-d",
        "--name", container_name,
        "--entrypoint", "",
        NILGUARD_IMAGE,
        "tail", "-f", "/dev/null"
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error starting container: {result.stderr}")
        return None

    container_id = result.stdout.strip()
    print(f"  Started: {container_name} ({container_id[:12]})")

    return {'id': container_id, 'name': container_name}
