import subprocess
import os

from algorithm.regen_configs_from_pre import regenerate_case
from algorithm.projects.registry import get_project_config
from algorithm.projects.base import ConfigSource

# Paths for git-based projects (volume mounted)
BENCHMARK_ROOT_VOLUME = "/opt/effFix-benchmark"
EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "export")


def run_case(session, project_name, case_name, repair_only=False):
    """Run effFix repair on a specific case and export results.

    Args:
        session: Container session
        project_name: Name of the project
        case_name: Name of the case
        repair_only: If True, only run repair stage (skip pre-analysis and regen)

    Full workflow (repair_only=False):
    1. Pre-analysis: Run Infer to discover bugs
    2. Regen: Update config with correct bug locations
    3. Repair: Run effFix repair

    Repair-only workflow (repair_only=True):
    1. Repair: Run effFix repair directly (assumes config is already correct)
    """
    print(f"\n{'='*60}")
    print(f"CASE: {project_name}/{case_name}")
    if repair_only:
        print("MODE: repair-only")
    print(f"{'='*60}")

    # Handle fake project for testing
    if project_name == "fake":
        run_fake_case(session)
        return {"status": "success", "case": case_name}

    # Get project config to determine paths
    project_config = get_project_config(project_name)
    if not project_config:
        print(f"Error: Unknown project: {project_name}")
        return {"status": "failed", "case": case_name, "stage": "config"}

    # Determine paths based on config_source
    if project_config.config_source == ConfigSource.CONTAINER:
        # Container-based: configs exist in container at benchmark path
        # Path: /opt/effFix-benchmark/{project}/{case}/
        benchmark_path = project_config.container_benchmark_path
        case_path = f"{benchmark_path}/{project_name}/{case_name}"
        config_path = f"{case_path}/EffFix/repair.conf"
        data_path = case_path
        session.cd(case_path)
    else:
        # Git-based (GENERATE): volume mounted with EffFix/repair.conf structure
        case_path = f"{BENCHMARK_ROOT_VOLUME}/{project_name}/{case_name}"
        config_path = f"{case_path}/EffFix/repair.conf"
        data_path = case_path
        session.cd(case_path)

    # Show diagnostic info
    print("\n--- Diagnostic Info ---")
    print(f"Working directory: {data_path}")
    session.exec("pwd")
    print("\nDirectory contents:")
    session.exec("ls -la")
    print(f"\nEffFix config: {config_path}")
    session.exec(f"cat {config_path}")

    if repair_only:
        # Repair-only mode: skip pre-analysis and regen
        print("\n--- Cleaning up previous repair ---")
        session.exec("rm -rf repair")

        # Run repair directly
        print("\n--- Repair ---")
        print(f"Command: effFix --stage repair {config_path} --budget 3")
        result = session.exec(f"effFix --stage repair {config_path} --budget 3", stream=True)
    else:
        # Full workflow
        # Clean up previous directories
        print("\n--- Cleaning up previous runs ---")
        session.exec("rm -rf repair pre")

        # Phase 1: Pre-analysis
        print("\n--- Phase 1: Pre-analysis ---")
        print(f"Command: effFix --stage pre {config_path}")
        pre_result = session.exec(f"effFix --stage pre {config_path}", stream=True)

        if not pre_result:
            print("\n[FAILED] Pre-analysis stage failed")
            export_results(session.container_id, project_name, case_name, data_path)
            return {"status": "failed", "case": case_name, "stage": "pre"}

        # Phase 2: Regenerate config
        print("\n--- Phase 2: Regenerate Config ---")
        if not regenerate_case(project_name, case_name):
            print("\n[FAILED] No matching bugs found by Infer")
            export_results(session.container_id, project_name, case_name, data_path)
            return {"status": "failed", "case": case_name, "stage": "regen"}

        print("\nUpdated config:")
        session.exec(f"cat {config_path}")

        # Phase 3: Repair
        print("\n--- Phase 3: Repair ---")
        print(f"Command: effFix --stage repair {config_path} --budget 3")
        result = session.exec(f"effFix --stage repair {config_path} --budget 3", stream=True)

    # Export results
    print("\n--- Exporting Results ---")
    export_results(session.container_id, project_name, case_name, data_path)

    status = "success" if result else "failed"
    print(f"\n[{status.upper()}] {project_name}/{case_name}")
    return {"status": status, "case": case_name}


def export_results(container_id, project_name, case_name, case_path):
    """Export repair results from container to local export folder."""
    export_path = os.path.join(EXPORT_DIR, project_name, case_name)
    os.makedirs(export_path, exist_ok=True)

    # Export EffFix config from generated_configs (local)
    generated_configs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "generated_configs"
    )
    local_config_path = os.path.join(generated_configs_dir, project_name, case_name, "EffFix", "repair.conf")
    if os.path.exists(local_config_path):
        efffix_export_path = os.path.join(export_path, "EffFix")
        os.makedirs(efffix_export_path, exist_ok=True)
        subprocess.run(["cp", local_config_path, efffix_export_path], capture_output=True)
        print(f"Exported config: {efffix_export_path}/repair.conf")

    # Export repair folder if it exists (from container)
    container_repair_path = f"{case_path}/repair"
    result = subprocess.run(
        ["docker", "exec", container_id, "test", "-d", container_repair_path],
        capture_output=True
    )
    if result.returncode == 0:
        subprocess.run(
            ["docker", "cp", f"{container_id}:{container_repair_path}/.", export_path],
            capture_output=True
        )
        print(f"Exported repair: {export_path}")

    # Export pre folder if it exists (from container)
    container_pre_path = f"{case_path}/pre"
    result = subprocess.run(
        ["docker", "exec", container_id, "test", "-d", container_pre_path],
        capture_output=True
    )
    if result.returncode == 0:
        pre_export_path = os.path.join(export_path, "pre")
        os.makedirs(pre_export_path, exist_ok=True)
        subprocess.run(
            ["docker", "cp", f"{container_id}:{container_pre_path}/.", pre_export_path],
            capture_output=True
        )
        print(f"Exported pre: {pre_export_path}")


def run_fake_case(session):
    """Run a fake case for testing."""
    session.exec("echo 'Step 1: Initializing...' && sleep 1")
    session.exec("echo 'Step 2: Analyzing...' && sleep 1")
    session.exec("echo 'Step 3: Repairing...' && sleep 1")
    session.exec("echo 'Step 4: Done!'")
