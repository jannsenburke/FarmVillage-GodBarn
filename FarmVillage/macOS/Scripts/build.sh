#!/bin/bash
# Build the local unsigned app without launching it or running tests.
set -euo pipefail
TASK_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TASK_PROJECT_DIR="$(cd "$TASK_SCRIPT_DIR/.." && pwd)"
TASK_CONFIGURATION="${1:-Debug}"
case "$TASK_CONFIGURATION" in
    Debug|Release) ;;
    *) printf 'Usage: %s [Debug|Release]\n' "$0" >&2; exit 2 ;;
esac
/usr/bin/xcodebuild \
    -project "$TASK_PROJECT_DIR/FarmVillage.xcodeproj" \
    -scheme FarmVillage \
    -configuration "$TASK_CONFIGURATION" \
    -destination 'platform=macOS' \
    -derivedDataPath "$TASK_PROJECT_DIR/.build/DerivedData" \
    CODE_SIGNING_ALLOWED=NO \
    build
printf '\nApp: %s/.build/DerivedData/Build/Products/%s/FarmVillage.app\n' "$TASK_PROJECT_DIR" "$TASK_CONFIGURATION"
