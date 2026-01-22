"""x264 project configuration.

NOTE: x264 has no null-ptr cases in the container benchmark.
Configs must be generated from report.txt.
Source code is in the container.
"""

from algorithm.projects.base import ProjectConfig, ConfigSource, CodeSource

X264_CONFIG = ProjectConfig(
    name="x264",
    config_source=ConfigSource.GENERATE,
    code_source=CodeSource.CONTAINER,
    config_cmd="./configure",
    build_cmd="make -j4",
    build_cmd_repair="make -j4",
    clean_cmd="make clean || true",
)
