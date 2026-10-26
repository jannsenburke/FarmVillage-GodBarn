#!/usr/bin/env python3
"""Stage only God Barn's application resources into the native game payload."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
import shutil


def bundle_companion(source: Path, destination: Path) -> None:
    source = source.resolve()
    destination = destination.absolute()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("God Barn must be staged into a fresh empty directory.")
    # Every module here is imported at runtime, so a missing one must fail the build.
    modules = ("__init__.py", "engine.py", "integration.py", "seasonal.py", "encyclopedia.py",
               "progression_tools.py", "catalog_tools.py", "helper_tools.py")
    required = (*modules, "static/index.html", "static/app.js", "static/style.css", "static/farmville.css",
                "static/touch.js",
                "data/rules.json", "data/catalog.json", "data/provenance.json", "data/untabbed.json")
    for name in required:
        path = source / name
        if not path.is_file() or path.is_symlink():
            raise ValueError("Missing regular companion resource: " + name)
    destination.mkdir(parents=True, exist_ok=True)
    for name in modules:
        shutil.copyfile(source / name, destination / name)
    # Thumbnails already exist in the user's extracted game asset archive. Copy
    # only interface art and fonts; map the large thumbnail collection by hash.
    for path in (source / "static").rglob("*"):
        relative = path.relative_to(source)
        if path.is_symlink():
            raise ValueError("Companion resources must not contain symbolic links.")
        if not path.is_file() or "__pycache__" in relative.parts or path.name == ".DS_Store":
            continue
        if relative.parts[:3] == ("static", "assets", "items"):
            continue
        if "contact-sheet" in path.name:
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    data = destination / "data"
    data.mkdir(exist_ok=True)
    shutil.copyfile(source / "data/rules.json", data / "rules.json")
    shutil.copyfile(source / "data/untabbed.json", data / "untabbed.json")
    if (source / "data/archive-provenance.json").is_file():
        shutil.copyfile(source / "data/archive-provenance.json", data / "archive-provenance.json")
    for name in ("progression.json", "historical-prizes.json", "catalog-audit.json", "helpers.json"):
        metadata = source / "data" / name
        if metadata.is_symlink():
            raise ValueError("Companion metadata must not be symbolic links.")
        if metadata.is_file():
            shutil.copyfile(metadata, data / name)
    encyclopedia = source / "data/encyclopedia.json"
    if encyclopedia.is_symlink():
        raise ValueError("Companion metadata must not be symbolic links.")
    if encyclopedia.is_file():
        (data / "encyclopedia.json.gz").write_bytes(gzip.compress(encyclopedia.read_bytes(), compresslevel=6, mtime=0))
    # Deterministic gzip keeps repeat builds and payload fingerprints stable.
    (data / "catalog.json.gz").write_bytes(gzip.compress((source / "data/catalog.json").read_bytes(), compresslevel=6, mtime=0))
    provenance = json.loads((source / "data/provenance.json").read_text())
    original_assets = Path(provenance["sourceDirectory"]) / "LocalData/assets"
    mapping = {}
    for item in provenance.get("assets", []):
        copied = item.get("path", "")
        if not copied.startswith("static/assets/items/"):
            continue
        try:
            relative = Path(item["originalPath"]).relative_to(original_assets)
        except (KeyError, ValueError) as error:
            raise ValueError("A catalog image escapes the original asset archive.") from error
        if ".." in relative.parts or relative.is_absolute():
            raise ValueError("Invalid archived thumbnail path.")
        mapping[copied] = relative.as_posix()
    (data / "asset-map.json").write_text(json.dumps(mapping, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    bundle_companion(args.source, args.destination)
