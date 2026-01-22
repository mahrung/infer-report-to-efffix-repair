"""Tests for algorithm/projects/base.py"""

import pytest

from algorithm.projects.base import ProjectConfig, ConfigSource, CodeSource


class TestProjectConfig:
    """Tests for ProjectConfig dataclass."""

    def test_create_with_required_fields(self):
        """Test creating config with only required fields."""
        config = ProjectConfig(
            name="test-project",
            config_source=ConfigSource.GENERATE,
            code_source=CodeSource.GIT,
            git_repo="https://github.com/example/repo.git",
            git_commit="abc123",
        )

        assert config.name == "test-project"
        assert config.config_source == ConfigSource.GENERATE
        assert config.code_source == CodeSource.GIT
        assert config.git_repo == "https://github.com/example/repo.git"
        assert config.git_commit == "abc123"

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = ProjectConfig(
            name="test",
            config_source=ConfigSource.GENERATE,
            code_source=CodeSource.GIT,
            git_repo="https://example.com/repo.git",
            git_commit="abc123",
        )

        assert config.config_cmd == "true"
        assert config.build_cmd == "make -j4"
        assert config.build_cmd_repair == "make -j4"
        assert config.clean_cmd == "make clean || true"
        assert config.pulse_args == ""
        assert config.src_subdir == "src"
        assert config.container_benchmark_path == "/opt/effFix-benchmark"

    def test_custom_values(self):
        """Test creating config with custom values."""
        config = ProjectConfig(
            name="custom-project",
            config_source=ConfigSource.CONTAINER,
            code_source=CodeSource.CONTAINER,
            git_repo="https://example.com/repo.git",
            git_commit="def456",
            config_cmd="./configure --prefix=/usr",
            build_cmd="make -j8",
            build_cmd_repair="make -j2",
            clean_cmd="make distclean",
            pulse_args="--extra-flag",
            src_subdir="source",
            container_benchmark_path="/custom/path",
        )

        assert config.name == "custom-project"
        assert config.config_source == ConfigSource.CONTAINER
        assert config.code_source == CodeSource.CONTAINER
        assert config.config_cmd == "./configure --prefix=/usr"
        assert config.build_cmd == "make -j8"
        assert config.build_cmd_repair == "make -j2"
        assert config.clean_cmd == "make distclean"
        assert config.pulse_args == "--extra-flag"
        assert config.src_subdir == "source"
        assert config.container_benchmark_path == "/custom/path"

    def test_empty_git_repo_for_container_based(self):
        """Test creating config with empty git_repo for container-based projects."""
        config = ProjectConfig(
            name="container-project",
            config_source=ConfigSource.CONTAINER,
            code_source=CodeSource.CONTAINER,
            git_repo="",
            git_commit="",
        )

        assert config.git_repo == ""
        assert config.git_commit == ""
        assert config.code_source == CodeSource.CONTAINER

    def test_config_is_dataclass(self):
        """Test that ProjectConfig behaves as a dataclass."""
        config = ProjectConfig(
            name="test",
            config_source=ConfigSource.GENERATE,
            code_source=CodeSource.GIT,
            git_repo="https://example.com/repo.git",
            git_commit="abc123",
        )

        # Dataclasses should have __eq__ that compares fields
        config2 = ProjectConfig(
            name="test",
            config_source=ConfigSource.GENERATE,
            code_source=CodeSource.GIT,
            git_repo="https://example.com/repo.git",
            git_commit="abc123",
        )

        assert config == config2

    def test_config_inequality(self):
        """Test that different configs are not equal."""
        config1 = ProjectConfig(
            name="project1",
            config_source=ConfigSource.GENERATE,
            code_source=CodeSource.GIT,
            git_repo="https://example.com/repo1.git",
            git_commit="abc123",
        )
        config2 = ProjectConfig(
            name="project2",
            config_source=ConfigSource.CONTAINER,
            code_source=CodeSource.CONTAINER,
            git_repo="https://example.com/repo2.git",
            git_commit="def456",
        )

        assert config1 != config2


class TestConfigSource:
    """Tests for ConfigSource enum."""

    def test_container_value(self):
        """Test CONTAINER enum value."""
        assert ConfigSource.CONTAINER.value == "container"

    def test_generate_value(self):
        """Test GENERATE enum value."""
        assert ConfigSource.GENERATE.value == "generate"


class TestCodeSource:
    """Tests for CodeSource enum."""

    def test_git_value(self):
        """Test GIT enum value."""
        assert CodeSource.GIT.value == "git"

    def test_container_value(self):
        """Test CONTAINER enum value."""
        assert CodeSource.CONTAINER.value == "container"
