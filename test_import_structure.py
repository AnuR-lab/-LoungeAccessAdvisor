#!/usr/bin/env python3
"""
Simple Lambda import structure test - focuses on module structure without AWS dependencies
"""
import sys
import os
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock

def test_import_structure():
    """Test that the Lambda package has the correct import structure"""
    print("🧪 Testing Lambda Module Structure")
    print("=" * 45)
    
    zip_file = Path("loungeaccessadvisor-lambda.zip")
    
    if not zip_file.exists():
        print("❌ Lambda package not found. Please create it first.")
        return False
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Extract ZIP
        with zipfile.ZipFile(zip_file, 'r') as zf:
            zf.extractall(temp_path)
        
        # Check that all required files are present
        required_files = [
            '__init__.py',
            'lambda_handler.py',
            'mcp_handler.py',
            'api_client.py',
            'requirements.txt'
        ]
        
        print("📁 Checking file structure...")
        missing_files = []
        for file_name in required_files:
            file_path = temp_path / file_name
            if file_path.exists():
                print(f"   ✅ {file_name}")
            else:
                print(f"   ❌ {file_name} (MISSING)")
                missing_files.append(file_name)
        
        if missing_files:
            print(f"\n❌ Missing files: {missing_files}")
            return False
        
        # Add to Python path
        sys.path.insert(0, str(temp_path))
        
        try:
            # Mock boto3 and other AWS dependencies
            with patch.dict('sys.modules', {
                'boto3': MagicMock(),
                'botocore': MagicMock(),
                'botocore.exceptions': MagicMock()
            }):
                
                print("\n📦 Testing imports (with mocked AWS)...")
                
                # Test mcp_handler import
                import mcp_handler
                print("   ✅ mcp_handler imported")
                
                # Check that key functions exist
                expected_functions = [
                    'get_user',
                    'get_lounges_with_access_rules',
                    'get_flight_aware_lounge_recommendations',
                    'analyze_layover_lounge_strategy'
                ]
                
                for func_name in expected_functions:
                    if hasattr(mcp_handler, func_name):
                        print(f"   ✅ {func_name} function found")
                    else:
                        print(f"   ❌ {func_name} function missing")
                        return False
                
                # Test lambda_handler import
                import lambda_handler
                print("   ✅ lambda_handler imported")
                
                if hasattr(lambda_handler, 'lambda_handler'):
                    print("   ✅ lambda_handler.lambda_handler function found")
                else:
                    print("   ❌ lambda_handler.lambda_handler function missing")
                    return False
                
                print("\n🎉 All module structure tests passed!")
                return True
                
        except Exception as e:
            print(f"\n❌ Import error: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            # Clean up sys.path
            if str(temp_path) in sys.path:
                sys.path.remove(str(temp_path))

if __name__ == "__main__":
    success = test_import_structure()
    if success:
        print("\n✅ Lambda package structure is correct!")
        print("   Ready for AWS Lambda deployment!")
        exit(0)
    else:
        print("\n❌ Lambda package has structural issues!")
        exit(1)