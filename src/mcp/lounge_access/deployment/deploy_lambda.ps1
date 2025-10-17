#!/usr/bin/env pwsh

# PowerShell script to deploy Lambda function
# Equivalent of deploy_lambda.sh
#
# Usage: .\deploy_lambda.ps1 [-FunctionName <name>] [-Region <region>]
# 
# Parameters:
#   -FunctionName: Name of the Lambda function (default: atpco-lounge-access-mcp-us-east-1)
#   -Region: AWS region (default: us-east-1)

param(
    [string]$FunctionName = "atpco-lounge-access-mcp-us-east-1",
    [string]$Region = "us-east-1"
)

Write-Host "Starting Lambda deployment process..." -ForegroundColor Green
Write-Host "Target Function: $FunctionName" -ForegroundColor Cyan
Write-Host "Target Region: $Region" -ForegroundColor Cyan

# Remove existing ZIP files
Write-Host "Cleaning up old ZIP files..." -ForegroundColor Yellow
Get-ChildItem -Path "." -Filter "*.zip" | Remove-Item -Force -ErrorAction SilentlyContinue

# Copy source files to deployment folder
Write-Host "Copying source files..." -ForegroundColor Yellow
$sourceFiles = @(
    "../api_client.py",
    "../lambda_handler.py", 
    "../mcp_handler.py",
    "../lounge_service.py",
    "../user_profile_service.py",
    "../flights_api_client.py",
    "../requirements.txt"
)

foreach ($file in $sourceFiles) {
    if (Test-Path $file) {
        Copy-Item $file -Destination "." -Force
        Write-Host "Copied: $file" -ForegroundColor Cyan
    } else {
        Write-Host "Warning: File not found: $file" -ForegroundColor Red
    }
}

## Install Python dependencies (flatten into function root for import)
Write-Host "Installing Python dependencies (requests)..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    $packagesDir = "packages"
    if (Test-Path $packagesDir) { Remove-Item $packagesDir -Recurse -Force }
    New-Item -ItemType Directory -Path $packagesDir | Out-Null

    # Prefer uv if available for deterministic, fast installs
    $useUv = $false
    try {
        uv --version 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { $useUv = $true }
    } catch { $useUv = $false }

    if ($useUv) {
        Write-Host "Using uv to install dependencies into $packagesDir" -ForegroundColor Cyan
        # uv pip install respects requirements.txt
        uv pip install --quiet --target $packagesDir -r requirements.txt
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Dependencies installed with uv" -ForegroundColor Green
        } else {
            Write-Host "uv install failed; falling back to python + ensurepip" -ForegroundColor Yellow
            $useUv = $false
        }
    }

    if (-not $useUv) {
        # Fallback: python -m ensurepip then pip install
        $pythonCommands = @("python","python3","py")
        $pythonCmd = $null
        foreach ($cmd in $pythonCommands) {
            try { & $cmd --version 2>$null | Out-Null; if ($LASTEXITCODE -eq 0) { $pythonCmd = $cmd; break } } catch { }
        }
        if ($pythonCmd) {
            Write-Host "Using $pythonCmd with ensurepip" -ForegroundColor Cyan
            & $pythonCmd -m ensurepip --upgrade 2>$null | Out-Null
            & $pythonCmd -m pip install --quiet --upgrade pip 2>$null | Out-Null
            & $pythonCmd -m pip install --quiet --target $packagesDir -r requirements.txt
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Dependencies installed with pip" -ForegroundColor Green
            } else {
                Write-Host "Failed to install dependencies with pip; deployment will likely fail for 'requests'" -ForegroundColor Red
            }
        } else {
            Write-Host "No Python interpreter found; cannot bundle dependencies" -ForegroundColor Red
        }
    }
} else {
    Write-Host "No requirements.txt found, skipping dependency installation" -ForegroundColor Yellow
}

# Create ZIP package
Write-Host "Creating ZIP package..." -ForegroundColor Yellow
$zipFileName = "atpco-lounge-access-lambda.zip"

# Remove existing ZIP if it exists
if (Test-Path $zipFileName) {
    Remove-Item $zipFileName -Force
}

# Get all Python files in current directory
$pythonFiles = Get-ChildItem -Path "." -Filter "*.py"
$filesToZip = @()

# Add Python files
foreach ($file in $pythonFiles) {
    $filesToZip += $file.Name
}

if (Test-Path "packages") {
    Write-Host "Will include dependencies from packages/" -ForegroundColor Cyan
}

