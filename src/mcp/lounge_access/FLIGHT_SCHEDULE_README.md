# Flight Schedule Integration - LoungeAccessAdvisor

## Overview
This document describes the integration of Amadeus Flight Schedule API into the LoungeAccessAdvisor MCP tool. The integration allows users to retrieve flight schedule information and correlate it with available lounges at departure and arrival airports.

## New Functionality

### Flight Schedule API
The new `get_flight_schedule` tool provides access to Amadeus Flight Schedule API (v2/schedule/flights) with the following capabilities:

- **Flight Information Retrieval**: Get detailed schedule information for specific flights
- **Lounge Correlation**: Automatically check for lounge availability at departure and arrival airports
- **Parameter Validation**: Validate input parameters before making API calls
- **Error Handling**: Comprehensive error handling with meaningful error messages

## API Parameters

### Required Parameters
- **carrier_code** (string): IATA carrier code (2 characters, e.g., 'AA', 'DL', 'UA')
- **flight_number** (string): Flight number (numeric, e.g., '1234')
- **scheduled_departure_date** (string): Departure date in YYYY-MM-DD format (local to departure airport)

### Optional Parameters
- **operational_suffix** (string): Operational suffix for flights like 'A' or 'B'

## Integration Architecture

### Files Added/Modified

1. **flights_api_client.py** (NEW)
   - Handles Amadeus API authentication and requests
   - OAuth2 client credentials flow
   - Token caching for performance
   - Comprehensive error handling

2. **mcp_handler.py** (MODIFIED)
   - Added `get_flight_schedule()` function
   - Integrates flight data with lounge availability
   - Returns enhanced response with lounge information

3. **lambda_handler.py** (MODIFIED)
   - Added "get_flight_schedule" case
   - Parameter validation
   - Error response handling

4. **api_client.py** (MODIFIED)
   - Integrated FlightsApiClient
   - Added flight schedule methods to LoungeAccessClient

5. **test_flight_schedule.py** (NEW)
   - Comprehensive unit tests
   - Mock testing for API calls
   - Lambda handler testing

## Usage Examples

### Basic Flight Schedule Query
```json
{
  "carrier_code": "AA",
  "flight_number": "1234",
  "scheduled_departure_date": "2025-12-25"
}
```

### Flight Schedule with Operational Suffix
```json
{
  "carrier_code": "UA",
  "flight_number": "567",
  "scheduled_departure_date": "2025-12-25",
  "operational_suffix": "A"
}
```

### Lambda Test Context
```json
{
  "clientContext": {
    "custom": {
      "bedrockAgentCoreToolName": "get_flight_schedule"
    }
  }
}
```

## Response Format

### Successful Response
```json
{
  "statusCode": 200,
  "body": {
    "result": {
      "flight_info": {
        "carrier_code": "AA",
        "flight_number": "1234",
        "scheduled_departure_date": "2025-12-25",
        "departure_airport": "JFK",
        "arrival_airport": "LAX",
        "departure": { /* Departure details */ },
        "arrival": { /* Arrival details */ },
        "aircraft": { /* Aircraft details */ },
        "status": "success"
      },
      "departure_airport": "JFK",
      "arrival_airport": "LAX",
      "departure_lounges_available": true,
      "arrival_lounges_available": true,
      "status": "success"
    }
  }
}
```

### Error Response
```json
{
  "statusCode": 400,
  "body": {
    "error": "Missing required parameters: carrier_code, flight_number, scheduled_departure_date"
  }
}
```

## Authentication & Configuration

### AWS Secrets Manager
The integration uses the same Amadeus credentials as the AutoRescue project:
- **Secret Name**: `autorescue/amadeus/credentials`
- **Format**: JSON with `client_id` and `client_secret`

### Environment Variables
- **AWS_REGION**: AWS region for Secrets Manager (default: us-east-1)
- **AMADEUS_BASE_URL**: Amadeus API base URL (default: https://test.api.amadeus.com)

## Deployment

### Lambda Package Dependencies
The following files must be included in the Lambda deployment package:
- `flights_api_client.py`
- `mcp_handler.py` (updated)
- `lambda_handler.py` (updated)
- `api_client.py` (updated)
- All existing lounge access files

### PowerShell Deployment Script
The existing `deploy_lambda.ps1` script has been updated to include the new files:
```powershell
.\deploy_lambda.ps1
```

## Testing

### Unit Tests
Run the comprehensive test suite:
```bash
python -m pytest test_flight_schedule.py -v
```

### Lambda Testing
Use the provided test events in the `test_events/` directory:
- `flight_schedule_test.json`
- `flight_schedule_with_suffix_test.json`

### Integration Testing
1. Deploy the updated Lambda function
2. Test with AWS Lambda console using test events
3. Verify Amadeus API connectivity
4. Confirm lounge data correlation

## Error Handling

The integration includes comprehensive error handling for:
- **Authentication Errors**: Invalid or expired Amadeus credentials
- **Parameter Validation**: Missing or invalid input parameters
- **API Errors**: Amadeus API failures or rate limiting
- **Network Errors**: Connection timeouts or network issues
- **Data Errors**: Malformed API responses

## Performance Considerations

### Caching Strategy
- **Token Caching**: OAuth tokens cached for 25 minutes
- **Credentials Caching**: AWS Secrets Manager responses cached for 1 hour
- **Lambda Container Reuse**: Leverages Lambda container reuse for performance

### Rate Limiting
- Amadeus API has rate limits that are handled gracefully
- Token refresh is automatic when needed
- Error responses include retry guidance

## Future Enhancements

### Potential Improvements
1. **Flight Status Integration**: Add real-time flight status information
2. **Route Analysis**: Analyze common routes for lounge recommendations
3. **Historical Data**: Track flight patterns for better lounge suggestions
4. **Multi-leg Flights**: Support for connecting flights and layover lounges
5. **Airline Alliance Integration**: Enhanced lounge access based on airline partnerships

### Monitoring & Observability
- CloudWatch logs for API calls and performance
- Error tracking and alerting
- Usage metrics and analytics

## Troubleshooting

### Common Issues
1. **Credentials Error**: Verify Amadeus credentials in AWS Secrets Manager
2. **Date Format**: Ensure date is in YYYY-MM-DD format
3. **Carrier Code**: Use valid IATA 2-letter carrier codes
4. **Flight Number**: Use numeric flight numbers only

### Debug Information
- Lambda logs include detailed request/response information
- Error messages provide specific guidance for resolution
- Test events can be used to isolate issues