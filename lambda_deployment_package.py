#!/usr/bin/env python3
"""
Create Lambda deployment package for LoungeAccessAdvisor
Enhanced with flight-aware capabilities
"""
import os
import shutil
import zipfile
from pathlib import Path

def create_lambda_package():
    """Create a deployment package for the Lambda function"""
    
    print("📦 Creating Lambda Deployment Package")
    print("=" * 50)
    
    # Define paths
    source_dir = Path("src/mcp/lounge_access")
    package_dir = Path("lambda_package")
    zip_file = Path("loungeaccessadvisor-lambda.zip")
    
    # Clean up previous package
    if package_dir.exists():
        shutil.rmtree(package_dir)
    if zip_file.exists():
        zip_file.unlink()
    
    # Create package directory
    package_dir.mkdir()
    
    print("📁 Copying source files...")
    
    # Files to include in Lambda package
    files_to_copy = [
        "lambda_handler.py",
        "mcp_handler.py", 
        "api_client.py",
        "flight_service.py",
        "lounge_service.py",
        "user_profile_service.py",
        "requirements.txt"
    ]
    
    # Copy source files
    for file_name in files_to_copy:
        source_file = source_dir / file_name
        if source_file.exists():
            shutil.copy2(source_file, package_dir / file_name)
            print(f"   ✅ Copied {file_name}")
        else:
            print(f"   ⚠️  Missing {file_name}")
    
    # Create deployment info file
    deployment_info = package_dir / "deployment_info.json"
    with open(deployment_info, 'w') as f:
        import json
        from datetime import datetime
        info = {
            "deployment_date": datetime.now().isoformat(),
            "version": "1.0.0-flight-aware",
            "features": [
                "Basic lounge lookup",
                "Flight-aware recommendations", 
                "Layover strategy analysis",
                "Optimized flight search",
                "Real-time Amadeus API integration"
            ],
            "tools_supported": [
                "getUser",
                "getLoungesWithAccessRules", 
                "getFlightLoungeRecs",
                "analyzeLayoverStrategy",
                "searchFlightsOptimized"
            ]
        }
        json.dump(info, f, indent=2)
    print(f"   ✅ Created deployment_info.json")
    
    # Create ZIP package
    print(f"\n📦 Creating ZIP package: {zip_file}")
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in package_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(package_dir)
                zf.write(file_path, arcname)
                print(f"   ✅ Added {arcname}")
    
    # Package info
    package_size = zip_file.stat().st_size / 1024 / 1024  # MB
    print(f"\n📊 Package Information:")
    print(f"   Size: {package_size:.2f} MB")
    print(f"   Files: {len(list(package_dir.rglob('*')))} files")
    print(f"   Location: {zip_file.absolute()}")
    
    # Deployment instructions
    print(f"\n🚀 Deployment Instructions:")
    print(f"1. Upload {zip_file} to AWS Lambda")
    print(f"2. Set handler to: lambda_handler.lambda_handler")
    print(f"3. Configure environment variables:")
    print(f"   - AWS_REGION=us-east-1")
    print(f"4. Attach IAM role with permissions:")
    print(f"   - secretsmanager:GetSecretValue (for autorescue/amadeus/credentials)")
    print(f"   - dynamodb:GetItem, Query (for lounge and user data)")
    print(f"5. Set timeout to 30 seconds (for API calls)")
    print(f"6. Configure memory to 256 MB minimum")
    
    # Clean up
    shutil.rmtree(package_dir)
    
    print(f"\n✅ Lambda package created successfully!")
    return zip_file

def validate_package_contents():
    """Validate the created package has all required files"""
    zip_file = Path("loungeaccessadvisor-lambda.zip")
    
    if not zip_file.exists():
        print("❌ Package file not found")
        return False
    
    print(f"\n🔍 Validating package contents...")
    
    required_files = [
        "lambda_handler.py",
        "mcp_handler.py",
        "api_client.py", 
        "flight_service.py",
        "requirements.txt",
        "deployment_info.json"
    ]
    
    with zipfile.ZipFile(zip_file, 'r') as zf:
        package_files = zf.namelist()
        
        all_present = True
        for required_file in required_files:
            if required_file in package_files:
                print(f"   ✅ {required_file}")
            else:
                print(f"   ❌ Missing: {required_file}")
                all_present = False
    
    if all_present:
        print("✅ All required files present in package")
    else:
        print("⚠️  Some required files are missing")
    
    return all_present

if __name__ == "__main__":
    try:
        zip_file = create_lambda_package()
        validate_package_contents()
        
        print(f"\n🎯 Ready for deployment!")
        print(f"Package: {zip_file.absolute()}")
        
    except Exception as e:
        print(f"❌ Error creating package: {e}")
        import traceback
        traceback.print_exc()