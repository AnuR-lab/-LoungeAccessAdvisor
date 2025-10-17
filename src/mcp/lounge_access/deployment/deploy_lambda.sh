#!/usr/bin/env bash
set -euo pipefail

# Enhanced deployment script (Bash) to mirror PowerShell version
# - Copies source files
# - Installs Python dependencies from requirements.txt (requests) into a temp dir
# - Flattens dependencies into function root
# - Creates a staged zip preserving directory structure
# - Updates Lambda function code
# - Optionally attaches a Lambda Layer (e.g., requests layer)
# - Cleans up temporary artifacts

FUNCTION_NAME="atpco-lounge-access-mcp-us-east-1"
REGION="us-east-1"
LAYER_ARN="arn:aws:lambda:us-east-1:905418267822:layer:atpco-lounge-access-requests-layer:1"

usage() {
  cat <<EOF
Usage: $0 [-f FUNCTION_NAME] [-r REGION] [-l LAYER_ARN]
Defaults: FUNCTION_NAME=$FUNCTION_NAME REGION=$REGION
If -l is not provided, the script will use layer_arn.txt from this directory if present.
EOF
}

while getopts ":f:r:l:h" opt; do
  case $opt in
    f) FUNCTION_NAME="$OPTARG" ;;
    r) REGION="$OPTARG" ;;
    l) LAYER_ARN="$OPTARG" ;;
    h) usage; exit 0 ;;
    :) echo "Option -$OPTARG requires an argument" >&2; exit 1 ;;
    \?) echo "Invalid option: -$OPTARG" >&2; usage; exit 1 ;;
  esac
done

# Load default layer ARN from file if not passed via -l
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -z "$LAYER_ARN" && -f "$SCRIPT_DIR/layer_arn.txt" ]]; then
  LAYER_ARN="$(cat "$SCRIPT_DIR/layer_arn.txt" | tr -d '\n' | tr -d '\r')"
fi

echo "Starting Lambda deployment..." >&2
echo "Function: $FUNCTION_NAME" >&2
echo "Region:   $REGION" >&2
if [[ -n "$LAYER_ARN" ]]; then echo "Layer:    $LAYER_ARN" >&2; fi

# Clean old zips
rm -f *.zip

SOURCE_FILES=(
  "../api_client.py"
  "../lambda_handler.py"
  "../mcp_handler.py"
  "../lounge_service.py"
  "../user_profile_service.py"
  "../flights_api_client.py"
  "../requirements.txt"
)

for f in "${SOURCE_FILES[@]}"; do
  if [[ -f "$f" ]]; then
    cp "$f" .
    echo "Copied $f" >&2
  else
    echo "Warning: missing $f" >&2
  fi
done

# Install dependencies if requirements present
PACKAGES_DIR="packages"
if [[ -f requirements.txt ]]; then
  rm -rf "$PACKAGES_DIR"
  mkdir "$PACKAGES_DIR"
  echo "Installing Python dependencies..." >&2
  # Prefer uv if available
  if command -v uv >/dev/null 2>&1; then
    if uv pip install --quiet --target "$PACKAGES_DIR" -r requirements.txt; then
      echo "Dependencies installed with uv" >&2
    else
      echo "uv install failed, falling back to pip" >&2
    fi
  fi
  if [[ ! -d "$PACKAGES_DIR/requests" ]]; then
    PYTHON_BIN=""
    for c in python python3 py; do
      if command -v "$c" >/dev/null 2>&1; then PYTHON_BIN="$c"; break; fi
    done
    if [[ -z "$PYTHON_BIN" ]]; then
      echo "No Python interpreter found; cannot install dependencies" >&2
    else
      "$PYTHON_BIN" -m ensurepip --upgrade >/dev/null 2>&1 || true
      "$PYTHON_BIN" -m pip install --quiet --upgrade pip >/dev/null 2>&1 || true
      if "$PYTHON_BIN" -m pip install --quiet --target "$PACKAGES_DIR" -r requirements.txt; then
        echo "Dependencies installed with pip" >&2
      else
        echo "pip install failed; 'requests' may not be packaged" >&2
      fi
    fi
  fi
else
  echo "requirements.txt not found; skipping dependency install" >&2
fi

