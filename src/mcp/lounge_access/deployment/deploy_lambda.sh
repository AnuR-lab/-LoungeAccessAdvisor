#!/bin/bash

# LoungeAccessAdvisor Lambda Deployment Script
# This script packages and deploys the Lambda function using CloudFormation

set -e

# Configuration
ENVIRONMENT=${ENVIRONMENT:-dev}
DYNAMODB_STACK_NAME=${DYNAMODB_STACK_NAME:-loungeaccess-dynamodb-${ENVIRONMENT}}
LAMBDA_STACK_NAME=${LAMBDA_STACK_NAME:-loungeaccess-lambda-${ENVIRONMENT}}
AWS_REGION=${AWS_REGION:-us-east-1}

echo "Deploying Lambda function for LoungeAccessAdvisor..."
echo "Environment: $ENVIRONMENT"
echo "Region: $AWS_REGION"
echo "DynamoDB Stack: $DYNAMODB_STACK_NAME"

# Create deployment directory
DEPLOY_DIR="lambda-deployment-$(date +%s)"
mkdir -p $DEPLOY_DIR
cd $DEPLOY_DIR

# Copy required files
echo "Copying source files..."
cp ../api_client.py .
cp ../lambda_handler.py .
cp ../mcp_handler.py .
cp ../user_profile_service.py .

# Create requirements.txt for Lambda dependencies
cat > requirements.txt << EOF
boto3>=1.34.0
botocore>=1.34.0
EOF

# Install dependencies if requirements exist
if [ -f requirements.txt ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt -t .
fi

# Create ZIP package
echo "Creating deployment package..."
zip -r lambda-deployment.zip . -x "*.pyc" "__pycache__/*" "*.git*"

# Upload to S3 (optional, for larger packages)
BUCKET_NAME="loungeaccess-lambda-deployments-${AWS_REGION}"
S3_KEY="lambda-packages/lounge-access-mcp-${ENVIRONMENT}-$(date +%s).zip"

# Check if S3 bucket exists, create if not
if ! aws s3 ls "s3://$BUCKET_NAME" 2>/dev/null; then
    echo "Creating S3 bucket for Lambda deployments..."
    aws s3 mb "s3://$BUCKET_NAME" --region $AWS_REGION
fi

# Upload package to S3
echo "Uploading package to S3..."
aws s3 cp lambda-deployment.zip "s3://$BUCKET_NAME/$S3_KEY"

# Deploy Lambda function using CloudFormation
echo "Deploying Lambda function via CloudFormation..."
aws cloudformation deploy \
    --template-file ../IaC/lambda_iam_role.yaml \
    --stack-name $LAMBDA_STACK_NAME \
    --parameter-overrides \
        Environment=$ENVIRONMENT \
        DynamoDBStackName=$DYNAMODB_STACK_NAME \
    --capabilities CAPABILITY_NAMED_IAM \
    --region $AWS_REGION

# Update Lambda function code
FUNCTION_NAME=$(aws cloudformation describe-stacks \
    --stack-name $LAMBDA_STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunctionName`].OutputValue' \
    --output text \
    --region $AWS_REGION)

echo "Updating Lambda function code..."
aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --s3-bucket $BUCKET_NAME \
    --s3-key $S3_KEY \
    --region $AWS_REGION

# Wait for update to complete
echo "Waiting for Lambda update to complete..."
aws lambda wait function-updated \
    --function-name $FUNCTION_NAME \
    --region $AWS_REGION

# Get function ARN
FUNCTION_ARN=$(aws cloudformation describe-stacks \
    --stack-name $LAMBDA_STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunctionArn`].OutputValue' \
    --output text \
    --region $AWS_REGION)

echo "Lambda function deployed successfully!"
echo "Function ARN: $FUNCTION_ARN"
echo "Function Name: $FUNCTION_NAME"

# Update target_payload.json with new Lambda ARN
echo "Updating target_payload.json..."
cat > ../IaC/target_payload.json << EOF
{
  "lambdaArn": "$FUNCTION_ARN",
  "toolSchema": {
    "inlinePayload": [
      {
        "name": "tool_example_1",
        "description": "An example tool that takes no input parameters.",
        "inputSchema": {
          "type": "object",
          "properties": {},
          "required": []
        }
      },
      {
        "name": "tool_example_2",
        "description": "An example tool that takes two string parameters.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "parameter_1": {"type": "string"},
            "parameter_2": {"type": "string"}
          },
          "required": ["parameter_1", "parameter_2"]
        }
      },
      {
        "name": "get_user",
        "description": "Retrieves user information including name, home airport, and memberships based on user ID.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "user_id": {
              "type": "string",
              "description": "The unique identifier for the user"
            }
          },
          "required": ["user_id"]
        }
      }
    ]
  }
}
EOF

# Cleanup
cd ..
rm -rf $DEPLOY_DIR

echo "Deployment completed successfully!"
echo "Next steps:"
echo "1. Deploy AgentCore Gateway using the updated target_payload.json"
echo "2. Configure environment variables in your Streamlit application"
