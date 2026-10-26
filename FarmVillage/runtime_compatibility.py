"""Verify and atomically stage a reviewed local Ruffle distribution.

This module is shared by source and bundled launches and needs only the Python
standard library. No modified runtime is selected until ACTIVE_RELEASE is pinned
after native acceptance. The caller retains the existing profile lifecycle lock.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
from types import MappingProxyType
from typing import Callable, Mapping, Optional
import uuid


MANIFEST_NAME = ".farmvillage-ruffle.json"
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z")
CheckCancelled = Optional[Callable[[], None]]


class RuntimeIntegrityError(ValueError):
    """A local runtime does not match its reviewed identity or complete files."""


@dataclass(frozen=True)
class RuntimeRelease:
    runtime_id: str
    upstream_version: str
    upstream_commit: str
    manifest_sha256: str

    def __post_init__(self):
        if (not all(isinstance(value, str) for value in (
                    self.runtime_id, self.upstream_version, self.upstream_commit, self.manifest_sha256))
                or not _IDENTIFIER.fullmatch(self.runtime_id)
                or not _IDENTIFIER.fullmatch(self.upstream_version)
                or not _COMMIT.fullmatch(self.upstream_commit)
                or not _SHA256.fullmatch(self.manifest_sha256)):
            raise ValueError("A runtime release requires a safe id and exact reviewed hashes.")


# Activation is deliberately separate from this reviewed verifier/installer.
ACTIVE_RELEASE: RuntimeRelease | None = RuntimeRelease(
    "0.7.1-farmvillage-gc1",
    "0.7.1",
    "89a7049965f3090e706265670df309a5128233ac",
    "a841dc7fc1729eab67afe67cf3418a4633a2de5e03ebd878e1cf6749387ddf03",
)


@dataclass(frozen=True)
class VerifiedRuntime:
    directory: Path
    release: RuntimeRelease
    files: Mapping[str, str]


def _release(release: RuntimeRelease | None) -> RuntimeRelease:
    selected = release if release is not None else ACTIVE_RELEASE
    if selected is None:
        raise RuntimeIntegrityError("No reviewed compatibility runtime has been activated.")
    return selected


def _check(callback: CheckCancelled) -> None:
    if callback is not None:
        callback()


def _directory(path: Path) -> Path:
    path = Path(path).absolute()
    try:
        mode = path.lstat().st_mode
    except OSError as error:
        raise RuntimeIntegrityError(f"The runtime directory is unavailable: {path.name}") from error
    if not stat.S_ISDIR(mode) or stat.S_ISLNK(mode):
        raise RuntimeIntegrityError("Runtime directories must be ordinary directories, not links.")
    return path


def _relative(name: str) -> PurePosixPath:
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise RuntimeIntegrityError("The runtime manifest contains an unsafe file name.")
    relative = PurePosixPath(name)
    if (not relative.parts or relative.is_absolute() or relative.as_posix() != name
            or any(part in ("", ".", "..") or ":" in part for part in relative.parts)):
        raise RuntimeIntegrityError("The runtime manifest contains an unsafe file name.")
    return relative


def _child(root: Path, name: str, *, directory: bool = False, missing: bool = False) -> Path:
    relative = _relative(name)
    current = root
    for index, part in enumerate(relative.parts):
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            if missing:
                return root / relative
            raise RuntimeIntegrityError(f"A reviewed runtime file is missing: {name}") from None
        if stat.S_ISLNK(mode):
            raise RuntimeIntegrityError("The runtime contains a symbolic link.")
        final = index == len(relative.parts) - 1
        expected_directory = not final or directory
        if expected_directory and not stat.S_ISDIR(mode):
            raise RuntimeIntegrityError("A runtime directory path is not a directory.")
        if not expected_directory and not stat.S_ISREG(mode):
            raise RuntimeIntegrityError("A runtime file is not an ordinary file.")
    return current


def _file_digest(path: Path, check_cancelled: CheckCancelled) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            _check(check_cancelled)
            digest.update(chunk)
    return digest.hexdigest()


def _manifest(directory: Path, release: RuntimeRelease) -> dict:
    manifest_file = _child(directory, MANIFEST_NAME)
    if manifest_file.stat().st_size > 1024 * 1024:
        raise RuntimeIntegrityError("The runtime manifest exceeds its expected size.")
    raw = manifest_file.read_bytes()
    if hashlib.sha256(raw).hexdigest() != release.manifest_sha256:
        raise RuntimeIntegrityError("The runtime manifest does not match its reviewed hash.")
    try:
        manifest = json.loads(raw)
    except (ValueError, UnicodeError) as error:
        raise RuntimeIntegrityError("The reviewed runtime manifest is invalid JSON.") from error
    if (not isinstance(manifest, dict) or manifest.get("schema") != 1
            or manifest.get("runtime_id") != release.runtime_id
            or manifest.get("version") != release.upstream_version
            or manifest.get("upstream_commit") != release.upstream_commit):
        raise RuntimeIntegrityError("The runtime manifest has an unsupported identity.")
    files = manifest.get("files")
    if (not isinstance(files, dict) or not files or "ruffle.js" not in files
            or not any(isinstance(name, str) and name.endswith(".wasm") for name in files)):
        raise RuntimeIntegrityError("The runtime manifest is missing its loader or WebAssembly.")
    for name, digest in files.items():
        _relative(name)
        if name == MANIFEST_NAME or not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            raise RuntimeIntegrityError("The runtime manifest has an invalid file hash.")
    return manifest


def verify_runtime(directory: Path, release: RuntimeRelease | None = None,
                   *, check_cancelled: CheckCancelled = None) -> VerifiedRuntime:
    """Verify a hard-pinned manifest and its exact complete file set."""
    _check(check_cancelled)
    selected = _release(release)
    directory = _directory(directory)
    manifest = _manifest(directory, selected)
    expected = set(manifest["files"]) | {MANIFEST_NAME}
    actual = set()
    for parent, directories, files in os.walk(directory, followlinks=False):
        _check(check_cancelled)
        parent = Path(parent)
        for name in directories:
            _child(directory, (parent / name).relative_to(directory).as_posix(), directory=True)
        for name in files:
            relative = (parent / name).relative_to(directory).as_posix()
            _child(directory, relative)
            actual.add(relative)
    if actual != expected:
        raise RuntimeIntegrityError("The runtime file set is incomplete or contains unreviewed files.")
    for name, digest in manifest["files"].items():
        if _file_digest(_child(directory, name), check_cancelled) != digest:
            raise RuntimeIntegrityError(f"A runtime file failed its reviewed hash: {name}")
    return VerifiedRuntime(directory, selected, MappingProxyType(dict(manifest["files"])))


def runtime_valid(directory: Path, release: RuntimeRelease | None = None) -> bool:
    try:
        verify_runtime(directory, release)
        return True
    except (OSError, RuntimeIntegrityError):
        return False


def read_resource(runtime: VerifiedRuntime, name: str) -> bytes:
    """Read once and verify exactly the bytes that a response will serve.

    A verified startup inventory is not a promise that mutable profile/source
    files stay unchanged. Hash the requested file without reopening it, so a
    replacement after verification cannot turn into a mixed runtime response.
    """
    _relative(name)
    if name not in runtime.files:
        raise RuntimeIntegrityError("The requested file is not a reviewed player resource.")
    try:
        contents = _child(_directory(runtime.directory), name).read_bytes()
    except OSError as error:
        raise RuntimeIntegrityError("The requested runtime file is unavailable.") from error
    if hashlib.sha256(contents).hexdigest() != runtime.files[name]:
        raise RuntimeIntegrityError("The requested runtime file changed after verification.")
    return contents


def bundled_runtime(payload: Path, release: RuntimeRelease | None = None) -> Path:
    """Locate the same reviewed runtime inside a source or staged payload."""
    selected = _release(release)
    payload = _directory(payload)
    return _child(payload, "ruffle_runtime/" + selected.runtime_id, directory=True)


def _remove_owned_directory(directory: Path) -> None:
    if directory.is_symlink():
        directory.unlink()
    elif directory.exists():
        shutil.rmtree(directory)


def _clean_stages(parent: Path, release: RuntimeRelease) -> None:
    # The profile lock excludes a live installer. Never follow links or remove
    # a prior-runtime quarantine, which may be the only copy after a failed
    # rollback. Only unpublished stages for this exact id are disposable.
    prefix = ".ruffle-stage-" + release.runtime_id + "-"
    for entry in parent.iterdir():
        if entry.name.startswith(prefix) and stat.S_ISDIR(entry.lstat().st_mode):
            shutil.rmtree(entry)


def install_runtime(payload: Path, data: Path, release: RuntimeRelease | None = None,
                    *, check_cancelled: CheckCancelled = None) -> Path:
    """Atomically install verified local bytes; preserve older runtime ids.

    The caller holds its normal profile lock. A valid installed copy is reused
    without network access. No interpreter, save, asset or other profile content
    is modified, and a failed replacement restores the previous directory.
    """
    selected = _release(release)
    data = _directory(data)
    parent = _child(data, "ruffle", directory=True, missing=True)
    parent.mkdir(exist_ok=True)
    parent = _child(data, "ruffle", directory=True)
    _clean_stages(parent, selected)
    destination = _child(parent, selected.runtime_id, directory=True, missing=True)
    _check(check_cancelled)
    try:
        verify_runtime(destination, selected, check_cancelled=check_cancelled)
        return destination
    except (OSError, RuntimeIntegrityError):
        pass
    source = verify_runtime(bundled_runtime(payload, selected), selected,
                            check_cancelled=check_cancelled)
    stage = Path(tempfile.mkdtemp(prefix=".ruffle-stage-" + selected.runtime_id + "-", dir=parent))
    previous: Path | None = None
    published = False
    try:
        for name in (*source.files, MANIFEST_NAME):
            _check(check_cancelled)
            target = stage / _relative(name)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(_child(source.directory, name), target)
        verify_runtime(stage, selected, check_cancelled=check_cancelled)
        _check(check_cancelled)
        # A prior invalid copy is quarantined only after the complete new copy
        # has verified; the official upstream directory has a different id.
        if destination.exists():
            previous = parent / (".ruffle-previous-" + selected.runtime_id + "-" + uuid.uuid4().hex)
            os.replace(destination, previous)
        try:
            os.replace(stage, destination)
            published = True
        except BaseException:
            if previous is not None:
                os.replace(previous, destination)
                previous = None
            raise
    finally:
        _remove_owned_directory(stage)
        if published and previous is not None:
            # Successful publication is not undone by an obsolete-copy cleanup
            # failure. The live verified runtime remains the authoritative copy.
            try:
                _remove_owned_directory(previous)
            except OSError:
                pass
    return destination


def public_path(release: RuntimeRelease | None = None) -> str:
    return "/ruffle/" + _release(release).runtime_id + "/"


def resource_name(path: str, release: RuntimeRelease | None = None) -> str:
    """Resolve only the active version prefix; never accept an old mixed URL."""
    selected = _release(release)
    prefix = selected.runtime_id + "/"
    if not isinstance(path, str) or not path.startswith(prefix):
        raise RuntimeIntegrityError("The requested Ruffle runtime id is unsupported.")
    relative = path[len(prefix):]
    _relative(relative)
    if relative == MANIFEST_NAME:
        raise RuntimeIntegrityError("The runtime manifest is not a player resource.")
    return relative


def main(arguments=None) -> None:
    """Build-time verification only; this command never installs a runtime."""
    parser = argparse.ArgumentParser(description="Verify the reviewed local Ruffle package.")
    parser.add_argument("--payload", required=True, type=Path)
    options = parser.parse_args(arguments)
    verified = verify_runtime(bundled_runtime(options.payload))
    print(f"Verified local Ruffle {verified.release.runtime_id}: {len(verified.files)} reviewed files.")


if __name__ == "__main__":
    main()
