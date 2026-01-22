# Claude Code Guide for infer-report-to-efffix-repair

## Project Overview

This project automates bug repair workflows using Infer static analysis reports and the EffFix repair tool. It parses Infer reports, generates EffFix configuration files, and orchestrates the repair process inside Docker containers.

## Architecture

### Two-Tier Project Configuration

Projects are configured with two key enums:

1. **ConfigSource** - Where case configurations come from:
   - `CONTAINER`: Pre-existing configs inside the container (e.g., openssl-1, openssl-3)
   - `GENERATE`: Generated from `algorithm/input/<project>/report.txt` (e.g., lxc, x264)

2. **CodeSource** - Where source code comes from:
   - `CONTAINER`: Source already exists in container
   - `GIT`: Clone from git repository

### Three-Stage Repair Workflow

Each case runs through these stages:
1. **pre**: Pre-analysis with Infer (generates `pre/infer-out-whole/`)
2. **regen**: Regenerate config from Infer's JSON output
3. **repair**: Run EffFix repair on the target file

## Key Directories

```
algorithm/
  input/<project>/report.txt     # Infer text reports for GENERATE projects
  projects/                      # Project configurations (registry.py, base.py)
  components/                    # Core workflow components (run_case.py, run_project.py)
  utils/                         # Utilities (exec_in_container.py, container/)

generated_configs/<project>/     # Generated case configs (for GENERATE projects)
  <case>/
    EffFix/repair.conf          # EffFix configuration
    src/                        # Source code copy
    pre/                        # Pre-analysis output

export/<project>/<case>/        # Output artifacts from repair runs
tests/                          # pytest test suite
```

## Key Files

- [main.py](main.py) - CLI entry point
- [algorithm/run_efffix.py](algorithm/run_efffix.py) - Main orchestration
- [algorithm/projects/base.py](algorithm/projects/base.py) - `ProjectConfig` dataclass
- [algorithm/projects/registry.py](algorithm/projects/registry.py) - Project lookup
- [algorithm/components/run_case.py](algorithm/components/run_case.py) - Case execution
- [algorithm/utils/exec_in_container.py](algorithm/utils/exec_in_container.py) - Docker command execution via `ContainerSession`
- [algorithm/report_to_config.py](algorithm/report_to_config.py) - Parse Infer reports

## Common Commands

```bash
# Run all cases for a project
python main.py lxc

# Run a specific case
python main.py lxc/null-ptr-1-lxc

# Start new container with volume mount
python main.py -s lxc

# Repair-only mode (skip pre-analysis)
python main.py -r openssl-1

# Generate configs from report.txt
python main.py -s lxc --generate-config

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest --cov=algorithm --cov-report=term-missing
```

## Adding a New Project

1. Create project config in `algorithm/projects/<project>.py`:
```python
from algorithm.projects.base import ProjectConfig, ConfigSource, CodeSource

PROJECT_CONFIG = ProjectConfig(
    name="myproject",
    config_source=ConfigSource.GENERATE,  # or CONTAINER
    code_source=CodeSource.GIT,           # or CONTAINER
    git_repo="https://github.com/org/repo.git",
    git_commit="abc123",
    config_cmd="./configure",
    build_cmd="make -j4",
    build_cmd_repair="make -j4",
    clean_cmd="make clean || true",
)
```

2. Register in `algorithm/projects/registry.py`:
```python
from algorithm.projects.myproject import PROJECT_CONFIG as MYPROJECT_CONFIG

PROJECT_CONFIGS = {
    # ... existing projects
    "myproject": MYPROJECT_CONFIG,
}
```

3. For GENERATE projects, add `algorithm/input/myproject/report.txt` with Infer output

## Container Paths

The container benchmark path is `/opt/effFix-benchmark`. This is where:
- CONTAINER projects have their cases (e.g., `/opt/effFix-benchmark/openssl-1/null-ptr-1/`)
- Volume-mounted GENERATE projects are mapped

## Testing

Tests use pytest with pytest-mock for mocking Docker/subprocess calls:
- Unit tests: `tests/unit/` - Test individual functions with mocks
- Integration tests: `tests/integration/` - Test workflows with fixture files
- Coverage threshold: 60% (configured in pyproject.toml)

Key fixtures are in `tests/conftest.py`:
- `mock_container_session` - Mocked ContainerSession
- `sample_bug_dict` - Sample parsed bug dictionary
- `temp_dir` - Temporary directory for test files

## Code Style Notes

- Docker commands are executed via `ContainerSession.exec()` which:
  - Uses `bash -c` for commands
  - Maintains working directory state via `cd()` method
  - Supports streaming output with `stream=True`
  - Supports silent capture with `capture=True`
- All container paths should use `/opt/effFix-benchmark` as the base
- Use colored output via constants in exec_in_container.py (GREEN, RED, GRAY, RESET)
