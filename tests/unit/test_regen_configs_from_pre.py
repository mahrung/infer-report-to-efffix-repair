"""Tests for algorithm/regen_configs_from_pre.py"""

import json
import pytest

from algorithm.regen_configs_from_pre import (
    SUPPORTED_BUG_TYPES,
    create_config_content,
    extract_start_end_lines,
    filter_bugs,
    load_infer_report,
)


class TestLoadInferReport:
    """Tests for load_infer_report function."""

    def test_load_valid_report(self, temp_dir, sample_infer_json_report):
        """Test loading a valid report.json file."""
        # Create the expected directory structure
        pre_dir = temp_dir / "pre" / "infer-out-whole"
        pre_dir.mkdir(parents=True)
        report_path = pre_dir / "report.json"
        report_path.write_text(json.dumps(sample_infer_json_report))

        bugs = load_infer_report(str(temp_dir))

        assert len(bugs) == 2
        assert bugs[0]["bug_type"] == "NULLPTR_DEREFERENCE"

    def test_load_nonexistent_report(self, temp_dir, capsys):
        """Test loading when report doesn't exist."""
        bugs = load_infer_report(str(temp_dir / "nonexistent"))

        assert bugs == []
        captured = capsys.readouterr()
        assert "Report not found" in captured.out

    def test_load_empty_report(self, temp_dir):
        """Test loading an empty report."""
        pre_dir = temp_dir / "pre" / "infer-out-whole"
        pre_dir.mkdir(parents=True)
        report_path = pre_dir / "report.json"
        report_path.write_text("[]")

        bugs = load_infer_report(str(temp_dir))

        assert bugs == []


class TestFilterBugs:
    """Tests for filter_bugs function."""

    def test_filter_supported_types(self, sample_infer_json_report):
        """Test filtering to supported bug types."""
        # Add an unsupported bug type
        bugs = sample_infer_json_report + [{"bug_type": "UNSUPPORTED"}]

        filtered = filter_bugs(bugs)

        assert len(filtered) == 2

    def test_filter_specific_type(self, sample_infer_json_report):
        """Test filtering for a specific bug type."""
        filtered = filter_bugs(sample_infer_json_report, "NULLPTR_DEREFERENCE")

        assert len(filtered) == 1
        assert filtered[0]["bug_type"] == "NULLPTR_DEREFERENCE"

    def test_filter_empty_list(self):
        """Test filtering an empty list."""
        filtered = filter_bugs([])

        assert filtered == []

    def test_filter_no_supported_bugs(self):
        """Test filtering when no bugs are supported."""
        bugs = [{"bug_type": "UNSUPPORTED_TYPE"}]

        filtered = filter_bugs(bugs)

        assert filtered == []

    def test_filter_all_supported_types(self):
        """Test that all supported types are kept."""
        bugs = [
            {"bug_type": "NULLPTR_DEREFERENCE"},
            {"bug_type": "MEMORY_LEAK_C"},
            {"bug_type": "USE_AFTER_FREE"},
        ]

        filtered = filter_bugs(bugs)

        assert len(filtered) == 3


class TestExtractStartEndLines:
    """Tests for extract_start_end_lines function."""

    def test_extract_from_bug_trace(self):
        """Test extracting lines from bug_trace."""
        bug = {
            "line": 100,
            "bug_trace": [
                {"line_number": 95},
                {"line_number": 100},
                {"line_number": 105},
            ],
        }

        start, end = extract_start_end_lines(bug)

        assert start == 95
        assert end == 105

    def test_extract_with_empty_trace(self):
        """Test extracting when bug_trace is empty."""
        bug = {"line": 100, "bug_trace": []}

        start, end = extract_start_end_lines(bug)

        assert start == 100
        assert end == 100

    def test_extract_without_trace(self):
        """Test extracting when bug_trace is missing."""
        bug = {"line": 100}

        start, end = extract_start_end_lines(bug)

        assert start == 100
        assert end == 100

    def test_extract_single_element_trace(self):
        """Test extracting from single-element trace."""
        bug = {
            "line": 100,
            "bug_trace": [{"line_number": 50}],
        }

        start, end = extract_start_end_lines(bug)

        assert start == 50
        assert end == 50

    def test_extract_trace_missing_line_number(self):
        """Test extracting when trace element lacks line_number."""
        bug = {
            "line": 100,
            "bug_trace": [{"description": "start"}, {"description": "end"}],
        }

        start, end = extract_start_end_lines(bug)

        # Falls back to bug['line']
        assert start == 100
        assert end == 100


class TestCreateConfigContent:
    """Tests for create_config_content function."""

    def test_creates_valid_config(self):
        """Test creating valid config content."""
        bug = {
            "bug_type": "NULLPTR_DEREFERENCE",
            "file": "src/test.c",
            "procedure": "test_func",
            "line": 100,
            "bug_trace": [
                {"line_number": 95},
                {"line_number": 100},
            ],
        }

        content = create_config_content(
            bug=bug,
            tag_id="null-ptr-1-test",
            container_base="/base/test",
            config_cmd="./configure",
            build_cmd="make",
            clean_cmd="make clean",
        )

        assert "tag_id:null-ptr-1-test" in content
        assert "bug_start_line:95" in content
        assert "bug_end_line:100" in content
        assert "bug_type:NULLPTR_DEREFERENCE" in content
        assert "bug_file:src/test.c" in content
        assert "bug_procedure:test_func" in content

    def test_config_has_all_required_fields(self):
        """Test that all required fields are present."""
        bug = {
            "bug_type": "NULLPTR_DEREFERENCE",
            "file": "src/test.c",
            "procedure": "test_func",
            "line": 100,
            "bug_trace": [],
        }

        content = create_config_content(
            bug=bug,
            tag_id="test-case",
            container_base="/base",
            config_cmd="./configure",
            build_cmd="make",
            clean_cmd="make clean",
        )

        required_fields = [
            "tag_id:",
            "config_command:",
            "build_command:",
            "build_command_repair:",
            "clean_command:",
            "src_dir:",
            "bug_type:",
            "bug_file:",
            "bug_procedure:",
            "bug_start_line:",
            "bug_end_line:",
            "runtime_dir_pre:",
            "runtime_dir_repair:",
        ]

        for field in required_fields:
            assert field in content, f"Missing field: {field}"

    def test_config_paths_are_correct(self):
        """Test that paths are correctly constructed."""
        bug = {
            "bug_type": "NULLPTR_DEREFERENCE",
            "file": "src/test.c",
            "procedure": "test_func",
            "line": 100,
            "bug_trace": [],
        }

        content = create_config_content(
            bug=bug,
            tag_id="case-1",
            container_base="/my/base/path",
            config_cmd="./configure",
            build_cmd="make",
            clean_cmd="make clean",
        )

        assert "src_dir:/my/base/path/case-1/src" in content
        assert "runtime_dir_pre:/my/base/path/case-1/pre" in content
        assert "runtime_dir_repair:/my/base/path/case-1/repair" in content

    def test_build_command_repair_matches_build_command(self):
        """Test that build_command_repair matches build_command."""
        bug = {
            "bug_type": "NULLPTR_DEREFERENCE",
            "file": "src/test.c",
            "procedure": "test_func",
            "line": 100,
            "bug_trace": [],
        }

        content = create_config_content(
            bug=bug,
            tag_id="test",
            container_base="/base",
            config_cmd="./configure",
            build_cmd="make -j8",
            clean_cmd="make clean",
        )

        assert "build_command:make -j8" in content
        assert "build_command_repair:make -j8" in content
