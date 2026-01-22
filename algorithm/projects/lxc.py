"""LXC project configuration."""

from algorithm.projects.base import ProjectConfig, ConfigSource, CodeSource

LXC_CONFIG = ProjectConfig(
    name="lxc",
    config_source=ConfigSource.GENERATE,
    code_source=CodeSource.GIT,
    git_repo="https://github.com/lxc/lxc.git",
    git_commit="72cc48f99",
    config_cmd="./autogen.sh && ./configure",
    build_cmd="make -j4",
    build_cmd_repair="make -j4",
    clean_cmd="make clean || true",
)
