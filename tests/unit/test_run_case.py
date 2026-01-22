"""Tests for algorithm/components/run_case.py"""

import pytest
from unittest.mock import MagicMock, patch

from algorithm.components.run_case import (
    run_case,
    run_fake_case,
)
from algorithm.projects.base import ConfigSource, CodeSource


class TestRunCase:
    """Tests for run_case function."""

    def test_run_fake_case_returns_success(self, mock_container_session):
        """Test running a fake case returns success."""
        result = run_case(mock_container_session, "fake", "test-case")

        assert result["status"] == "success"
        assert result["case"] == "test-case"

    def test_run_fake_case_calls_session_exec(self, mock_container_session):
        """Test that fake case calls session.exec multiple times."""
        run_case(mock_container_session, "fake", "test-case")

        # Fake case should call exec 4 times (steps 1-4)
        assert mock_container_session.exec.call_count == 4

    @patch("algorithm.components.run_case.get_project_config")
    @patch("algorithm.components.run_case.regenerate_case")
    @patch("algorithm.components.run_case.export_results")
    def test_run_case_git_based_project(
        self, mock_export, mock_regen, mock_get_config, mock_container_session
    ):
        """Test running a git-based project case."""
        mock_config = MagicMock()
        mock_config.config_source = ConfigSource.GENERATE
        mock_config.code_source = CodeSource.GIT
        mock_get_config.return_value = mock_config
        mock_regen.return_value = True
        mock_container_session.exec.return_value = "success output"

        result = run_case(mock_container_session, "lxc", "null-ptr-1-lxc")

        assert result["status"] == "success"
        assert result["case"] == "null-ptr-1-lxc"
        mock_export.assert_called_once()

    @patch("algorithm.components.run_case.get_project_config")
    @patch("algorithm.components.run_case.export_results")
    def test_run_case_repair_only_mode(
        self, mock_export, mock_get_config, mock_container_session
    ):
        """Test running in repair-only mode."""
        mock_config = MagicMock()
        mock_config.config_source = ConfigSource.GENERATE
        mock_config.code_source = CodeSource.GIT
        mock_get_config.return_value = mock_config
        mock_container_session.exec.return_value = "success output"

        result = run_case(
            mock_container_session, "lxc", "null-ptr-1-lxc", repair_only=True
        )

        assert result["status"] == "success"
        # Should not call regenerate_case in repair-only mode
        mock_export.assert_called_once()

    @patch("algorithm.components.run_case.get_project_config")
    @patch("algorithm.components.run_case.export_results")
    def test_run_case_pre_failure(
        self, mock_export, mock_get_config, mock_container_session
    ):
        """Test handling pre-analysis failure."""
        mock_config = MagicMock()
        mock_config.config_source = ConfigSource.GENERATE
        mock_config.code_source = CodeSource.GIT
        mock_get_config.return_value = mock_config

        # Create a side_effect function that returns None for streaming pre-analysis
        call_count = [0]

        def exec_side_effect(cmd, stream=False, capture=False):
            call_count[0] += 1
            # The pre-analysis call (with stream=True) fails
            if stream:
                return None
            return "success output"

        mock_container_session.exec.side_effect = exec_side_effect

        result = run_case(mock_container_session, "lxc", "null-ptr-1-lxc")

        assert result["status"] == "failed"
        assert result["stage"] == "pre"

    @patch("algorithm.components.run_case.get_project_config")
    @patch("algorithm.components.run_case.regenerate_case")
    @patch("algorithm.components.run_case.export_results")
    def test_run_case_regen_failure(
        self, mock_export, mock_regen, mock_get_config, mock_container_session
    ):
        """Test handling regenerate config failure."""
        mock_config = MagicMock()
        mock_config.config_source = ConfigSource.GENERATE
        mock_config.code_source = CodeSource.GIT
        mock_get_config.return_value = mock_config
        mock_regen.return_value = False  # Regen fails
        mock_container_session.exec.return_value = "success output"

        result = run_case(mock_container_session, "lxc", "null-ptr-1-lxc")

        assert result["status"] == "failed"
        assert result["stage"] == "regen"

    @patch("algorithm.components.run_case.get_project_config")
    def test_run_case_unknown_project(self, mock_get_config, mock_container_session):
        """Test handling unknown project."""
        mock_get_config.return_value = None

        result = run_case(mock_container_session, "unknown", "test-case")

        assert result["status"] == "failed"
        assert result["stage"] == "config"


class TestRunFakeCase:
    """Tests for run_fake_case function."""

    def test_executes_all_steps(self, mock_container_session):
        """Test that all fake steps are executed."""
        run_fake_case(mock_container_session)

        assert mock_container_session.exec.call_count == 4

    def test_executes_echo_commands(self, mock_container_session):
        """Test that echo commands are executed."""
        run_fake_case(mock_container_session)

        calls = mock_container_session.exec.call_args_list
        # Check that calls contain echo commands
        for call in calls:
            assert "echo" in call[0][0]
