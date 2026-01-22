import subprocess
import os


def setup_container_source(container_id, project):
    """Copy and extract source code archive into container.

    Args:
        container_id: Docker container ID
        project: Project name (e.g., 'openssl-1')

    Returns:
        True if successful, False otherwise
    """
    # Path to local archives
    archives_dir = "/home/vorashil/Projects/EffFix-artifact/effFix-benchmark/archives"
    archive_path = os.path.join(archives_dir, f"{project}.tar.gz")

    if not os.path.exists(archive_path):
        print(f"  Archive not found: {archive_path}")
        return False

    print(f"\n--- Setting up source code ---")
    print(f"  Archive: {archive_path}")

    # Copy archive to container
    result = subprocess.run(
        ["docker", "cp", archive_path, f"{container_id}:/tmp/{project}.tar.gz"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  Error copying archive: {result.stderr}")
        return False

    # Create src directory and extract
    data_path = f"/data/{project}"
    commands = [
        f"mkdir -p {data_path}/src",
        f"tar -xzf /tmp/{project}.tar.gz -C {data_path}/src --strip-components=1",
        f"rm /tmp/{project}.tar.gz"
    ]

    for cmd in commands:
        result = subprocess.run(
            ["docker", "exec", container_id, "bash", "-c", cmd],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  Error: {cmd}")
            print(f"  {result.stderr}")
            return False

    print(f"  Extracted to: {data_path}/src")
    return True
