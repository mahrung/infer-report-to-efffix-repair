import subprocess


def stop_container(container):
    """Stop and remove a container."""
    subprocess.run(["docker", "rm", "-f", container['id']],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"\nStopped container: {container['name']}")