try {
    # Build list of paths to archive: python sources + packages tree
    $pathsToArchive = @()
    $pathsToArchive += (Get-ChildItem -Path "." -Filter "*.py" | ForEach-Object { $_.FullName })
    if (Test-Path "packages") {
        $pathsToArchive += (Get-ChildItem -Path "packages" -Recurse -File | ForEach-Object { $_.FullName })
    }

    if ($pathsToArchive.Count -eq 0) { Write-Host "Nothing to package" -ForegroundColor Red; exit 1 }

    # Flatten dependencies: copy each top-level dependency directory/file into current working directory
    if (Test-Path "packages") {
        Write-Host "Flattening dependency directories into function root..." -ForegroundColor Cyan
        # Discover top-level package directories actually installed
        $topLevelDirs = Get-ChildItem -Path $packagesDir -Directory | Select-Object -ExpandProperty Name
        foreach ($d in $topLevelDirs) {
            # Skip __pycache__
            if ($d -like "__pycache__") { continue }
            Copy-Item (Join-Path $packagesDir $d) -Destination . -Recurse -Force
        }
        # Copy .py files sitting at root of packagesDir (rare)
        Get-ChildItem -Path $packagesDir -File -Filter "*.py" | ForEach-Object { Copy-Item $_.FullName -Destination . -Force }
        # Copy metadata directories (.dist-info) required for some libs
        Get-ChildItem -Path $packagesDir -Directory -Filter "*.dist-info" | ForEach-Object { Copy-Item $_.FullName -Destination . -Recurse -Force }
    }

    if (Test-Path $zipFileName) { Remove-Item $zipFileName -Force }
    $contentToZip = @()
    # All top-level python source files
    $contentToZip += (Get-ChildItem -Path . -Filter "*.py" | ForEach-Object { $_.FullName })
    # Add dependency directories discovered (requests and its deps)
    foreach ($dir in (Get-ChildItem -Directory)) {
        if ($dir.Name -in @("requests","urllib3","certifi","charset_normalizer","idna")) {
            $contentToZip += $dir.FullName
        }
        if ($dir.Name -like "*.dist-info") { $contentToZip += $dir.FullName }
    }
    if ($contentToZip.Count -eq 0) { Write-Host "No content collected for zip; aborting." -ForegroundColor Red; exit 1 }
    # Use staging folder to preserve directory names
    $stage = "stage_zip"
    if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
    New-Item -ItemType Directory -Path $stage | Out-Null
    foreach ($item in $contentToZip) {
        $dest = Join-Path $stage (Split-Path $item -Leaf)
        Copy-Item $item $dest -Recurse -Force
    }
    Compress-Archive -Path "$stage/*" -DestinationPath $zipFileName -Force
    Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "ZIP package created: $zipFileName" -ForegroundColor Green
    $zipSize = (Get-Item $zipFileName).Length
    Write-Host "ZIP file size: $zipSize bytes" -ForegroundColor Cyan
} catch {
    Write-Host "Error creating ZIP package: $_" -ForegroundColor Red
    exit 1
}

# Update Lambda function code
Write-Host "Updating Lambda function code..." -ForegroundColor Yellow

# Check if AWS CLI is configured
Write-Host "Checking AWS CLI configuration..." -ForegroundColor Yellow

try {
    # Try to get AWS identity to verify configuration
    $awsIdentity = aws sts get-caller-identity 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "AWS CLI not configured or no valid credentials found." -ForegroundColor Red
        Write-Host "Please run 'aws configure' to set up your AWS credentials." -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "AWS CLI configured successfully" -ForegroundColor Green
    
    # Update Lambda function with region specified
    Write-Host "Deploying to Lambda function: $FunctionName in region: $Region" -ForegroundColor Cyan
    aws lambda update-function-code --region $Region --function-name $FunctionName --zip-file "fileb://$zipFileName"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Lambda function updated successfully!" -ForegroundColor Green
    } else {
        Write-Host "Error updating Lambda function. AWS CLI exit code: $LASTEXITCODE" -ForegroundColor Red
        Write-Host "Make sure the Lambda function '$FunctionName' exists in region '$Region'" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Error executing AWS CLI command: $_" -ForegroundColor Red
}

# Clean up copied Python files and temporary directories
Write-Host "Cleaning up temporary files..." -ForegroundColor Yellow

# Keep flattened dependencies for inspection if desired (comment out to remove). Remove build artifacts only.
Remove-Item "packages" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "requirements.txt" -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path "." -Filter "*.egg-info" -Recurse | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path "." -Filter "*__pycache__*" -Recurse | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Deployment process completed!" -ForegroundColor Green