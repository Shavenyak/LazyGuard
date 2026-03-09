import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any, Tuple

def load_task(task_path: str) -> Dict[str, Any]:
    """Load the task JSON file."""
    try:
        with open(task_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading task file: {e}")
        sys.exit(1)

def check_required_files(task: Dict[str, Any], project_path: str) -> Tuple[bool, list[str]]:
    """Check if all required files exist."""
    required_files = task.get("required_files", [])
    if not required_files:
        return True, ["No required files specified."]
    
    reasons = []
    all_exist = True
    for file_path in required_files:
        full_path = os.path.join(project_path, file_path)
        if os.path.isfile(full_path):
            reasons.append(f"Required file exists: {file_path}")
        else:
            reasons.append(f"Missing required file: {file_path}")
            all_exist = False
            
    return all_exist, reasons

def check_must_contain(task: Dict[str, Any], project_path: str) -> Tuple[bool, list[str]]:
    """Check if specified files contain required text."""
    must_contain_checks = task.get("must_contain_checks", [])
    if not must_contain_checks:
        return True, ["No 'must_contain' checks specified."]
        
    reasons = []
    all_passed = True
    for check in must_contain_checks:
        file_path = check.get("file")
        text = check.get("text")
        if not file_path or not text:
            continue
            
        full_path = os.path.join(project_path, file_path)
        if not os.path.isfile(full_path):
            reasons.append(f"Cannot check content, file missing: {file_path}")
            all_passed = False
            continue
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if text in content:
                    reasons.append(f"Text '{text}' found in {file_path}")
                else:
                    reasons.append(f"Text '{text}' not found in {file_path}")
                    all_passed = False
        except Exception as e:
            reasons.append(f"Error reading contents of {file_path}: {e}")
            all_passed = False
            
    return all_passed, reasons

def run_test_command(task: Dict[str, Any], project_path: str) -> Dict[str, Any]:
    """Run the test command and capture output."""
    test_command = task.get("test_command")
    if not test_command:
        return {
            "passed": True,
            "exit_code": 0,
            "stdout": "No test command specified.",
            "stderr": "",
            "ran": False
        }
        
    try:
        # Run command securely, capturing output
        result = subprocess.run(
            test_command,
            cwd=project_path,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300 # 5 min timeout to prevent hanging
        )
        passed = (result.returncode == 0)
        return {
            "passed": passed,
            "exit_code": result.returncode,
            "stdout": (result.stdout or "")[:2000],  # capture first 2000 chars to avoid massive logs
            "stderr": (result.stderr or "")[:2000],
            "ran": True
        }
    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": "Command timed out after 300 seconds.",
            "ran": True
        }
    except Exception as e:
        return {
            "passed": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "ran": True
        }

def build_report(task: Dict[str, Any], checks: Dict[str, bool], test_result: Dict[str, Any], all_reasons: list[str]) -> Dict[str, Any]:
    """Build the final report JSON structure."""
    
    all_passed = checks["required_files"] and checks["must_contain_checks"] and test_result["passed"]
    
    status = "FAIL"
    next_action = "Return task to worker agent for correction"
    
    if all_passed:
        status = "PASS"
        next_action = "Task approved. Proceed to next task."
    elif checks["required_files"] and test_result["passed"] and not checks["must_contain_checks"]:
        # Files exist, tests pass, but didn't contain exact text
        status = "PARTIAL"
        next_action = "Review partially completed task."
        
    report = {
        "task_id": task.get("task_id", "unknown"),
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": {
            "required_files": checks["required_files"],
            "must_contain_checks": checks["must_contain_checks"],
            "tests_passed": test_result["passed"]
        },
        "test_command": task.get("test_command"),
        "test_exit_code": test_result["exit_code"],
        "test_stdout_summary": test_result["stdout"],
        "test_stderr_summary": test_result["stderr"],
        "reasons": all_reasons,
        "next_action": next_action
    }
    
    return report

def save_report(report: Dict[str, Any], output_path: str):
    """Save the report JSON to disk."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(f"Report successfully saved to {output_path}")
    except Exception as e:
        print(f"Error saving report: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python validator.py <path_to_task.json> [output_report.json]")
        sys.exit(1)
        
    task_path = sys.argv[1]
    report_path = sys.argv[2] if len(sys.argv) > 2 else "report.json"
    
    print(f"Loading task from: {task_path}")
    task = load_task(task_path)
    
    # Resolve project path relative to task json location or as absolute
    project_path = task.get("project_path", ".")
    task_dir = os.path.dirname(os.path.abspath(task_path))
    if not os.path.isabs(project_path):
        project_path = os.path.normpath(os.path.join(task_dir, project_path))
        
    print(f"Target project path: {project_path}")
    
    all_reasons = []
    checks = {}
    
    # Check 1: Files
    print("Checking required files...")
    files_passed, files_reasons = check_required_files(task, project_path)
    checks["required_files"] = files_passed
    all_reasons.extend(files_reasons)
    
    # Check 2: Content
    print("Checking file contents...")
    content_passed, content_reasons = check_must_contain(task, project_path)
    checks["must_contain_checks"] = content_passed
    all_reasons.extend(content_reasons)
    
    # Check 3: Tests
    print("Running tests...")
    test_result = run_test_command(task, project_path)
    checks["tests_passed"] = test_result["passed"]
    if test_result["ran"]:
        if test_result["passed"]:
            all_reasons.append("Test command passed.")
        else:
            all_reasons.append("Test command failed.")
    else:
        all_reasons.append("No test command executed.")
        
    print("Building report...")
    report = build_report(task, checks, test_result, all_reasons)
    
    save_report(report, report_path)
    
    # Exit code based on status for easy CI chaining
    if report["status"] == "PASS":
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
