"""Base project configuration class."""

from dataclasses import dataclass
from enum import Enum


class ConfigSource(Enum):
    """Where the case configurations come from."""
    CONTAINER = "container"  # Use existing configs inside container
    GENERATE = "generate"    # Generate configs from report.txt file


class CodeSource(Enum):
    """Where the source code comes from."""
    GIT = "git"              # Clone from git_repo
    CONTAINER = "container"  # Source already exists in container


@dataclass
class ProjectConfig:
    """Configuration for a project to run effFix on."""

    # Project identification
    name: str

    # Config source: where case configs come from (REQUIRED - no default)
    config_source: ConfigSource

    # Code source: where source code comes from (REQUIRED - no default)
    code_source: CodeSource

    # Source code setup (required if code_source=GIT)
    git_repo: str = ""
    git_commit: str = ""

    # Container benchmark path (where projects live in container)
    # For CONTAINER projects: /effFix-experiment/effFix-benchmark (nilguard image)
    # For GENERATE projects: /opt/effFix-benchmark (efffix image with volume mount)
    container_benchmark_path: str = "/effFix-experiment/effFix-benchmark"

    # Build commands
    config_cmd: str = "true"
    build_cmd: str = "make -j4"
    build_cmd_repair: str = "make -j4"
    clean_cmd: str = "make clean || true"

    # Infer/effFix settings
    pulse_args: str = ""

    # Container paths (relative to container base)
    src_subdir: str = "src"  # Where source lives within case dir
