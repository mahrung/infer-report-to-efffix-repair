"""Tests for get_running_containers.py"""

import pytest
from unittest.mock import MagicMock, patch

from get_running_containers import get_running_containers


class TestGetRunningContainers:
    """Tests for get_running_containers function."""

    @patch("subprocess.run")
    def test_returns_containers_list(self, mock_run):
        """Test that containers are parsed correctly."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="abc123\tefffix-lxc\tefffix-experiments:latest\ndef456\tefffix-openssl\tefffix-experiments:latest",
            stderr="",
        )

        containers = get_running_containers()

        assert len(containers) == 2
        assert containers[0]["id"] == "abc123"
        assert containers[0]["name"] == "efffix-lxc"
        assert containers[0]["image"] == "efffix-experiments:latest"
        assert containers[1]["id"] == "def456"
        assert containers[1]["name"] == "efffix-openssl"

    @patch("subprocess.run")
    def test_returns_empty_list_on_error(self, mock_run):
        """Test that errors return an empty list."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="docker not found"
        )

        containers = get_running_containers()

        assert containers == []

    @patch("subprocess.run")
    def test_handles_no_containers(self, mock_run):
        """Test handling when no containers are running."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        containers = get_running_containers()

        assert containers == []

    @patch("subprocess.run")
    def test_handles_single_container(self, mock_run):
        """Test handling a single running container."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="abc123\tmy-container\tmy-image:latest",
            stderr="",
        )

        containers = get_running_containers()

        assert len(containers) == 1
        assert containers[0]["id"] == "abc123"
        assert containers[0]["name"] == "my-container"
        assert containers[0]["image"] == "my-image:latest"

    @patch("subprocess.run")
    def test_handles_malformed_output_missing_fields(self, mock_run):
        """Test handling malformed docker output with missing fields."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="invalid_line_without_tabs\nabc123\tname",  # Missing image
            stderr="",
        )

        containers = get_running_containers()

        # Should skip lines that don't have all fields
        assert len(containers) == 0

    @patch("subprocess.run")
    def test_handles_empty_lines(self, mock_run):
        """Test handling output with empty lines."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="\nabc123\tcontainer\timage\n\n",
            stderr="",
        )

        containers = get_running_containers()

        assert len(containers) == 1
        assert containers[0]["id"] == "abc123"

    @patch("subprocess.run")
    def test_calls_docker_with_correct_args(self, mock_run):
        """Test that docker is called with correct arguments."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        get_running_containers()

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "docker" in call_args
        assert "ps" in call_args
        assert "--format" in call_args

    @patch("subprocess.run")
    def test_captures_output(self, mock_run):
        """Test that subprocess is called with capture_output=True."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        get_running_containers()

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("capture_output") is True
        assert call_kwargs.get("text") is True
