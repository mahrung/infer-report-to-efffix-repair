# Infer Report to EffFix Repair

Runs EffFix repairs on Docker containers using Infer static analysis reports.

## Usage

```bash
# Run all cases for a project (uses first running container)
python main.py lxc

# Run a specific case
python main.py lxc/null-ptr-1-lxc

# Start a new container with volume mount
python main.py -s openssl-1

# Repair-only mode (skip pre-analysis, use existing config)
python main.py -r openssl-1
python main.py --repair-only openssl-3/null-ptr-6-openssl-3
```

## Project Structure

```text
algorithm/input/<project>/report.txt  # Infer reports (auto-generates cases)
generated_configs/<project>/<case>/   # Generated EffFix configs
```

## Adding Projects

**Option 1:** Add `algorithm/input/<project>/report.txt` with Infer output

**Option 2:** Hardcode cases in `algorithm/components/run_project.py`:

```python
KNOWN_PROJECT_CASES = {
    "openssl-1": ["null-ptr-1", "null-ptr-2", ...],
}
```

## Available Projects

- `lxc` - null-ptr cases from report.txt
- `openssl-1` - null-ptr-1 to null-ptr-5 (hardcoded, container-based)
- `openssl-3` - null-ptr-1 to null-ptr-3 (hardcoded, container-based)
