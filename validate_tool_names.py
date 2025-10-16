#!/usr/bin/env python3
"""
Validate MCP tool names for AWS Bedrock compliance
"""
import json
import os

def validate_tool_name(tool_name, prefix="LoungeAccessMCPServerTarget___"):
    """Validate that tool name meets AWS Bedrock 64-character limit"""
    full_name = f"{prefix}{tool_name}"
    is_valid = len(full_name) <= 64
    status = "✅" if is_valid else "❌"
    print(f"{tool_name:30} | {len(full_name):2} chars | {status}")
    return is_valid

def validate_mcp_tool_files():
    """Validate all MCP tool definition files"""
    print("🔍 Validating MCP Tool Names for AWS Bedrock Compliance")
    print("=" * 60)
    print(f"{'Tool Name':30} | {'Length':8} | {'Status'}")
    print("-" * 60)
    
    mcp_tools_dir = "mcp_tools"
    all_valid = True
    
    if os.path.exists(mcp_tools_dir):
        for filename in os.listdir(mcp_tools_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(mcp_tools_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        tool_def = json.load(f)
                        tool_name = tool_def.get('name', 'UNKNOWN')
                        is_valid = validate_tool_name(tool_name)
                        if not is_valid:
                            all_valid = False
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
                    all_valid = False
    
    print("-" * 60)
    
    # Test some common tool names that might exist
    print("\n🧪 Testing Common Tool Names:")
    print("-" * 60)
    common_tools = [
        "getUser",
        "getLounges", 
        "getLoungesWithAccessRules",
        "searchFlights",
        "getFlightStatus"
    ]
    
    for tool in common_tools:
        validate_tool_name(tool)
    
    print("-" * 60)
    
    if all_valid:
        print("🎉 All tool names are compliant with AWS Bedrock 64-character limit!")
    else:
        print("⚠️  Some tool names exceed the 64-character limit and need shortening.")
    
    print(f"\n📏 AWS Bedrock Limit: 64 characters")
    print(f"🏷️  Prefix Length: {len('LoungeAccessMCPServerTarget___')} characters")
    print(f"✂️  Max Tool Name: {64 - len('LoungeAccessMCPServerTarget___')} characters")
    
    return all_valid

if __name__ == "__main__":
    validate_mcp_tool_files()