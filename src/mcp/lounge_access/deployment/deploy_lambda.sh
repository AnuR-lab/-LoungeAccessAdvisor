# copy files to the folder
cp ../api_client.py .
cp ../lambda_handler.py .
cp ../mcp_handler.py .

# Create a ZIP package
zip -r atpco-lounge-access-lambda.zip .

# Update the Lambda function code
aws lambda update-function-code \
  --function-name atpco-lounge-access-mcp-us-east-1 \
  --zip-file fileb://atpco-lounge-access-lambda.zip
