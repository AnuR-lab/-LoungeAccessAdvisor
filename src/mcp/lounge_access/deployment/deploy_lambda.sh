# copy files to the folder
cp ../api_client .
cp ../lambda_handler.txt .
cp ../mcp_handler.py .

# Create a ZIP package
zip -r atpco-lounge-access-lambda.zip .

# Create the Lambda function
aws lambda create-function \
  --function-name atpco-lounge-access-mcp-us-east-1 \
  --runtime python3.11 \
  --role  arn:aws:iam::905418267822:role/atpco-mcp-lambda-role \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://atpco-lounge-access-lambda.zip \
  --timeout 300 \
  --memory-size 512
