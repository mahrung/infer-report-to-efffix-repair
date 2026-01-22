"""OpenSSL-3 project configuration."""

from algorithm.projects.base import ProjectConfig, ConfigSource, CodeSource

OPENSSL_3_CONFIG = ProjectConfig(
    name="openssl-3",
    config_source=ConfigSource.CONTAINER,
    code_source=CodeSource.CONTAINER,
    config_cmd="./config",
    build_cmd="make -j4",
    build_cmd_repair="make -j4",
    clean_cmd="make clean || true",
)
