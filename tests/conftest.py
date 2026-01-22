"""Shared test fixtures and configuration."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_infer_text_report():
    """Sample Infer text report content."""
    return """#0
hooks/unmount-namespace.c:123: error: Use After Free(USE_AFTER_FREE)
  accessing `fd` that was closed with `fclose()` on line 120.
  121. 	if (!mf) {
  122. 		int error = errno;
  123. 		close(fd);
       ^
  124. 		errno = error;
  125. 		free(mounts);

#1
src/lxc/af_unix.c:154: error: Null Dereference(NULLPTR_DEREFERENCE)
  `cmsg` could be null (null value originating from line 153) and is dereferenced.
  152.
  153. 	cmsg = CMSG_FIRSTHDR(&msg);
  154. 	cmsg->cmsg_level = SOL_SOCKET;
       ^
  155. 	cmsg->cmsg_type = SCM_RIGHTS;
  156. 	cmsg->cmsg_len = CMSG_LEN(num_sendfds * sizeof(int));

#2
src/lxc/cgroups/cgfsng.c:462: error: Memory Leak(MEMORY_LEAK_C)
  Memory dynamically allocated by `malloc` is not freed.
  460. 		ret = snprintf(numstr, LXC_NUMSTRLEN64, "%zu", i);
  461. 		if (ret < 0 || (size_t)ret >= LXC_NUMSTRLEN64) {
  462. 			lxc_free_array((void **)cpulist, free);
       ^
  463. 			return NULL;
  464. 		}
"""


@pytest.fixture
def sample_infer_json_report():
    """Sample Infer JSON report content."""
    return [
        {
            "bug_type": "NULLPTR_DEREFERENCE",
            "file": "src/lxc/af_unix.c",
            "line": 154,
            "procedure": "lxc_abstract_unix_connect",
            "bug_trace": [
                {"line_number": 150, "description": "start"},
                {"line_number": 154, "description": "null dereference"},
            ],
        },
        {
            "bug_type": "MEMORY_LEAK_C",
            "file": "src/lxc/cgroups/cgfsng.c",
            "line": 462,
            "procedure": "cg_legacy_get_hierarchies",
            "bug_trace": [
                {"line_number": 460, "description": "allocation"},
                {"line_number": 462, "description": "leak"},
            ],
        },
    ]


@pytest.fixture
def sample_bug_dict():
    """Sample parsed bug dictionary."""
    return {
        "index": 1,
        "file": "src/lxc/af_unix.c",
        "line": 154,
        "bug_type": "Null Dereference",
        "bug_type_id": "NULLPTR_DEREFERENCE",
        "description": "`cmsg` could be null and is dereferenced.",
        "code_lines": [
            {"line_num": 152, "code": ""},
            {"line_num": 153, "code": "\tcmsg = CMSG_FIRSTHDR(&msg);"},
            {"line_num": 154, "code": "\tcmsg->cmsg_level = SOL_SOCKET;"},
        ],
        "procedure": "unknown",
    }


@pytest.fixture
def sample_c_source():
    """Sample C source code for procedure detection."""
    return """#include <stdio.h>
#include <stdlib.h>

static int helper_function(void) {
    return 0;
}

int lxc_abstract_unix_connect(const char *name, int type) {
    struct sockaddr_un addr;
    int fd;

    fd = socket(AF_UNIX, type, 0);
    if (fd < 0)
        return -1;

    return fd;
}

void another_function(void) {
    printf("hello\\n");
}
"""


@pytest.fixture
def mock_container_session():
    """Create a mock ContainerSession."""
    session = MagicMock()
    session.container_id = "abc123"
    session.workdir = "/opt/effFix-benchmark"
    session.exec.return_value = "mock output"
    session.cd.return_value = "/some/path"
    return session


@pytest.fixture
def mock_subprocess_run(mocker):
    """Mock subprocess.run for Docker commands."""
    mock = mocker.patch("subprocess.run")
    mock.return_value = MagicMock(
        returncode=0, stdout="container_id\tcontainer_name\timage_name", stderr=""
    )
    return mock


@pytest.fixture
def create_report_file(temp_dir, sample_infer_text_report):
    """Create a temporary report.txt file."""
    report_path = temp_dir / "report.txt"
    report_path.write_text(sample_infer_text_report)
    return report_path


@pytest.fixture
def create_json_report_file(temp_dir, sample_infer_json_report):
    """Create a temporary report.json file."""
    report_path = temp_dir / "report.json"
    report_path.write_text(json.dumps(sample_infer_json_report))
    return report_path


@pytest.fixture
def create_project_structure(temp_dir):
    """Create a mock project directory structure."""

    def _create(project_name, cases):
        project_dir = temp_dir / project_name
        for case_name in cases:
            case_dir = project_dir / case_name
            efffix_dir = case_dir / "EffFix"
            efffix_dir.mkdir(parents=True)

            config_content = f"""tag_id:{case_name}
config_command:./configure
build_command:make -j4
build_command_repair:make -j4
clean_command:make clean
src_dir:/path/to/{case_name}/src
bug_type:NULLPTR_DEREFERENCE
bug_file:src/file.c
bug_procedure:some_function
bug_start_line:100
bug_end_line:100
runtime_dir_pre:/path/to/{case_name}/pre
runtime_dir_repair:/path/to/{case_name}/repair
"""
            (efffix_dir / "repair.conf").write_text(config_content)
        return project_dir

    return _create
