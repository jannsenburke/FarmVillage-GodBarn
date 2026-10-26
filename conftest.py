"""Report tests that need the private original game inputs as UNRUN.

A public clone does not contain the original 2009 game files listed in
PrivateInputs.expected.json. Tests that read them would otherwise crash with
FileNotFoundError and look like bugs. Here they are reported as skipped with an
"UNRUN: needs private input" reason, so PASS, FAIL and UNRUN stay separate.
Any other missing file still fails normally.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
# Documented as external/private and absent from this source export.
EXTERNAL_REFERENCES = {"FarmVillage/macOS/Documentation/MECHANICS_RELEASE.md"}


def _private_paths():
    try:
        files = json.loads((ROOT / "PrivateInputs.expected.json").read_text())["files"]
    except (OSError, ValueError, KeyError):
        return set(EXTERNAL_REFERENCES)
    return set(files) | EXTERNAL_REFERENCES


PRIVATE = _private_paths()
MISSING = re.compile(r"(?:FileNotFoundError|NotADirectoryError): \[Errno 2\] No such file or directory: '([^']+)'")


def _private_input(text):
    for match in MISSING.finditer(text):
        try:
            relative = Path(match.group(1)).resolve().relative_to(ROOT).as_posix()
        except ValueError:
            continue
        if relative in PRIVATE and not (ROOT / relative).exists():
            return relative
    return None


def _as_unrun(report, path):
    report.outcome = "skipped"
    location = str(getattr(report, "fspath", "") or report.nodeid)
    report.longrepr = (location, 0, "UNRUN: needs private input " + path)


@pytest.hookimpl(hookwrapper=True)
def pytest_make_collect_report(collector):
    outcome = yield
    report = outcome.get_result()
    if report.failed:
        path = _private_input(str(report.longrepr))
        if path:
            _as_unrun(report, path)
            report.result = []


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.failed and call.excinfo is not None and call.excinfo.errisinstance(OSError):
        path = _private_input(str(report.longrepr))
        if path:
            _as_unrun(report, path)
