#!/usr/bin/env python3
"""Read-only player readiness guide; not a complete download-and-play installer."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_BYTES = 19_126_111_395
GUIDES = {"mac": "docs/PLAY_ON_MAC.md", "server": "docs/PLAY_ON_SERVER.md"}

class RefusedInput(ValueError):
    pass

def ordinary_root(value):
    path = Path(value)
    if ".." in path.parts:
        raise RefusedInput("Choose the exact ordinary source folder without parent-directory traversal.")
    root = path.absolute()
    if any(p.is_symlink() for p in (root, *root.parents)):
        raise RefusedInput("The selected source folder or an ancestor is a symbolic link.")
    if not root.is_dir():
        raise RefusedInput("The selected source folder is missing or is not a directory.")
    return root

def relative_file(name):
    if not isinstance(name, str) or not name or "\\" in name:
        raise RefusedInput("Invalid relative resource path.")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise RefusedInput("A manifest resource path escapes the selected source folder.")
    if any(part in {".git", ".ssh", ".aws", "Keychains", ".lan-server", "saves", "workspace", "snapshots", "history", ".venv"} for part in path.parts):
        raise RefusedInput("Player state, account data and private workspaces are not prepared resource inputs.")
    return path

@contextmanager
def ordinary_file(root, name):
    """Read one named regular file; never follow relative component symlinks."""
    path = relative_file(name)
    directories, descriptor = [], None
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        current = os.open(root, flags | getattr(os, "O_DIRECTORY", 0))
        directories.append(current)
        for part in path.parts[:-1]:
            current = os.open(part, flags | getattr(os, "O_DIRECTORY", 0), dir_fd=current)
            directories.append(current)
        descriptor = os.open(path.parts[-1], flags, dir_fd=current)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise RefusedInput("The resource is not an ordinary file.")
        stream = os.fdopen(descriptor, "rb")
        descriptor = None
        with stream:
            yield stream
    except OSError as error:
        if error.errno in {errno.ELOOP, errno.ENOTDIR}:
            raise RefusedInput("The resource is linked or has a non-directory parent.") from error
        raise
    finally:
        if descriptor is not None:
            os.close(descriptor)
        for directory in reversed(directories):
            os.close(directory)

def group_name(name):
    for prefix, group in [
        ("FarmVillage/ruffle_runtime/", "Pinned local Ruffle player"),
        ("FarmVillage/macOS/Resources/", "Native macOS interface resources"),
        ("FarmVillage/macOS/Tests/", "Resource-dependent test fixtures"),
        ("FarmVillage/templates/", "Original browser interface resources"),
        ("FarmVillage/villages/", "Original starter templates"),
        ("GodBarn/data/", "God Barn metadata"),
        ("GodBarn/static/", "God Barn interface resources")]:
        if name.startswith(prefix):
            return group
    return "Original client and configuration" if name.startswith("FarmVillage/") else "Other prepared resources"

def resource_report(root):
    result = {"status": "manifest-unavailable", "scope": "Shared prepared-source compatibility set, not a minimal player download list", "expected_files": 0, "expected_bytes": 0,
              "matching_files": 0, "missing_files": 0, "mismatched_files": 0,
              "refused_files": 0, "unreadable_files": 0, "groups": {}, "errors": []}
    try:
        with ordinary_file(root, "PrivateInputs.expected.json") as stream:
            document = json.load(stream)
        if not isinstance(document, dict):
            raise ValueError("The prepared-resource manifest must be an object.")
        files = document.get("files")
        if document.get("schema") != 1 or not isinstance(files, dict) or not files:
            raise ValueError("The prepared-resource manifest is empty or unsupported.")
        for name, identity in files.items():
            if relative_file(name).parts[0] not in {"FarmVillage", "GodBarn"}:
                raise RefusedInput("A manifest resource is outside the two game components.")
            if not isinstance(identity, dict) or type(identity.get("bytes")) is not int or identity["bytes"] < 0:
                raise ValueError("Invalid resource byte count in the manifest.")
            if not isinstance(identity.get("sha256"), str) or not re.fullmatch(r"[0-9a-fA-F]{64}", identity["sha256"]):
                raise ValueError("Invalid resource SHA-256 identity in the manifest.")
        result["expected_files"] = len(files)
        result["expected_bytes"] = sum(x["bytes"] for x in files.values())
        for name, identity in sorted(files.items()):
            group = result["groups"].setdefault(group_name(name), {"expected": 0, "matching": 0,
                "missing": 0, "mismatched": 0, "refused": 0, "unreadable": 0, "problem_examples": []})
            group["expected"] += 1
            problem = None
            try:
                with ordinary_file(root, name) as stream:
                    if os.fstat(stream.fileno()).st_size != identity["bytes"]:
                        problem = "mismatched"
                    else:
                        digest = hashlib.sha256()
                        for block in iter(lambda: stream.read(1024 * 1024), b""):
                            digest.update(block)
                        if digest.hexdigest() != identity["sha256"].lower():
                            problem = "mismatched"
            except FileNotFoundError:
                problem = "missing"
            except RefusedInput:
                problem = "refused"
            except OSError:
                problem = "unreadable"
            if problem:
                group[problem] += 1
                result[problem + "_files"] += 1
                if len(group["problem_examples"]) < 3:
                    group["problem_examples"].append({"path": name, "problem": problem})
            else:
                group["matching"] += 1
                result["matching_files"] += 1
        result["status"] = "complete" if result["matching_files"] == len(files) else "incomplete"
    except (OSError, ValueError, TypeError) as error:
        result["errors"].append(str(error) if isinstance(error, ValueError) else "The resource manifest cannot be read as an ordinary file.")
    return result

def build_report(source_root, audience="mac"):
    if audience not in GUIDES:
        raise ValueError("Choose the mac or server audience.")
    root = ordinary_root(source_root)
    resources = resource_report(root)
    system = platform.system()
    version = platform.mac_ver()[0] if system == "Darwin" else ""
    try:
        mac_supported = system == "Darwin" and tuple(int(x) for x in version.split(".")[:2]) >= (14,)
    except ValueError:
        mac_supported = False
    return {"schema": 1, "audience": audience, "status": "not-ready", "guide_only": True,
        "source_root": str(root), "play_ready": False,
        "public_bootstrap": {"implemented": False, "status": "unfinished"},
        "prepared_resource_inputs_match": resources["status"] == "complete", "resource_inputs": resources,
        "platform": {"system": system, "python_version": platform.python_version(), "project_python_minimum": "3.10",
                     "python_supported": sys.version_info >= (3, 10), "macos_version": version or None,
                     "macos_14_or_newer": mac_supported,
                     "audience_platform_matches": mac_supported if audience == "mac" else system == "Linux",
                     "xcode_sdk_or_ubuntu_service_check": "not run"},
        "storage": {"archive_bytes": ARCHIVE_BYTES, "archive_gib": round(ARCHIVE_BYTES / 1024 ** 3, 2),
                    "exact_peak_known": False, "disk_space_checked": False,
                    "additional_space": "Extracted artwork, temporary extraction, Python environments and build products need additional space."},
        "download_plan": {"archive_source": "https://archive.org/download/original-farmville/", "archive_count": 4,
            "mac_prepare": "A complete app installs pinned packages from PyPI and copies its bundled LOCAL reviewed Ruffle player. Prepare does not download game-art archives.",
            "mac_first_create_or_open": "A complete prepared app can download and extract four original Internet Archive WARCs when artwork is missing. Original client and companion inputs must already be bundled.",
            "server_owner": "The Ubuntu installer needs a prepared release bundle and already-extracted artwork. It may fetch Python packages from PyPI; it does not fetch the original game-art archives.",
            "browser_players": "Browser players visiting a prepared server do not install the full archive collection; game resources are served by that server as needed."},
        "data_paths": {"mac_app_default": "~/Library/Application Support/FarmVillage",
                       "server": "The owner chooses a clearly named managed installation on the Ubuntu host.",
                       "checked_by_this_guide": "Only the explicit source folder and manifest-named resources; no personal folders are searched."},
        "actions_this_guide": {"downloads": False, "installs": False, "builds": False,
                              "creates_environment_or_cache": False, "reads_accounts_or_credentials": False,
                              "scans_personal_folders": False},
        "guide": GUIDES[audience], "active_worlds": 16, "excluded_worlds": ["glen", "hlights"],
        "ios_development": "discontinued"}

def print_report(report):
    print("\nFarmVillage — " + ("Mac players" if report["audience"] == "mac" else "Ubuntu server owners and browser players") + "\n")
    print("This is a READINESS GUIDE, not a completed game installer.")
    print("The public download-and-play setup is unfinished. This guide does not download, install or build anything.")
    print("\nStep 1 of 4 — What you downloaded\nA source checkout is not a ready-built FarmVillage.app or a complete server release.")
    print("\nStep 2 of 4 — Check this selected source folder")
    resources = report["resource_inputs"]
    print("This is the shared source-resource manifest; some entries serve native builds or tests, not a minimal player download list.")
    print("Prepared resource identities matching: %d/%d." % (resources["matching_files"], resources["expected_files"]))
    for name, group in sorted(resources["groups"].items()):
        print("  %s: %d/%d match; %d missing, %d different, %d refused, %d unreadable." % (name, group["matching"], group["expected"], group["missing"], group["mismatched"], group["refused"], group["unreadable"]))
        for example in group["problem_examples"]:
            print("    %s: %s" % (example["problem"], example["path"]))
    for error in resources["errors"]:
        print("  " + error)
    if report["prepared_resource_inputs_match"]:
        print("Matching prepared inputs are present. This does not prove an app build, complete installation or gameplay.")
    else:
        print("Missing prepared resources cannot yet be generated by a complete public bootstrap in this source release.")
    host = report["platform"]
    print("Python %s; project runtime needs Python 3.10+." % host["python_version"])
    print("macOS 14+ and full Xcode/SDK are needed for native developer builds; no developer tool was launched." if report["audience"] == "mac" else "Hosting needs Ubuntu/Linux. A systemd session and actual Ubuntu installation have not been checked.")
    if not host["audience_platform_matches"]:
        print("This host does not establish the selected audience's platform prerequisite.")
    print("\nStep 3 of 4 — Downloads, storage and locations")
    plan = report["download_plan"]
    if report["audience"] == "mac":
        print("Prepare Runtime: " + plan["mac_prepare"])
        print("First Create/Open after preparation: " + plan["mac_first_create_or_open"])
        print("The complete app's default data folder is " + report["data_paths"]["mac_app_default"] + ". This guide has not opened it.")
    else:
        print("Server owner: " + plan["server_owner"])
        print(plan["browser_players"])
        print(report["data_paths"]["server"])
    print("Original archives: %s bytes (%s GiB), before extracted artwork and temporary files." % (format(ARCHIVE_BYTES, ","), report["storage"]["archive_gib"]))
    print("Extracted artwork and temporary space are additional; the exact total peak is not qualified. No free-space check or download was performed.")
    print("\nStep 4 of 4 — Supported next steps")
    print("Read " + report["guide"] + " and docs/RESOURCE_SETUP.md for the original public sources and missing work.")
    print("Setup stops before any download, build or installation. It will not ask for files from the project owner's computer or server.")

def read_guide(root, audience):
    with ordinary_file(root, GUIDES[audience]) as stream:
        print(stream.read().decode("utf-8"))

def run_source_check(root):
    with ordinary_file(root, "tools/check-source.py"):
        pass
    environment = {key: value for key, value in os.environ.items() if key not in {"BASH_ENV", "ENV"} and not key.startswith(("PYTHON", "PIP_"))}
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run([sys.executable, "-I", "-S", "-B", str(root / "tools/check-source.py"), "--root", str(root)], cwd=root, env=environment, check=False).returncode

def interactive(root, audience, input_fn):
    while True:
        print("\n1. Read the local player guide\n2. Check source files (no game download or install)\n3. Close this guide")
        try:
            choice = input_fn("Choose 1, 2 or 3: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGuide closed. No installation was started.")
            return
        if choice == "3":
            print("Guide closed. The game is not installed by this guide.")
            return
        if choice == "1":
            try:
                read_guide(root, audience)
            except (OSError, ValueError, UnicodeError):
                print("The local guide is missing, linked or unreadable. Open its copy in your source download.")
        elif choice == "2":
            print("You selected the source check. This checks code and documentation; it does not install the game.")
            try:
                code = run_source_check(root)
                print("Source check passed. Game installation remains unfinished." if code == 0 else "Source check failed. Read its named source/documentation issue; game installation remains unfinished.")
            except (OSError, ValueError):
                print("The local source checker is missing, linked or could not run.")
        else:
            print("Please choose a displayed number. No action was taken.")

def main(argv=None, input_fn=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audience", choices=sorted(GUIDES), default="mac")
    parser.add_argument("--source-root", type=Path, default=ROOT, help="Explicit source folder; no other folders are searched")
    parser.add_argument("--check", action="store_true", help="Print read-only readiness without interactive choices")
    parser.add_argument("--json", action="store_true", help="Print read-only JSON and exit without prompts")
    args = parser.parse_args(argv)
    try:
        report = build_report(args.source_root, args.audience)
    except (OSError, ValueError) as error:
        if args.json:
            print(json.dumps({"schema": 1, "status": "not-ready", "play_ready": False, "public_bootstrap": {"implemented": False}, "error": str(error)}, indent=2))
        else:
            print("Player guide paused: " + str(error), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_report(report)
        if not args.check:
            interactive(Path(report["source_root"]), args.audience, input_fn or input)
    return 2  # Never imply that this readiness guide installed a game.

if __name__ == "__main__":
    raise SystemExit(main())
