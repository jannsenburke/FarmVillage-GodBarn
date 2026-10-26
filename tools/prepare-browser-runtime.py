#!/usr/bin/env python3
"""Stage a NEW private browser release; never install, download, start or read saves."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def prepare(root, destination):
    root, destination = root.absolute(), destination.absolute()
    if any(p.is_symlink() for p in [root, *root.parents, destination, *destination.parents]):
        raise ValueError("Linked source/output ancestors refused; use ordinary canonical paths")
    if destination.exists() or destination.is_symlink():
        raise ValueError("Choose a NEW private output folder; existing releases/data are preserved")
    if root == destination or root in destination.parents or destination in root.parents:
        raise ValueError("Keep private releases outside the GitHub source folder")
    subprocess.run([sys.executable, "-B", str(root / "tools/check-source.py"), "--root", str(root)], check=True)
    subprocess.run([sys.executable, "-B", str(root / "tools/private-inputs.py"), "--root", str(root), "check"], check=True)
    game, barn = root / "FarmVillage", root / "GodBarn"
    destination.mkdir(parents=True)
    try:
        runtime = destination / "Runtime"
        runtime.mkdir()
        for p in sorted(game.glob("*.py")):
            if p.is_symlink():
                raise ValueError("Linked source refused")
            shutil.copyfile(p, runtime / p.name)
        for name in ["requirements.txt", "LICENSE", "FLASH.md"]:
            shutil.copyfile(game / name, runtime / name)
        for name in ["assethash", "embeds", "patched", "templates", "villages", "warc_extractor", "xml", "ruffle_runtime"]:
            shutil.copytree(game / name, runtime / name, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
        subprocess.run([sys.executable, "-B", str(barn / "scripts/bundle_companion.py"), str(barn), str(runtime / "GodBarn")], check=True)
        subprocess.run([sys.executable, "-B", str(game / "macOS/Scripts/patch-game-client.py"), str(game / "embeds/Flash/v855097-855094/FarmGame.swf"), str(runtime / "embeds/Flash/v855097-855094/FarmGame.swf")], check=True)
        subprocess.run([sys.executable, "-B", str(runtime / "runtime_compatibility.py"), "--payload", str(runtime)], check=True)
        shutil.copytree(game / "macOS/Runtime", destination / "BackendHost", ignore=shutil.ignore_patterns("__pycache__"))
        hosting = destination / "hosting"
        hosting.mkdir()
        for name in ["server_runner.py", "neighborhood_host.py", "preloader_timing.py"]:
            shutil.copyfile(game / "portable/Linux" / name, hosting / name)
        files = {}
        for p in sorted(destination.rglob("*")):
            if p.is_symlink():
                raise ValueError("Private stage must not contain linked files")
            if p.is_file():
                raw = p.read_bytes()
                files[p.relative_to(destination).as_posix()] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        (destination / "PRIVATE_RELEASE_MANIFEST.json").write_text(json.dumps({"schema": 1, "kind": "new-private-browser-runtime", "source": json.loads((root / "SOURCE_MANIFEST.json").read_text())["source"], "files": files}, indent=2, sort_keys=True) + "\n")
    except BaseException:
        shutil.rmtree(destination)
        raise
    return {"status": "staged-private-browser-release", "files": len(files), "destination": str(destination), "started": False, "downloaded": False, "savesRead": False}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-root", type=Path, default=ROOT)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    print(json.dumps(prepare(a.source_root, a.output), indent=2))

if __name__ == "__main__":
    main()
