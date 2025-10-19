# MCP Tool Name Mapping for AWS Bedrock Validation

## Tool Name Length Constraints
AWS Bedrock has a 64-character limit for tool names. When using AgentCore Gateway, the actual tool name becomes:
`LoungeAccessMCPServerTarget___[toolName]`

This means our tool names must be ≤ 32 characters to avoid validation errors.

## Updated Tool Names (✅ Compliant)

### 1. Flight-Aware Lounge Recommendations
- **Original**: `getFlightAwareLoungeRecommendations` (35 chars) ❌
- **Updated**: `getFlightLoungeRecs` (18 chars) ✅
- **Full Name**: `LoungeAccessMCPServerTarget___getFlightLoungeRecs` (50 chars) ✅

### 2. Layover Strategy Analysis  
- **Original**: `analyzeLayoverLoungeStrategy` (28 chars) ✅
- **Updated**: `analyzeLayoverStrategy` (21 chars) ✅  
- **Full Name**: `LoungeAccessMCPServerTarget___analyzeLayoverStrategy` (53 chars) ✅

### 3. Flight Search with Lounge Optimization
- **Original**: `searchFlightsWithLoungeOptimization` (35 chars) ❌
- **Updated**: `searchFlightsOptimized` (21 chars) ✅
- **Full Name**: `LoungeAccessMCPServerTarget___searchFlightsOptimized` (53 chars) ✅

## Existing Tools (Need Verification)

### 4. Basic Lounge Search
- **Likely Name**: `getLoungesWithAccessRules` (24 chars) ✅
- **Full Name**: `LoungeAccessMCPServerTarget___getLoungesWithAccessRules` (56 chars) ✅

### 5. User Profile
- **Likely Name**: `getUser` (7 chars) ✅
- **Full Name**: `LoungeAccessMCPServerTarget___getUser` (39 chars) ✅

## Tool Function Mapping

| Short Name | Function | Description |
|------------|----------|-------------|
| `getFlightLoungeRecs` | `get_flight_aware_lounge_recommendations()` | Real-time flight + lounge optimization |
| `analyzeLayoverStrategy` | `analyze_layover_lounge_strategy()` | Multi-flight connection planning |
| `searchFlightsOptimized` | `search_flights_for_lounge_optimization()` | Flight search ranked by lounge access |
| `getLoungesWithAccessRules` | `get_lounges_with_access_rules()` | Basic airport lounge lookup |
| `getUser` | `get_user()` | User profile and membership info |

## Deployment Notes

1. **AgentCore Gateway Configuration**: Use the short names when registering tools
2. **Lambda Function Names**: Can remain descriptive (no length limit)
3. **MCP Handler Functions**: Keep existing function names for code clarity
4. **Tool Descriptions**: Can be detailed (no length limit on descriptions)

## Error Resolution

The original error:
```
Value 'LoungeAccessMCPServerTarget___getFlightAwareLoungeRecommendations' at 'toolConfig.tools.4.member.toolSpec.name' failed to satisfy constraint: Member must have length less than or equal to 64
```

Is now resolved with:
```
LoungeAccessMCPServerTarget___getFlightLoungeRecs (50 characters) ✅
```

## Testing Tool Names

To verify tool name compliance:
```python
def validate_tool_name(tool_name, prefix="LoungeAccessMCPServerTarget___"):
    full_name = f"{prefix}{tool_name}"
    is_valid = len(full_name) <= 64
    print(f"{tool_name}: {len(full_name)} chars - {'✅' if is_valid else '❌'}")
    return is_valid

# Test all tools
tools = [
    "getFlightLoungeRecs",
    "analyzeLayoverStrategy", 
    "searchFlightsOptimized",
    "getLoungesWithAccessRules",
    "getUser"
]

for tool in tools:
    validate_tool_name(tool)
```

All updated tool names are now compliant with AWS Bedrock's 64-character limit.