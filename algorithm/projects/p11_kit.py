"""p11-kit project configuration."""

from algorithm.projects.base import ProjectConfig, ConfigSource, CodeSource

P11_KIT_CONFIG = ProjectConfig(
    name="p11-kit",
    config_source=ConfigSource.GENERATE,
    code_source=CodeSource.CONTAINER,
    config_cmd="./autogen.sh && ./configure",
    build_cmd="make -j4",
    build_cmd_repair="make -j4",
    clean_cmd="make clean || true",
)
