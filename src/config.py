"""
Configuration management for LoungeAccessAdvisor.
Handles environment variables and application settings.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for LoungeAccessAdvisor application."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Environment settings
        self.environment = os.getenv('ENVIRONMENT', 'dev')
        self.aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        
        # DynamoDB Configuration
        self.dynamodb_table_name = os.getenv('DYNAMODB_TABLE_NAME', 'UserProfile')
        self.dynamodb_region = os.getenv('DYNAMODB_REGION', self.aws_region)
        
        # Bedrock Configuration
        self.bedrock_model_id = os.getenv('BEDROCK_MODEL_ID', 'us.anthropic.claude-sonnet-4-20250514-v1:0')
        self.bedrock_region = os.getenv('BEDROCK_REGION', self.aws_region)
        
        # AgentCore Gateway Configuration
        self.mcp_gateway_url = os.getenv('MCP_GATEWAY_URL')
        self.cognito_client_id = os.getenv('COGNITO_CLIENT_ID')
        self.cognito_client_secret = os.getenv('COGNITO_CLIENT_SECRET')
        self.cognito_token_url = os.getenv('COGNITO_TOKEN_URL')
        
        # Streamlit Configuration
        self.streamlit_port = int(os.getenv('STREAMLIT_SERVER_PORT', '8501'))
        self.streamlit_address = os.getenv('STREAMLIT_SERVER_ADDRESS', '0.0.0.0')
        
        # Lambda Configuration
        self.lambda_function_name = os.getenv('LAMBDA_FUNCTION_NAME', 'lounge-access-mcp-dev')
        self.lambda_timeout = int(os.getenv('LAMBDA_TIMEOUT', '300'))
        self.lambda_memory_size = int(os.getenv('LAMBDA_MEMORY_SIZE', '512'))
        
        # Logging Configuration
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.debug_logging = os.getenv('ENABLE_DEBUG_LOGGING', 'false').lower() == 'true'
        
        # Security Configuration
        self.enable_https = os.getenv('ENABLE_HTTPS', 'false').lower() == 'true'
        self.ssl_cert_path = os.getenv('SSL_CERT_PATH')
        self.ssl_key_path = os.getenv('SSL_KEY_PATH')
        
        # Performance Configuration
        self.cache_ttl_seconds = int(os.getenv('CACHE_TTL_SECONDS', '300'))
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == 'dev'
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == 'prod'
    
    @property
    def mcp_enabled(self) -> bool:
        """Check if MCP client configuration is complete."""
        return all([
            self.mcp_gateway_url,
            self.cognito_client_id,
            self.cognito_client_secret,
            self.cognito_token_url
        ])
    
    def get_dynamodb_config(self) -> Dict[str, Any]:
        """Get DynamoDB configuration dictionary."""
        return {
            'table_name': self.dynamodb_table_name,
            'region_name': self.dynamodb_region
        }
    
    def get_bedrock_config(self) -> Dict[str, Any]:
        """Get Bedrock configuration dictionary."""
        return {
            'model_id': self.bedrock_model_id,
            'region_name': self.bedrock_region
        }
    
    def get_mcp_config(self) -> Optional[Dict[str, str]]:
        """Get MCP client configuration dictionary."""
        if not self.mcp_enabled:
            return None
        
        return {
            'mcp_gateway_url': self.mcp_gateway_url,
            'client_id': self.cognito_client_id,
            'client_secret': self.cognito_client_secret,
            'token_url': self.cognito_token_url
        }
    
    def get_lambda_config(self) -> Dict[str, Any]:
        """Get Lambda configuration dictionary."""
        return {
            'function_name': self.lambda_function_name,
            'timeout': self.lambda_timeout,
            'memory_size': self.lambda_memory_size,
            'region': self.aws_region
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate the current configuration and return status."""
        issues = []
        warnings = []
        
        # Check required AWS configuration
        if not self.aws_region:
            issues.append("AWS_DEFAULT_REGION not set")
        
        if not self.dynamodb_table_name:
            issues.append("DYNAMODB_TABLE_NAME not set")
        
        # Check optional MCP configuration
        if not self.mcp_enabled:
            warnings.append("MCP client configuration incomplete - running without MCP tools")
        
        # Check Bedrock configuration
        if not self.bedrock_model_id:
            warnings.append("BEDROCK_MODEL_ID not set - using default")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'environment': self.environment,
            'mcp_enabled': self.mcp_enabled
        }
    
    def get_health_info(self) -> Dict[str, Any]:
        """Get configuration health information."""
        validation = self.validate_configuration()
        
        return {
            'environment': self.environment,
            'aws_region': self.aws_region,
            'dynamodb_table': self.dynamodb_table_name,
            'bedrock_model': self.bedrock_model_id,
            'mcp_enabled': self.mcp_enabled,
            'configuration_valid': validation['valid'],
            'issues': validation['issues'],
            'warnings': validation['warnings']
        }
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return f"Config(environment={self.environment}, region={self.aws_region}, table={self.dynamodb_table_name})"


# Global configuration instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config


def reload_config() -> Config:
    """Reload configuration from environment variables."""
    global config
    # Reload environment variables
    load_dotenv(override=True)
    config = Config()
    return config