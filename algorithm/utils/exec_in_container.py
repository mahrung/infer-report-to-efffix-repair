import subprocess

# Simple colors: green for success, red for error, gray for output
GREEN = "\033[92m"
RED = "\033[91m"
GRAY = "\033[90m"
RESET = "\033[0m"


class ContainerSession:
    """A stateful session for executing commands in a Docker container."""

    def __init__(self, container_id, workdir="/effFix-experiment/effFix-benchmark"):
        self.container_id = container_id
        self.workdir = workdir

    def exec(self, command, stream=False, capture=False):
        """Execute a command in the container with current state.

        Args:
            command: The command to execute
            stream: If True, stream output to console in real-time
            capture: If True, suppress printing output (just return it)
        """
        full_command = f"cd {self.workdir} && {command}"

        if stream:
            return self._exec_streaming(full_command)

        result = subprocess.run(
            ["docker", "exec", self.container_id, "bash", "-c", full_command],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            if not capture:
                print(f"{RED}ERROR: {result.stderr}{RESET}")
            return None

        if result.stdout.strip() and not capture:
            print(f"{GRAY}{result.stdout}{RESET}")
        return result.stdout

    def _exec_streaming(self, full_command):
        """Execute command and stream output in real-time."""
        process = subprocess.Popen(
            ["docker", "exec", self.container_id, "bash", "-c", full_command],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1  # Line buffered
        )

        output_lines = []
        for line in process.stdout:
            output_lines.append(line)
            # Print each line immediately
            print(line, end="", flush=True)

        process.wait()

        if process.returncode != 0:
            print(f"{RED}Command exited with code {process.returncode}{RESET}")
            return None

        return "".join(output_lines)

    def cd(self, path):
        """Change the working directory for subsequent commands."""
        if path.startswith("/"):
            self.workdir = path
        else:
            result = subprocess.run(
                ["docker", "exec", self.container_id, "bash", "-c",
                 f"cd {self.workdir} && cd {path} && pwd"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.workdir = result.stdout.strip()
        return self.workdir


def exec_in_container(container_id, command):
    """Execute a command inside a Docker container (stateless)."""
    result = subprocess.run(
        ["docker", "exec", container_id, "sh", "-c", command],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"{RED}ERROR: {result.stderr}{RESET}")
        return None

    if result.stdout.strip():
        print(f"{GRAY}{result.stdout}{RESET}")
    return result.stdout
