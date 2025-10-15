#!/bin/bash

# Quick deployment script for AWS CI/CD Pipeline
# Run this to deploy the complete CI/CD infrastructure

set -e

echo "================================================"
echo "AWS CI/CD Pipeline Deployment Script"
echo "================================================"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed"
    echo "Install from: https://aws.amazon.com/cli/"
    exit 1
fi

echo "✅ AWS CLI found"

# Collect parameters
read -p "GitHub Owner (username): " GITHUB_OWNER
read -p "GitHub Repository name: " GITHUB_REPO
read -p "GitHub Branch [main]: " GITHUB_BRANCH
GITHUB_BRANCH=${GITHUB_BRANCH:-main}
read -sp "GitHub Personal Access Token: " GITHUB_TOKEN
echo ""
read -p "Stack Name [lounge-advisor-cicd]: " STACK_NAME
STACK_NAME=${STACK_NAME:-lounge-advisor-cicd}
read -p "AWS Region [us-east-1]: " AWS_REGION
AWS_REGION=${AWS_REGION:-us-east-1}
read -p "EC2 Instance Type [t2.micro]: " INSTANCE_TYPE
INSTANCE_TYPE=${INSTANCE_TYPE:-t2.micro}

echo ""
echo "================================================"
echo "Deployment Configuration:"
echo "================================================"
echo "GitHub Owner:     $GITHUB_OWNER"
echo "GitHub Repo:      $GITHUB_REPO"
echo "GitHub Branch:    $GITHUB_BRANCH"
echo "Stack Name:       $STACK_NAME"
echo "AWS Region:       $AWS_REGION"
echo "Instance Type:    $INSTANCE_TYPE"
echo "================================================"
echo ""

read -p "Deploy with these settings? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""
echo "🚀 Deploying CloudFormation stack..."
echo ""

# Deploy the stack
aws cloudformation create-stack \
  --stack-name $STACK_NAME \
  --template-body file://cicd-pipeline.yaml \
  --parameters \
    ParameterKey=GitHubOwner,ParameterValue=$GITHUB_OWNER \
    ParameterKey=GitHubRepo,ParameterValue=$GITHUB_REPO \
    ParameterKey=GitHubBranch,ParameterValue=$GITHUB_BRANCH \
    ParameterKey=GitHubToken,ParameterValue=$GITHUB_TOKEN \
    ParameterKey=EC2InstanceType,ParameterValue=$INSTANCE_TYPE \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $AWS_REGION

echo ""
echo "⏳ Waiting for stack creation to complete..."
echo "This will take 5-10 minutes..."
echo ""

aws cloudformation wait stack-create-complete \
  --stack-name $STACK_NAME \
  --region $AWS_REGION

echo ""
echo "================================================"
echo "✅ Deployment Complete!"
echo "================================================"
echo ""

# Get outputs
APPLICATION_URL=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $AWS_REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`ApplicationURL`].OutputValue' \
  --output text)

PIPELINE_URL=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $AWS_REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`PipelineURL`].OutputValue' \
  --output text)

echo "📱 Application URL: $APPLICATION_URL"
echo "🔗 Pipeline Console: $PIPELINE_URL"
echo ""
echo "================================================"
echo "Next Steps:"
echo "================================================"
echo "1. Open the Pipeline Console to monitor deployments"
echo "2. Make a commit to trigger the pipeline"
echo "3. Wait 5-7 minutes for initial deployment"
echo "4. Access your application at the URL above"
echo ""
echo "Note: It may take a few minutes for the application"
echo "to be fully accessible after the stack completes."
echo "================================================"