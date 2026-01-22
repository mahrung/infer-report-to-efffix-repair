"""Tests for algorithm/report_to_config.py"""

import pytest

from algorithm.report_to_config import (
    SUPPORTED_BUG_TYPES,
    create_config_content,
    filter_supported_bugs,
    find_procedure_name,
    generate_tag_id,
    parse_report,
)


class TestParseReport:
    """Tests for parse_report function."""

    def test_parse_empty_file(self, temp_dir):
        """Test parsing an empty report file."""
        report_path = temp_dir / "empty.txt"
        report_path.write_text("")

        bugs = parse_report(str(report_path))

        assert bugs == []

    def test_parse_single_bug(self, temp_dir):
        """Test parsing a report with a single bug."""
        report_content = """#0
src/file.c:100: error: Null Dereference(NULLPTR_DEREFERENCE)
  `ptr` could be null and is dereferenced.
  99. 	ptr = get_ptr();
  100. 	ptr->field = value;
       ^
  101. 	return 0;
"""
        report_path = temp_dir / "single_bug.txt"
        report_path.write_text(report_content)

        bugs = parse_report(str(report_path))

        assert len(bugs) == 1
        assert bugs[0]["index"] == 0
        assert bugs[0]["file"] == "src/file.c"
        assert bugs[0]["line"] == 100
        assert bugs[0]["bug_type_id"] == "NULLPTR_DEREFERENCE"
        assert len(bugs[0]["code_lines"]) == 3

    def test_parse_multiple_bugs(self, create_report_file):
        """Test parsing a report with multiple bugs."""
        bugs = parse_report(str(create_report_file))

        assert len(bugs) == 3
        assert bugs[0]["bug_type_id"] == "USE_AFTER_FREE"
        assert bugs[1]["bug_type_id"] == "NULLPTR_DEREFERENCE"
        assert bugs[2]["bug_type_id"] == "MEMORY_LEAK_C"

    def test_parse_extracts_file_and_line(self, create_report_file):
        """Test that file paths and line numbers are extracted correctly."""
        bugs = parse_report(str(create_report_file))

        assert bugs[0]["file"] == "hooks/unmount-namespace.c"
        assert bugs[0]["line"] == 123
        assert bugs[1]["file"] == "src/lxc/af_unix.c"
        assert bugs[1]["line"] == 154

    def test_parse_extracts_description(self, create_report_file):
        """Test that bug descriptions are extracted correctly."""
        bugs = parse_report(str(create_report_file))

        assert bugs[1]["description"] is not None
        assert "cmsg" in bugs[1]["description"]
        assert "null" in bugs[1]["description"]

    def test_parse_extracts_code_lines(self, create_report_file):
        """Test that code lines are extracted correctly."""
        bugs = parse_report(str(create_report_file))

        # Check that code lines have line_num and code
        for bug in bugs:
            assert len(bug["code_lines"]) > 0
            for code_line in bug["code_lines"]:
                assert "line_num" in code_line
                assert "code" in code_line

    def test_parse_handles_nonexistent_file(self, temp_dir):
        """Test that parsing a non-existent file raises an error."""
        with pytest.raises(FileNotFoundError):
            parse_report(str(temp_dir / "nonexistent.txt"))


class TestFilterSupportedBugs:
    """Tests for filter_supported_bugs function."""

    def test_filter_returns_supported_types_only(self):
        """Test that only supported bug types are returned."""
        bugs = [
            {"bug_type_id": "NULLPTR_DEREFERENCE"},
            {"bug_type_id": "MEMORY_LEAK_C"},
            {"bug_type_id": "USE_AFTER_FREE"},
            {"bug_type_id": "UNSUPPORTED_TYPE"},
        ]

        filtered = filter_supported_bugs(bugs)

        assert len(filtered) == 3
        assert all(b["bug_type_id"] in SUPPORTED_BUG_TYPES for b in filtered)

    def test_filter_by_specific_type(self):
        """Test filtering for a specific bug type."""
        bugs = [
            {"bug_type_id": "NULLPTR_DEREFERENCE"},
            {"bug_type_id": "MEMORY_LEAK_C"},
            {"bug_type_id": "NULLPTR_DEREFERENCE"},
        ]

        filtered = filter_supported_bugs(bugs, "NULLPTR_DEREFERENCE")

        assert len(filtered) == 2
        assert all(b["bug_type_id"] == "NULLPTR_DEREFERENCE" for b in filtered)

    def test_filter_empty_list(self):
        """Test filtering an empty list."""
        filtered = filter_supported_bugs([])
        assert filtered == []

    def test_filter_no_matches(self):
        """Test filtering when no bugs match."""
        bugs = [{"bug_type_id": "UNSUPPORTED_TYPE"}]

        filtered = filter_supported_bugs(bugs)

        assert filtered == []

    def test_filter_preserves_bug_data(self):
        """Test that filtering preserves all bug data."""
        bugs = [
            {
                "bug_type_id": "NULLPTR_DEREFERENCE",
                "file": "test.c",
                "line": 100,
                "extra_field": "value",
            }
        ]

        filtered = filter_supported_bugs(bugs)

        assert len(filtered) == 1
        assert filtered[0]["file"] == "test.c"
        assert filtered[0]["line"] == 100
        assert filtered[0]["extra_field"] == "value"


