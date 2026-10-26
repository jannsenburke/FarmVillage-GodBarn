#!/usr/bin/env bash
set -euo pipefail
FV_SETUP_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$(uname -s)" != Linux ]]; then
  printf 'Run this guide on the Ubuntu/Linux game host. macOS uses the native desktop app in README.md. Nothing is deployed remotely.\n' >&2
  exit 2
fi
if [[ -f "$FV_SETUP_DIR/SHA256SUMS" ]]; then
  printf 'Checking the complete private bundle before setup...\n'
  if ! command -v sha256sum >/dev/null; then
    printf 'Install Ubuntu coreutils (sudo apt install coreutils), then rerun this same entry. No game data has changed.\n' >&2
    exit 2
  fi
  if ! (cd -- "$FV_SETUP_DIR" && sha256sum --quiet -c SHA256SUMS); then
    printf "Some bundle files are missing or different. Extract the complete matching private ZIP again, then rerun this same entry. No installation data has changed.\n" >&2
    exit 2
  fi
fi
if ! command -v python3 >/dev/null || ! python3 -c 'import sys, venv, ensurepip; assert sys.version_info >= (3,10)' >/dev/null 2>&1; then
  printf 'A few Ubuntu tools are needed first. Run:\n\n  sudo apt update\n  sudo apt install python3 python3-venv python3-pip\n\nThen run this same START_HERE.sh again. No game files have changed.\n' >&2
  exit 2
fi
if [[ -f "$FV_SETUP_DIR/setup-wizard.py" ]]; then
  exec python3 -I -B "$FV_SETUP_DIR/setup-wizard.py"
fi
exec python3 -I -B "$FV_SETUP_DIR/tools/setup-wizard.py"
