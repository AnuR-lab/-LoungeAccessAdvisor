#!/bin/bash

# copy files to the folder
rm *.zip

cp ../api_client.py .
cp ../lambda_handler.py .
cp ../mcp_handler.py .
cp ../lounge_service.py .
cp ../user_profile_service.py .

# Create a ZIP package
zip -r atpco-lounge-access-lambda.zip *.py

# Update the Lambda function code
aws lambda update-function-code \
  --function-name atpco-lounge-access-mcp-us-east-1 \
  --zip-file fileb://atpco-lounge-access-lambda.zip

rm *.py



