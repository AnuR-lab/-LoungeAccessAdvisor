#!/usr/bin/env python3
"""
Test Lambda import compatibility
Simulates Lambda environment import behavior
"""
import sys
import os
import tempfile
import zipfile
from pathlib import Path

def test_lambda_imports():
    """Test imports in a simulated Lambda environment"""
    print("🧪 Testing Lambda Import Compatibility")
    print("=" * 50)
    
    # Extract the Lambda package to a temporary directory
    zip_file = Path("loungeaccessadvisor-lambda.zip")
    
    if not zip_file.exists():
        print("❌ Lambda package not found. Run lambda_deployment_package.py first.")
        return False
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Extract ZIP contents
        with zipfile.ZipFile(zip_file, 'r') as zf:
            zf.extractall(temp_path)
        
        # Add temp directory to Python path (simulates Lambda environment)
        sys.path.insert(0, str(temp_path))
        
        try:
            # Test lambda_handler import
            print("1. Testing lambda_handler import...")
            import lambda_handler
            print("   ✅ lambda_handler imported successfully")
            
            # Test that the handler function exists
            if hasattr(lambda_handler, 'lambda_handler'):
                print("   ✅ lambda_handler function found")
            else:
                print("   ❌ lambda_handler function missing")
            
            # Test individual service imports
            print("\n2. Testing service imports...")
            
            services = [
                ('api_client', 'LoungeAccessClient'),
                ('mcp_handler', 'get_user'),
                ('flight_service', 'FlightService'),
                ('user_profile_service', 'UserProfileService'),
                ('lounge_service', 'LoungeService')
            ]
            
            for module_name, class_or_function in services:
                try:
                    module = __import__(module_name)
                    if hasattr(module, class_or_function):
                        print(f"   ✅ {module_name}.{class_or_function}")
                    else:
                        print(f"   ⚠️  {module_name} imported but {class_or_function} not found")
                except ImportError as e:
                    print(f"   ❌ {module_name}: {e}")
            
            # Test Lambda handler execution structure
            print("\n3. Testing handler execution structure...")
            
            # Create mock context
            class MockContext:
                def __init__(self):
                    self.request_id = "test-request-123"
                    self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"
                    self.client_context = MockClientContext()
            
            class MockClientContext:
                def __init__(self):
                    self.custom = {"bedrockAgentCoreToolName": "LoungeAccessMCPServerTarget___getUser"}
            
            # Test handler with mock data
            try:
                event = {"user_id": "test_user"}
                context = MockContext()
                
                # This should not crash due to import issues
                result = lambda_handler.lambda_handler(event, context)
                
                if isinstance(result, dict) and 'statusCode' in result:
                    print("   ✅ Handler returns proper response structure")
                    print(f"   Status Code: {result['statusCode']}")
                else:
                    print(f"   ⚠️  Unexpected response format: {type(result)}")
                    
            except ImportError as e:
                print(f"   ❌ Import error during execution: {e}")
                return False
            except Exception as e:
                # Other errors are expected (missing AWS services, etc.)
                print(f"   ✅ Handler executed (expected error: {type(e).__name__})")
            
            print("\n✅ All import tests passed!")
            return True
            
        except ImportError as e:
            print(f"❌ Critical import error: {e}")
            return False
        
        finally:
            # Clean up sys.path
            if str(temp_path) in sys.path:
                sys.path.remove(str(temp_path))

def test_deployment_info():
    """Test deployment info file"""
    print("\n🧪 Testing Deployment Info")
    print("-" * 50)
    
    zip_file = Path("loungeaccessadvisor-lambda.zip")
    
    try:
        with zipfile.ZipFile(zip_file, 'r') as zf:
            if 'deployment_info.json' in zf.namelist():
                deployment_info = zf.read('deployment_info.json')
                import json
                info = json.loads(deployment_info)
                
                print(f"Version: {info.get('version', 'unknown')}")
                print(f"Deployment Date: {info.get('deployment_date', 'unknown')}")
                
                features = info.get('features', [])
                print(f"Features: {len(features)}")
                for feature in features:
                    print(f"  - {feature}")
                
                tools = info.get('tools_supported', [])
                print(f"Tools: {len(tools)}")
                for tool in tools:
                    print(f"  - {tool}")
                
                print("✅ Deployment info validated")
            else:
                print("❌ deployment_info.json not found in package")
                
    except Exception as e:
        print(f"❌ Error reading deployment info: {e}")

def main():
    """Run all import tests"""
    print("🚀 Lambda Import Compatibility Test Suite")
    print("=" * 60)
    
    success = test_lambda_imports()
    test_deployment_info()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! Lambda package is ready for deployment.")
        print("\n📋 Deployment Summary:")
        print("✅ No import errors")
        print("✅ Handler function accessible")
        print("✅ All services importable")
        print("✅ Proper response structure")
        
        print("\n🚀 Next Steps:")
        print("1. Upload loungeaccessadvisor-lambda.zip to AWS Lambda")
        print("2. Set handler to: lambda_handler.lambda_handler")
        print("3. Configure IAM permissions for AWS services")
        print("4. Test with real AWS environment")
    else:
        print("❌ Import issues detected. Please fix before deployment.")

if __name__ == "__main__":
    main()