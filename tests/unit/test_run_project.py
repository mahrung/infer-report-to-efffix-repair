"""Tests for algorithm/components/run_project.py"""

import os
import pytest
from unittest.mock import patch, MagicMock

from algorithm.components.run_project import (
    get_project_cases,
    get_generated_cases,
    discover_container_cases,
    run_project,
)
from algorithm.projects.base import ConfigSource, CodeSource


class TestGetProjectCases:
    """Tests for get_project_cases function."""

    @patch("algorithm.components.run_project.get_project_config")
    def test_returns_none_for_container_source(self, mock_get_config):
        """Test that None is returned for container-based projects."""
        mock_config = MagicMock()
        mock_config.config_source = ConfigSource.CONTAINER
        mock_get_config.return_value = mock_config

        cases = get_project_cases("openssl-1")

        assert cases is None

    @patch("algorithm.components.run_project.get_project_config")
    @patch("algorithm.components.run_project.get_generated_cases")
    def test_returns_generated_cases_for_generate_source(self, mock_gen_cases, mock_get_config):
        """Test that generated cases are returned for GENERATE projects."""
        mock_config = MagicMock()
        mock_config.config_source = ConfigSource.GENERATE
        mock_get_config.return_value = mock_config
        mock_gen_cases.return_value = ["null-ptr-1-lxc", "null-ptr-2-lxc"]

        cases = get_project_cases("lxc")

        assert cases == ["null-ptr-1-lxc", "null-ptr-2-lxc"]

    @patch("algorithm.components.run_project.get_project_config")
    def test_returns_empty_for_unknown_project(self, mock_get_config):
        """Test returns empty list for unknown project."""
        mock_get_config.return_value = None

        cases = get_project_cases("unknown-project")

        assert cases == []


class TestGetGeneratedCases:
    """Tests for get_generated_cases function."""

    def test_finds_cases_from_generated_configs(self, temp_dir, create_project_structure):
        """Test finding cases from generated_configs directory."""
        project_dir = create_project_structure("test-project", ["case-1", "case-2"])

        with patch(
            "algorithm.components.run_project.GENERATED_CONFIGS_DIR",
            str(temp_dir),
        ):
            cases = get_generated_cases("test-project")

        assert len(cases) == 2
        assert "case-1" in cases
        assert "case-2" in cases

    def test_returns_sorted_cases(self, temp_dir, create_project_structure):
        """Test that returned cases are sorted."""
        project_dir = create_project_structure("test-project", ["z-case", "a-case", "m-case"])

        with patch(
            "algorithm.components.run_project.GENERATED_CONFIGS_DIR",
            str(temp_dir),
        ):
            cases = get_generated_cases("test-project")

        assert cases == sorted(cases)

    def test_returns_empty_for_nonexistent_project(self):
        """Test returns empty list for nonexistent project directory."""
        with patch(
            "algorithm.components.run_project.GENERATED_CONFIGS_DIR",
            "/nonexistent/path",
        ):
            cases = get_generated_cases("unknown-project")

        assert cases == []

    def test_skips_source_directory(self, temp_dir, create_project_structure):
        """Test that _source directory is skipped."""
        project_dir = create_project_structure("test-project", ["case-1", "_source"])

        with patch(
            "algorithm.components.run_project.GENERATED_CONFIGS_DIR",
            str(temp_dir),
        ):
            cases = get_generated_cases("test-project")

        assert len(cases) == 1
        assert "case-1" in cases
        assert "_source" not in cases


class TestDiscoverContainerCases:
    """Tests for discover_container_cases function."""

    def test_discovers_cases_from_container(self, mock_container_session):
        """Test discovering cases from container."""
        mock_config = MagicMock()
        mock_config.container_benchmark_path = "/opt/effFix-benchmark"

        def exec_side_effect(cmd, capture=False):
            if "ls -1" in cmd:
                return "case-1\ncase-2\ncase-3"
            elif "test -f" in cmd:
                return "yes"
            return ""

        mock_container_session.exec.side_effect = exec_side_effect

        cases = discover_container_cases(mock_container_session, "test-project", mock_config)

        assert len(cases) == 3
        assert "case-1" in cases
        assert "case-2" in cases
        assert "case-3" in cases

    def test_returns_empty_on_ls_failure(self, mock_container_session):
        """Test returns empty list when ls fails."""
        mock_config = MagicMock()
        mock_config.container_benchmark_path = "/opt/effFix-benchmark"
        mock_container_session.exec.return_value = ""

        cases = discover_container_cases(mock_container_session, "test-project", mock_config)

        assert cases == []


