import subprocess
import os

# Docker image for effFix
EFFFIX_IMAGE = "efffix-experiments:latest"
CONTAINER_BASE = "/opt/effFix-benchmark"

# Directory paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
GENERATED_CONFIGS_DIR = os.path.join(BASE_DIR, "generated_configs")


def start_container_with_volume(project):
    """Start a new container with volume mount for generated configs."""
    local_path = os.path.join(GENERATED_CONFIGS_DIR, project)
    container_path = f"{CONTAINER_BASE}/{project}"

    if not os.path.exists(local_path):
        print(f"Error: Generated configs not found at {local_path}")
        return None

    container_name = f"efffix-{project}"

    # Stop and remove existing container with same name
    subprocess.run(["docker", "rm", "-f", container_name],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"\n--- Starting Container ---")
    print(f"  Local:     {local_path}")
    print(f"  Container: {container_path}")

    result = subprocess.run([
        "docker", "run", "-d",
        "--name", container_name,
        "--entrypoint", "",
        "-v", f"{local_path}:{container_path}",
        EFFFIX_IMAGE,
        "tail", "-f", "/dev/null"
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error starting container: {result.stderr}")
        return None

    container_id = result.stdout.strip()
    print(f"  Started: {container_name} ({container_id[:12]})")

    return {'id': container_id, 'name': container_name}
