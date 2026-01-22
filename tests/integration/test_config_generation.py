"""Integration tests for config generation workflow."""

import json
import pytest
from pathlib import Path

from algorithm.report_to_config import (
    create_config_content,
    filter_supported_bugs,
    generate_tag_id,
    parse_report,
)


class TestConfigGenerationWorkflow:
    """End-to-end tests for config generation."""

    def test_full_workflow_from_text_report(self, fixtures_dir):
        """Test complete workflow from text report to config."""
        report_path = fixtures_dir / "sample_report.txt"

        # Parse report
        bugs = parse_report(str(report_path))
        assert len(bugs) == 3

        # Filter bugs
        null_ptr_bugs = filter_supported_bugs(bugs, "NULLPTR_DEREFERENCE")
        assert len(null_ptr_bugs) == 1

        # Generate tag
        bug = null_ptr_bugs[0]
        tag_id = generate_tag_id(bug["bug_type_id"], 1, "test-project")
        assert tag_id == "null-ptr-1-test-project"

        # Create config
        bug["procedure"] = "test_function"
        config = create_config_content(
            bug=bug,
            tag_id=tag_id,
            subject="test-project",
            container_base="/opt/effFix-benchmark",
            config_cmd="./configure",
            build_cmd="make -j4",
            build_cmd_repair="make -j4",
            clean_cmd="make clean",
            pulse_args="",
        )

        # Verify config format
        lines = config.strip().split("\n")
        config_dict = {}
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                config_dict[key] = value

        assert config_dict["tag_id"] == "null-ptr-1-test-project"
        assert config_dict["bug_type"] == "NULLPTR_DEREFERENCE"
        assert config_dict["bug_file"] == "src/lxc/af_unix.c"

    def test_generates_unique_tags_for_multiple_bugs(self, temp_dir):
        """Test that multiple bugs get unique tag IDs."""
        report_content = """#0
src/file1.c:100: error: Null Dereference(NULLPTR_DEREFERENCE)
  null pointer
  99. 	ptr = NULL;
  100. 	ptr->x = 1;
       ^

#1
src/file2.c:200: error: Null Dereference(NULLPTR_DEREFERENCE)
  null pointer
  199. 	ptr = NULL;
  200. 	ptr->y = 2;
       ^
"""
        report_path = temp_dir / "multi_bugs.txt"
        report_path.write_text(report_content)

        bugs = parse_report(str(report_path))
        bugs = filter_supported_bugs(bugs, "NULLPTR_DEREFERENCE")

        tags = []
        for i, bug in enumerate(bugs, 1):
            tag = generate_tag_id(bug["bug_type_id"], i, "project")
            tags.append(tag)

        # All tags should be unique
        assert len(tags) == len(set(tags))
        assert tags[0] == "null-ptr-1-project"
        assert tags[1] == "null-ptr-2-project"

    def test_workflow_with_different_bug_types(self, temp_dir):
        """Test workflow filtering different bug types."""
        report_content = """#0
src/file1.c:100: error: Use After Free(USE_AFTER_FREE)
  use after free
  99. 	free(ptr);
  100. 	ptr->x = 1;
       ^

#1
src/file2.c:200: error: Null Dereference(NULLPTR_DEREFERENCE)
  null pointer
  199. 	ptr = NULL;
  200. 	ptr->y = 2;
       ^

#2
src/file3.c:300: error: Memory Leak(MEMORY_LEAK_C)
  memory leak
  299. 	ptr = malloc(10);
  300. 	return;
       ^
"""
        report_path = temp_dir / "mixed_bugs.txt"
        report_path.write_text(report_content)

        # Parse all bugs
        all_bugs = parse_report(str(report_path))
        assert len(all_bugs) == 3

        # Filter for each type
        uaf_bugs = filter_supported_bugs(all_bugs, "USE_AFTER_FREE")
        null_bugs = filter_supported_bugs(all_bugs, "NULLPTR_DEREFERENCE")
        leak_bugs = filter_supported_bugs(all_bugs, "MEMORY_LEAK_C")

        assert len(uaf_bugs) == 1
        assert len(null_bugs) == 1
        assert len(leak_bugs) == 1

        # Generate unique tags for each type
        uaf_tag = generate_tag_id("USE_AFTER_FREE", 1, "proj")
        null_tag = generate_tag_id("NULLPTR_DEREFERENCE", 1, "proj")
        leak_tag = generate_tag_id("MEMORY_LEAK_C", 1, "proj")

        assert uaf_tag == "use-after-free-1-proj"
        assert null_tag == "null-ptr-1-proj"
        assert leak_tag == "memory-leak-1-proj"

    def test_config_paths_are_consistent(self, temp_dir):
        """Test that config paths are consistent throughout."""
        report_content = """#0
src/test.c:100: error: Null Dereference(NULLPTR_DEREFERENCE)
  null pointer
  99. 	ptr = NULL;
  100. 	ptr->x = 1;
       ^
"""
        report_path = temp_dir / "test.txt"
        report_path.write_text(report_content)

        bugs = parse_report(str(report_path))
        bug = bugs[0]
        bug["procedure"] = "test_func"

        tag_id = "null-ptr-1-myproj"
        # container_base is the root, subject is added in create_config_content
        container_base = "/opt/effFix-benchmark"

        config = create_config_content(
            bug=bug,
            tag_id=tag_id,
            subject="myproj",
            container_base=container_base,
            config_cmd="./configure",
            build_cmd="make",
            build_cmd_repair="make",
            clean_cmd="make clean",
            pulse_args="",
        )

        # All paths should use the same base: {container_base}/{subject}/{tag_id}
        expected_base = f"{container_base}/myproj/{tag_id}"
        assert f"src_dir:{expected_base}/src" in config
        assert f"runtime_dir_pre:{expected_base}/pre" in config
        assert f"runtime_dir_repair:{expected_base}/repair" in config


class TestProjectDiscoveryIntegration:
    """Integration tests for project case discovery."""

    def test_discovers_cases_from_directory(self, temp_dir, create_project_structure):
        """Test discovering cases from generated_configs directory."""
        # Create a project structure with multiple cases
        create_project_structure(
            "lxc", ["null-ptr-1-lxc", "null-ptr-2-lxc", "null-ptr-3-lxc"]
        )

        from algorithm.components.run_project import get_project_cases

        with patch_generated_configs_dir(temp_dir):
            cases = get_project_cases("lxc")

        assert len(cases) == 3
        assert "null-ptr-1-lxc" in cases
        assert "null-ptr-2-lxc" in cases
        assert "null-ptr-3-lxc" in cases


def patch_generated_configs_dir(temp_dir):
    """Context manager to patch GENERATED_CONFIGS_DIR."""
    from unittest.mock import patch

    return patch(
        "algorithm.components.run_project.GENERATED_CONFIGS_DIR", str(temp_dir)
    )