class TestRunProject:
    """Tests for run_project function."""

    @patch("algorithm.components.run_project.get_project_config")
    @patch("algorithm.components.run_project.get_project_cases")
    @patch("algorithm.components.run_project.run_case")
    def test_runs_all_cases(self, mock_run_case, mock_get_cases, mock_get_config, mock_container_session):
        """Test that all cases in a project are run."""
        mock_config = MagicMock()
        mock_config.config_source = ConfigSource.GENERATE
        mock_get_config.return_value = mock_config
        mock_get_cases.return_value = ["case-1", "case-2", "case-3"]
        mock_run_case.return_value = {"status": "success"}

        run_project(mock_container_session, "test-project")

        assert mock_run_case.call_count == 3

    @patch("algorithm.components.run_project.get_project_config")
    @patch("algorithm.components.run_project.get_project_cases")
    @patch("algorithm.components.run_project.run_case")
    def test_passes_repair_only_flag(
        self, mock_run_case, mock_get_cases, mock_get_config, mock_container_session
    ):
        """Test that repair_only flag is passed to run_case."""
        mock_config = MagicMock()
        mock_config.config_source = ConfigSource.GENERATE
        mock_get_config.return_value = mock_config
        mock_get_cases.return_value = ["case-1"]
        mock_run_case.return_value = {"status": "success"}

        run_project(mock_container_session, "test-project", repair_only=True)

        mock_run_case.assert_called_once()
        call_kwargs = mock_run_case.call_args[1]
        assert call_kwargs["repair_only"] is True

    @patch("algorithm.components.run_project.get_project_config")
    @patch("algorithm.components.run_project.get_project_cases")
    def test_handles_no_cases(self, mock_get_cases, mock_get_config, mock_container_session, capsys):
        """Test handling when no cases are found."""
        mock_config = MagicMock()
        mock_config.config_source = ConfigSource.GENERATE
        mock_get_config.return_value = mock_config
        mock_get_cases.return_value = []

        result = run_project(mock_container_session, "unknown-project")

        captured = capsys.readouterr()
        assert "No cases found" in captured.out
        assert result == mock_container_session

    @patch("algorithm.components.run_project.get_project_config")
    @patch("algorithm.components.run_project.get_project_cases")
    @patch("algorithm.components.run_project.run_case")
    def test_returns_session(self, mock_run_case, mock_get_cases, mock_get_config, mock_container_session):
        """Test that session is returned."""
        mock_config = MagicMock()
        mock_config.config_source = ConfigSource.GENERATE
        mock_get_config.return_value = mock_config
        mock_get_cases.return_value = ["case-1"]
        mock_run_case.return_value = {"status": "success"}

        result = run_project(mock_container_session, "test-project")

        assert result == mock_container_session

    @patch("algorithm.components.run_project.get_project_config")
    def test_handles_unknown_project(self, mock_get_config, mock_container_session, capsys):
        """Test handling unknown project."""
        mock_get_config.return_value = None

        result = run_project(mock_container_session, "unknown-project")

        captured = capsys.readouterr()
        assert "Unknown project" in captured.out
        assert result == mock_container_session

    @patch("algorithm.components.run_project.get_project_config")
    @patch("algorithm.components.run_project.get_project_cases")
    @patch("algorithm.components.run_project.discover_container_cases")
    @patch("algorithm.components.run_project.run_case")
    def test_discovers_cases_for_container_project(
        self, mock_run_case, mock_discover, mock_get_cases, mock_get_config, mock_container_session
    ):
        """Test that container cases are discovered when get_project_cases returns None."""
        mock_config = MagicMock()
        mock_config.config_source = ConfigSource.CONTAINER
        mock_get_config.return_value = mock_config
        mock_get_cases.return_value = None  # Indicates container-based
        mock_discover.return_value = ["null-ptr-1-openssl-1", "null-ptr-2-openssl-1"]
        mock_run_case.return_value = {"status": "success"}

        run_project(mock_container_session, "openssl-1")

        mock_discover.assert_called_once()
        assert mock_run_case.call_count == 2
