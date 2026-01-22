"""Tests for algorithm/utils/exec_in_container.py"""

import pytest
from unittest.mock import MagicMock, patch

from algorithm.utils.exec_in_container import ContainerSession, exec_in_container


class TestContainerSession:
    """Tests for ContainerSession class."""

    def test_init_default_workdir(self):
        """Test initialization with default workdir."""
        session = ContainerSession("container123")

        assert session.container_id == "container123"
        assert session.workdir == "/opt/effFix-benchmark"

    def test_init_custom_workdir(self):
        """Test initialization with custom workdir."""
        session = ContainerSession("container123", workdir="/custom/path")

        assert session.container_id == "container123"
        assert session.workdir == "/custom/path"

    @patch("subprocess.run")
    def test_exec_success(self, mock_run):
        """Test successful command execution."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="command output\n", stderr=""
        )

        session = ContainerSession("container123")
        result = session.exec("ls -la")

        assert result == "command output\n"
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "docker" in call_args
        assert "exec" in call_args
        assert "container123" in call_args
        assert "bash" in call_args

    @patch("subprocess.run")
    def test_exec_includes_workdir(self, mock_run):
        """Test that exec includes cd to workdir."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="output\n", stderr=""
        )

        session = ContainerSession("container123", workdir="/my/workdir")
        session.exec("pwd")

        call_args = mock_run.call_args[0][0]
        # The command should include cd to workdir
        command_str = call_args[-1]  # Last argument is the full command
        assert "cd /my/workdir" in command_str

    @patch("subprocess.run")
    def test_exec_failure_returns_none(self, mock_run, capsys):
        """Test that failed commands return None and print error."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="command not found"
        )

        session = ContainerSession("container123")
        result = session.exec("invalid_command")

        assert result is None
        captured = capsys.readouterr()
        assert "ERROR" in captured.out

    @patch("subprocess.run")
    def test_exec_empty_output(self, mock_run, capsys):
        """Test that empty output doesn't print anything."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        session = ContainerSession("container123")
        result = session.exec("true")

        assert result == ""
        captured = capsys.readouterr()
        # Should not print gray output for empty string
        assert captured.out == ""

    @patch("subprocess.run")
    def test_exec_capture_suppresses_output(self, mock_run, capsys):
        """Test that capture=True suppresses printing."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="captured output\n", stderr=""
        )

        session = ContainerSession("container123")
        result = session.exec("ls -la", capture=True)

        assert result == "captured output\n"
        captured = capsys.readouterr()
        # Should not print anything when capture=True
        assert captured.out == ""

    @patch("subprocess.run")
    def test_exec_capture_suppresses_error(self, mock_run, capsys):
        """Test that capture=True suppresses error printing."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="error message"
        )

        session = ContainerSession("container123")
        result = session.exec("failing_command", capture=True)

        assert result is None
        captured = capsys.readouterr()
        # Should not print error when capture=True
        assert captured.out == ""

    @patch("subprocess.Popen")
    def test_exec_streaming(self, mock_popen, capsys):
        """Test streaming command execution."""
        mock_process = MagicMock()
        mock_process.stdout = iter(["line1\n", "line2\n"])
        mock_process.wait.return_value = None
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        session = ContainerSession("container123")
        result = session.exec("long_command", stream=True)

        assert "line1" in result
        assert "line2" in result
        # Should have printed to console
        captured = capsys.readouterr()
        assert "line1" in captured.out
        assert "line2" in captured.out

    @patch("subprocess.Popen")
    def test_exec_streaming_failure(self, mock_popen, capsys):
        """Test streaming execution with failure."""
        mock_process = MagicMock()
        mock_process.stdout = iter(["partial output\n"])
        mock_process.wait.return_value = None
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        session = ContainerSession("container123")
        result = session.exec("failing_command", stream=True)

        assert result is None
        captured = capsys.readouterr()
        assert "exited with code 1" in captured.out

    def test_cd_absolute_path(self):
        """Test changing to absolute path."""
        session = ContainerSession("container123")
        result = session.cd("/new/absolute/path")

        assert session.workdir == "/new/absolute/path"
        assert result == "/new/absolute/path"

    @patch("subprocess.run")
    def test_cd_relative_path(self, mock_run):
        """Test changing to relative path."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="/opt/effFix-benchmark/subdir\n",
            stderr="",
        )

        session = ContainerSession("container123")
        result = session.cd("subdir")

        assert session.workdir == "/opt/effFix-benchmark/subdir"
        assert result == "/opt/effFix-benchmark/subdir"

    @patch("subprocess.run")
    def test_cd_relative_path_failure(self, mock_run):
        """Test cd with relative path when directory doesn't exist."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="No such file or directory",
        )

        session = ContainerSession("container123")
        original_workdir = session.workdir
        result = session.cd("nonexistent")

        # Workdir should remain unchanged on failure
        assert session.workdir == original_workdir
        assert result == original_workdir


class TestExecInContainer:
    """Tests for exec_in_container function."""

    @patch("subprocess.run")
    def test_exec_success(self, mock_run):
        """Test successful stateless execution."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="output\n", stderr=""
        )

        result = exec_in_container("container123", "echo hello")

        assert result == "output\n"

    @patch("subprocess.run")
    def test_exec_failure_returns_none(self, mock_run, capsys):
        """Test that failed execution returns None."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="error message"
        )

        result = exec_in_container("container123", "bad_command")

        assert result is None
        captured = capsys.readouterr()
        assert "ERROR" in captured.out

    @patch("subprocess.run")
    def test_exec_uses_sh(self, mock_run):
        """Test that exec_in_container uses sh instead of bash."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        exec_in_container("container123", "pwd")

        call_args = mock_run.call_args[0][0]
        assert "sh" in call_args
        assert "bash" not in call_args

    @patch("subprocess.run")
    def test_exec_empty_output(self, mock_run, capsys):
        """Test handling of empty output."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = exec_in_container("container123", "true")

        assert result == ""
        captured = capsys.readouterr()
        assert captured.out == ""
