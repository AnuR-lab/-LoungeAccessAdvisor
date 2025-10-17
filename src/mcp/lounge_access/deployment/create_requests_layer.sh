#!/usr/bin/env bash
set -euo pipefail

# Creates an AWS Lambda Layer containing the 'requests' library (and its deps)
# and publishes it to AWS. Writes the resulting LayerVersionArn to layer_arn.txt
# in this directory for reuse by deployment scripts.
#
# Usage:
#   ./create_requests_layer.sh [-n LAYER_NAME] [-r REGION] [-p PYTHON_BIN]
# Defaults:
#   LAYER_NAME=atpco-lounge-access-requests-layer
#   REGION=us-east-1
#   PYTHON_BIN=python3 (auto-detected fallback to python)

LAYER_NAME="atpco-lounge-access-requests-layer"
REGION="us-east-1"
PYTHON_BIN=""

usage() {
  cat <<EOF
Usage: $0 [-n LAYER_NAME] [-r REGION] [-p PYTHON_BIN]
Defaults: LAYER_NAME=$LAYER_NAME REGION=$REGION PYTHON_BIN=auto
EOF
}

while getopts ":n:r:p:h" opt; do
  case $opt in
    n) LAYER_NAME="$OPTARG" ;;
    r) REGION="$OPTARG" ;;
    p) PYTHON_BIN="$OPTARG" ;;
    h) usage; exit 0 ;;
    :) echo "Option -$OPTARG requires an argument" >&2; exit 1 ;;
    \?) echo "Invalid option: -$OPTARG" >&2; usage; exit 1 ;;
  esac
done

# Determine Python binary
if [[ -z "$PYTHON_BIN" ]]; then
  for c in python3 python py; do
    if command -v "$c" >/dev/null 2>&1; then PYTHON_BIN="$c"; break; fi
  done
fi
if [[ -z "$PYTHON_BIN" ]]; then
  echo "No Python interpreter found." >&2
  exit 1
fi

# Determine Python version components for layer path
PY_VER_FULL="$($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ -z "$PY_VER_FULL" ]]; then
  echo "Unable to determine Python version from $PYTHON_BIN" >&2
  exit 1
fi

BUILD_DIR="layer_build"
SITE_PKGS_DIR="$BUILD_DIR/python/lib/python$PY_VER_FULL/site-packages"
ZIP_NAME="requests-layer.zip"

# Clean previous artifacts
rm -rf "$BUILD_DIR" "$ZIP_NAME"
mkdir -p "$SITE_PKGS_DIR"

# Try uv first, then pip
if command -v uv >/dev/null 2>&1; then
  echo "Installing requests with uv to $SITE_PKGS_DIR" >&2
  if ! uv pip install --quiet --target "$SITE_PKGS_DIR" requests==2.31.0; then
    echo "uv failed, falling back to pip" >&2
  fi
fi

if [[ ! -d "$SITE_PKGS_DIR/requests" ]]; then
  echo "Installing requests with pip to $SITE_PKGS_DIR" >&2
  "$PYTHON_BIN" -m ensurepip --upgrade >/dev/null 2>&1 || true
  "$PYTHON_BIN" -m pip install --quiet --upgrade pip >/dev/null 2>&1 || true
  "$PYTHON_BIN" -m pip install --quiet --target "$SITE_PKGS_DIR" requests==2.31.0
fi

if [[ ! -d "$SITE_PKGS_DIR/requests" ]]; then
  echo "Requests did not install correctly; aborting" >&2
  exit 1
fi

# Zip the layer content
pushd "$BUILD_DIR" >/dev/null
zip -r "../$ZIP_NAME" python >/dev/null
popd >/dev/null

# Verify AWS CLI
if ! aws sts get-caller-identity >/dev/null 2>&1; then
  echo "AWS CLI not configured or credentials invalid. Run 'aws configure'." >&2
  exit 1
fi

# Publish layer version
echo "Publishing layer $LAYER_NAME to $REGION" >&2
LAYER_ARN=$(aws lambda publish-layer-version \
  --region "$REGION" \
  --layer-name "$LAYER_NAME" \
  --description "Requests library for Lounge Access MCP" \
  --license-info "Apache-2.0" \
  --zip-file "fileb://$ZIP_NAME" \
  --compatible-runtimes python3.11 python3.12 \
  --query 'LayerVersionArn' --output text)

if [[ -z "$LAYER_ARN" ]]; then
  echo "Failed to publish layer" >&2
  exit 1
fi

echo "$LAYER_ARN" | tee layer_arn.txt >/dev/null

# Optional: show result
echo "Layer published: $LAYER_ARN" >&2

# Cleanup build directory but keep the zip and arn file for traceability
rm -rf "$BUILD_DIR"