# Flatten dependencies into root
if [[ -d "$PACKAGES_DIR" ]]; then
  echo "Flattening dependencies..." >&2
  for d in "$PACKAGES_DIR"/*; do
    base="$(basename "$d")"
    [[ "$base" == "__pycache__" ]] && continue
    cp -R "$d" .
  done
fi

ZIP_NAME="atpco-lounge-access-lambda.zip"
STAGE_DIR="stage_zip"
rm -rf "$STAGE_DIR" "$ZIP_NAME"
mkdir "$STAGE_DIR"

echo "Collecting content for zip..." >&2
CONTENT=()
# Collect Python source files without process substitution
for py in ./*.py; do
  [[ -f "$py" ]] && CONTENT+=("$py")
done

for dir in requests urllib3 certifi charset_normalizer idna; do
  [[ -d "$dir" ]] && CONTENT+=("$dir")
done

# Include *.dist-info metadata directories
for meta in ./*.dist-info; do
  [[ -d "$meta" ]] && CONTENT+=("$meta")
done

if [[ ${#CONTENT[@]} -eq 0 ]]; then
  echo "No content found to package; aborting" >&2
  exit 1
fi

for item in "${CONTENT[@]}"; do
  cp -R "$item" "$STAGE_DIR/" 2>/dev/null || true
done

echo "Creating zip $ZIP_NAME" >&2
pushd "$STAGE_DIR" >/dev/null
zip -r "../$ZIP_NAME" . >/dev/null
popd >/dev/null
ZIP_SIZE=$(stat -c %s "$ZIP_NAME" 2>/dev/null || wc -c <"$ZIP_NAME")
echo "Zip size: $ZIP_SIZE bytes" >&2

# Verify AWS CLI credentials
if ! aws sts get-caller-identity >/dev/null 2>&1; then
  echo "AWS CLI not configured or credentials invalid. Run 'aws configure'." >&2
  exit 1
fi
echo "AWS CLI identity verified" >&2

echo "Updating Lambda function code..." >&2
if aws lambda update-function-code --region "$REGION" --function-name "$FUNCTION_NAME" --zip-file "fileb://$ZIP_NAME" >/dev/null; then
  echo "Lambda code updated successfully" >&2
  echo "Waiting for function code update to complete..." >&2
  aws lambda wait function-updated --region "$REGION" --function-name "$FUNCTION_NAME" || {
    echo "Warning: wait for function-updated failed or timed out; continuing" >&2
  }
else
  echo "Failed to update Lambda function" >&2
  exit 1
fi

# Attach the specified layer if provided
if [[ -n "$LAYER_ARN" ]]; then
  echo "Updating Lambda function configuration to use layer..." >&2
  # Retry on ResourceConflictException while a previous update is in progress
  max_attempts=10
  attempt=1
  backoff=3
  while true; do
    if out=$(aws lambda update-function-configuration --region "$REGION" --function-name "$FUNCTION_NAME" --layers "$LAYER_ARN" 2>&1); then
      echo "Lambda layer updated: $LAYER_ARN" >&2
      echo "Waiting for configuration update to complete..." >&2
      aws lambda wait function-updated --region "$REGION" --function-name "$FUNCTION_NAME" || {
        echo "Warning: wait after configuration update failed or timed out; continuing" >&2
      }
      break
    else
      # If conflict, back off and retry; otherwise, fail
      if grep -qi "ResourceConflictException" <<< "$out"; then
        if (( attempt >= max_attempts )); then
          echo "Failed to update Lambda layer configuration after $attempt attempts (still in progress)" >&2
          echo "Last error: $out" >&2
          exit 1
        fi
        echo "Update in progress; retrying in ${backoff}s (attempt $attempt/$max_attempts)..." >&2
        sleep "$backoff"
        ((attempt++))
        # Exponential-ish backoff up to 15s
        if (( backoff < 15 )); then backoff=$((backoff * 2)); fi
      else
        echo "Failed to update Lambda layer configuration" >&2
        echo "$out" >&2
        exit 1
      fi
    fi
  done
fi

# Cleanup
echo "Cleaning up build artifacts" >&2
rm -rf "$STAGE_DIR" "$PACKAGES_DIR" requirements.txt *.egg-info */__pycache__
echo "Deployment complete" >&2



