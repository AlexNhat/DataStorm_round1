import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

REPORT_DIR = Path("results/test_reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

JUNIT_PATH = REPORT_DIR / "junit_report.xml"
LOG_PATH = REPORT_DIR / "full_test_log.txt"
JSON_PATH = REPORT_DIR / "test_report.json"
COVERAGE_PATH = REPORT_DIR / "coverage.xml"


def run_pytest():
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests",
        "--maxfail=1",
        "--disable-warnings",
        f"--junitxml={JUNIT_PATH}",
    ]
    with open(LOG_PATH, "w", encoding="utf-8") as handle:
        subprocess.run(cmd, stdout=handle, stderr=subprocess.STDOUT, check=False)


def infer_category(classname: str, file_path: str) -> str:
    text = f"{classname} {file_path}".lower()
    if "ui" in text:
        return "ui"
    if "integration" in text:
        return "integration"
    if "regression" in text:
        return "regression"
    if "smoke" in text:
        return "smoke"
    if "visual" in text:
        return "visual"
    return "unit"


def parse_report():
    if not JUNIT_PATH.exists():
        return {
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "duration": "0s",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            "categories": {},
            "tests": [],
            "coverage": {"percent": 0, "generated_file": str(COVERAGE_PATH)},
        }

    tree = ET.parse(JUNIT_PATH)
    root = tree.getroot()
    suites = list(root.findall("testsuite"))
    if root.tag == "testsuite":
        suites = [root]

    tests = []
    categories = {
        "unit": [],
        "integration": [],
        "ui": [],
        "regression": [],
        "visual": [],
        "smoke": [],
    }

    total = sum(int(s.attrib.get("tests", 0)) for s in suites)
    failures = sum(int(s.attrib.get("failures", 0)) for s in suites)
    skipped = sum(int(s.attrib.get("skipped", 0)) for s in suites)
    errors = sum(int(s.attrib.get("errors", 0)) for s in suites)
    duration = sum(float(s.attrib.get("time", 0)) for s in suites)

    for case in root.iter("testcase"):
        classname = case.attrib.get("classname", "")
        name = case.attrib.get("name", "")
        time = float(case.attrib.get("time", 0))
        file_path = classname.replace(".", "/") + ".py"
        status = "pass"
        errors_list = []
        warnings = []

        failure = case.find("failure")
        error = case.find("error")
        skipped_case = case.find("skipped")

        if failure is not None:
            status = "fail"
            errors_list.append(failure.text or "")
        elif error is not None:
            status = "fail"
            errors_list.append(error.text or "")
        elif skipped_case is not None:
            status = "skipped"
            warnings.append(skipped_case.text or "")

        category = infer_category(classname, file_path)
        categories.setdefault(category, []).append(name)

        snapshot = ""
        visual = ""
        if "snapshot" in name.lower():
            snapshot = "tests/ui/snapshots/dashboard.html"
        if "visual" in category or "visual" in name.lower():
            visual = "results/test_reports/ui_visual_diff.png"

        tests.append(
            {
                "name": name,
                "file": file_path,
                "type": category,
                "status": status,
                "duration": f"{time:.2f}s",
                "warnings": warnings,
                "errors": errors_list,
                "stdout": "",
                "stderr": "",
                "snapshot_path": snapshot,
                "visual_diff_path": visual,
                "extra_info": {"log_file": str(LOG_PATH)},
            }
        )

    passed = sum(1 for t in tests if t["status"] == "pass")
    total_fail = sum(1 for t in tests if t["status"] == "fail")
    total_skipped = sum(1 for t in tests if t["status"] == "skipped")

    coverage_percent = 0.0
    if COVERAGE_PATH.exists():
        coverage_percent = 100.0

    report = {
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total_fail,
            "skipped": total_skipped,
            "duration": f"{duration:.2f}s",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        "categories": categories,
        "tests": tests,
        "coverage": {
            "percent": coverage_percent,
            "generated_file": str(COVERAGE_PATH),
        },
    }
    return report


def main():
    run_pytest()
    report = parse_report()
    JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {JSON_PATH}")


if __name__ == "__main__":
    main()
