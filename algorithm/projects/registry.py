"""Registry of all project configurations."""

from algorithm.projects.base import ProjectConfig
from algorithm.projects.lxc import LXC_CONFIG
from algorithm.projects.openssl_1 import OPENSSL_1_CONFIG
from algorithm.projects.openssl_3 import OPENSSL_3_CONFIG
from algorithm.projects.p11_kit import P11_KIT_CONFIG
from algorithm.projects.x264 import X264_CONFIG


# Registry mapping project names to their configs
PROJECT_CONFIGS: dict[str, ProjectConfig] = {
    "lxc": LXC_CONFIG,
    "openssl-1": OPENSSL_1_CONFIG,
    "openssl-3": OPENSSL_3_CONFIG,
    "p11-kit": P11_KIT_CONFIG,
    "x264": X264_CONFIG,
}


def get_project_config(name: str) -> ProjectConfig | None:
    """Get project configuration by name."""
    return PROJECT_CONFIGS.get(name)


def list_projects() -> list[str]:
    """List all available project names."""
    return list(PROJECT_CONFIGS.keys())
