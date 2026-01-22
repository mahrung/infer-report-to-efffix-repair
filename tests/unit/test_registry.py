"""Tests for algorithm/projects/registry.py"""

import pytest

from algorithm.projects.base import ProjectConfig
from algorithm.projects.registry import (
    PROJECT_CONFIGS,
    get_project_config,
    list_projects,
)


class TestGetProjectConfig:
    """Tests for get_project_config function."""

    def test_get_existing_project(self):
        """Test getting an existing project config."""
        config = get_project_config("lxc")

        assert config is not None
        assert isinstance(config, ProjectConfig)
        assert config.name == "lxc"

    def test_get_nonexistent_project(self):
        """Test getting a non-existent project returns None."""
        config = get_project_config("nonexistent")

        assert config is None

    def test_get_project_returns_correct_type(self):
        """Test that returned config is a ProjectConfig instance."""
        config = get_project_config("lxc")

        assert isinstance(config, ProjectConfig)
        assert hasattr(config, "name")
        assert hasattr(config, "git_repo")
        assert hasattr(config, "build_cmd")

    @pytest.mark.parametrize("project_name", list(PROJECT_CONFIGS.keys()))
    def test_all_registered_projects_have_valid_config(self, project_name):
        """Test that all registered projects have valid configs."""
        config = get_project_config(project_name)

        assert config is not None
        assert config.name == project_name

    def test_get_project_config_is_case_sensitive(self):
        """Test that project lookup is case sensitive."""
        config_lower = get_project_config("lxc")
        config_upper = get_project_config("LXC")

        assert config_lower is not None
        assert config_upper is None


class TestListProjects:
    """Tests for list_projects function."""

    def test_returns_list_of_strings(self):
        """Test that list_projects returns a list of strings."""
        projects = list_projects()

        assert isinstance(projects, list)
        assert all(isinstance(p, str) for p in projects)

    def test_contains_expected_projects(self):
        """Test that expected projects are in the list."""
        projects = list_projects()

        # Check that known projects are in the list
        assert "lxc" in projects
        assert "openssl-1" in projects
        assert "openssl-3" in projects

    def test_matches_registry_keys(self):
        """Test that list matches PROJECT_CONFIGS keys."""
        projects = list_projects()

        assert set(projects) == set(PROJECT_CONFIGS.keys())

    def test_list_is_not_empty(self):
        """Test that the list is not empty."""
        projects = list_projects()

        assert len(projects) > 0


class TestProjectConfigs:
    """Tests for PROJECT_CONFIGS dictionary."""

    def test_all_configs_are_project_config_instances(self):
        """Test that all registry entries are ProjectConfig instances."""
        for name, config in PROJECT_CONFIGS.items():
            assert isinstance(
                config, ProjectConfig
            ), f"{name} is not a ProjectConfig"

    def test_all_configs_have_matching_names(self):
        """Test that config names match registry keys."""
        for name, config in PROJECT_CONFIGS.items():
            assert (
                config.name == name
            ), f"Config name {config.name} doesn't match key {name}"

    def test_all_configs_have_required_fields(self):
        """Test that all configs have required fields set."""
        for name, config in PROJECT_CONFIGS.items():
            assert config.name, f"{name} missing name"
            assert config.build_cmd, f"{name} missing build_cmd"
            assert config.clean_cmd, f"{name} missing clean_cmd"
