import subprocess
import logging

logger = logging.getLogger(__name__)


def get_running_containers():
    """Get list of running Docker containers."""
    logger.info("Fetching running Docker containers...")
    result = subprocess.run(
        ["docker", "ps", "--format", "{{.ID}}\t{{.Names}}\t{{.Image}}"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logger.error(f"Failed to get containers: {result.stderr}")
        return []

    containers = []
    for line in result.stdout.strip().split('\n'):
        if line:
            parts = line.split('\t')
            if len(parts) >= 3:
                containers.append({
                    'id': parts[0],
                    'name': parts[1],
                    'image': parts[2]
                })

    logger.info(f"Found {len(containers)} running container(s)")
    return containers