class TestGenerateTagId:
    """Tests for generate_tag_id function."""

    def test_generate_null_ptr_tag(self):
        """Test generating tag ID for null pointer bugs."""
        tag = generate_tag_id("NULLPTR_DEREFERENCE", 1, "lxc")

        assert tag == "null-ptr-1-lxc"

    def test_generate_memory_leak_tag(self):
        """Test generating tag ID for memory leak bugs."""
        tag = generate_tag_id("MEMORY_LEAK_C", 5, "openssl")

        assert tag == "memory-leak-5-openssl"

    def test_generate_use_after_free_tag(self):
        """Test generating tag ID for use-after-free bugs."""
        tag = generate_tag_id("USE_AFTER_FREE", 3, "project")

        assert tag == "use-after-free-3-project"

    def test_generate_unknown_type_tag(self):
        """Test generating tag ID for unknown bug types."""
        tag = generate_tag_id("UNKNOWN_TYPE", 1, "test")

        assert tag == "bug-1-test"

    def test_generate_with_different_indices(self):
        """Test generating tags with various indices."""
        tag1 = generate_tag_id("NULLPTR_DEREFERENCE", 1, "proj")
        tag2 = generate_tag_id("NULLPTR_DEREFERENCE", 10, "proj")
        tag3 = generate_tag_id("NULLPTR_DEREFERENCE", 100, "proj")

        assert tag1 == "null-ptr-1-proj"
        assert tag2 == "null-ptr-10-proj"
        assert tag3 == "null-ptr-100-proj"


class TestCreateConfigContent:
    """Tests for create_config_content function."""

    def test_creates_valid_config(self, sample_bug_dict):
        """Test that a valid config is created."""
        content = create_config_content(
            bug=sample_bug_dict,
            tag_id="null-ptr-1-lxc",
            subject="lxc",
            container_base="/opt/effFix-benchmark",
            config_cmd="./configure",
            build_cmd="make -j4",
            build_cmd_repair="make -j4",
            clean_cmd="make clean",
            pulse_args="",
        )

        assert "tag_id:null-ptr-1-lxc" in content
        assert "bug_type:NULLPTR_DEREFERENCE" in content
        assert "bug_file:src/lxc/af_unix.c" in content
        assert "bug_start_line:154" in content

    def test_includes_pulse_args_when_provided(self, sample_bug_dict):
        """Test that pulse_args are included when provided."""
        content = create_config_content(
            bug=sample_bug_dict,
            tag_id="test",
            subject="test",
            container_base="/base",
            config_cmd="true",
            build_cmd="make",
            build_cmd_repair="make",
            clean_cmd="make clean",
            pulse_args="--extra-arg value",
        )

        assert "pulse_extra_command:--extra-arg value" in content

    def test_excludes_pulse_args_when_empty(self, sample_bug_dict):
        """Test that pulse_args line is excluded when empty."""
        content = create_config_content(
            bug=sample_bug_dict,
            tag_id="test",
            subject="test",
            container_base="/base",
            config_cmd="true",
            build_cmd="make",
            build_cmd_repair="make",
            clean_cmd="make clean",
            pulse_args="",
        )

        assert "pulse_extra_command:" not in content

    def test_config_has_all_required_fields(self, sample_bug_dict):
        """Test that all required config fields are present."""
        content = create_config_content(
            bug=sample_bug_dict,
            tag_id="test",
            subject="test",
            container_base="/base",
            config_cmd="true",
            build_cmd="make",
            build_cmd_repair="make",
            clean_cmd="make clean",
            pulse_args="",
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

    def test_config_paths_use_container_base(self, sample_bug_dict):
        """Test that paths are correctly based on container_base."""
        content = create_config_content(
            bug=sample_bug_dict,
            tag_id="null-ptr-1-proj",
            subject="proj",
            container_base="/custom/path",
            config_cmd="true",
            build_cmd="make",
            build_cmd_repair="make",
            clean_cmd="make clean",
            pulse_args="",
        )

        assert "src_dir:/custom/path/proj/null-ptr-1-proj/src" in content
        assert "runtime_dir_pre:/custom/path/proj/null-ptr-1-proj/pre" in content
        assert "runtime_dir_repair:/custom/path/proj/null-ptr-1-proj/repair" in content


class TestFindProcedureName:
    """Tests for find_procedure_name function."""

    def test_finds_procedure_in_source(self, temp_dir, sample_c_source):
        """Test finding a procedure name in source code."""
        source_path = temp_dir / "test.c"
        source_path.write_text(sample_c_source)

        # Line 12 is inside lxc_abstract_unix_connect
        procedure = find_procedure_name(str(source_path), 12)

        assert procedure == "lxc_abstract_unix_connect"

    def test_returns_unknown_for_nonexistent_file(self):
        """Test that 'unknown' is returned for non-existent files."""
        procedure = find_procedure_name("/nonexistent/file.c", 100)

        assert procedure == "unknown"

    def test_returns_unknown_for_line_outside_functions(
        self, temp_dir, sample_c_source
    ):
        """Test that 'unknown' is returned for lines outside functions."""
        source_path = temp_dir / "test.c"
        source_path.write_text(sample_c_source)

        # Line 1 is outside any function (include statement)
        procedure = find_procedure_name(str(source_path), 1)

        assert procedure == "unknown"

    def test_finds_static_function(self, temp_dir, sample_c_source):
        """Test finding a static function."""
        source_path = temp_dir / "test.c"
        source_path.write_text(sample_c_source)

        # Line 5 is inside helper_function
        procedure = find_procedure_name(str(source_path), 5)

        assert procedure == "helper_function"

    def test_finds_void_function(self, temp_dir, sample_c_source):
        """Test finding a void function."""
        source_path = temp_dir / "test.c"
        source_path.write_text(sample_c_source)

        # Line 20 is inside another_function
        procedure = find_procedure_name(str(source_path), 20)

        assert procedure == "another_function"
