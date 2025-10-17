#!/usr/bin/env bash
set -euo pipefail

# Enhanced deployment script (Bash) to mirror PowerShell version
# - Copies source files
# - Installs Python dependencies from requirements.txt (requests) into a temp dir
# - Flattens dependencies into function root
# - Creates a staged zip preserving directory structure
# - Updates Lambda function code
# - Cleans up temporary artifacts

FUNCTION_NAME="atpco-lounge-access-mcp-us-east-1"
REGION="us-east-1"

usage() {
  cat <<EOF
Usage: $0 [-f FUNCTION_NAME] [-r REGION]
Defaults: FUNCTION_NAME=$FUNCTION_NAME REGION=$REGION
EOF
}

while getopts ":f:r:h" opt; do
  case $opt in
    f) FUNCTION_NAME="$OPTARG" ;;
    r) REGION="$OPTARG" ;;
    h) usage; exit 0 ;;
    :) echo "Option -$OPTARG requires an argument" >&2; exit 1 ;;
    \?) echo "Invalid option: -$OPTARG" >&2; usage; exit 1 ;;
  esac
done

echo "Starting Lambda deployment..." >&2
echo "Function: $FUNCTION_NAME" >&2
echo "Region:   $REGION" >&2

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
while IFS= read -r -d '' py; do CONTENT+=("$py"); done < <(find . -maxdepth 1 -name '*.py' -print0)

for dir in requests urllib3 certifi charset_normalizer idna; do
  [[ -d "$dir" ]] && CONTENT+=("$dir")
done

# Include *.dist-info metadata
while IFS= read -r -d '' meta; do CONTENT+=("$meta"); done < <(find . -maxdepth 1 -type d -name '*.dist-info' -print0)

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
else
  echo "Failed to update Lambda function" >&2
  exit 1
fi

# Cleanup
echo "Cleaning up build artifacts" >&2
rm -rf "$STAGE_DIR" "$PACKAGES_DIR" requirements.txt *.egg-info */__pycache__
echo "Deployment complete" >&2



