"""OpenSSL-1 project configuration."""

from algorithm.projects.base import ProjectConfig, ConfigSource, CodeSource

OPENSSL_1_CONFIG = ProjectConfig(
    name="openssl-1",
    config_source=ConfigSource.CONTAINER,
    code_source=CodeSource.CONTAINER,
    config_cmd="./config",
    build_cmd="make -j4",
    build_cmd_repair="make -j4",
    clean_cmd="make clean || true",
)
