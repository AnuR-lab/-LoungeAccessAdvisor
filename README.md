# Lounge Access Advisor ✈️

> AI-powered Travel Lounge Assistant using AWS Bedrock and Streamlit

Lounge Access Advisor is an intelligent chatbot that helps travelers discover airport lounge access information, check credit card benefits, and get personalized travel recommendations. Built with Claude Sonnet 4 and featuring a modern Streamlit interface.

## 🎯 Project Goals

- Help travelers quickly determine airport lounge eligibility based on flight details, loyalty status, and credit card memberships.
- Provide a delightful chat experience powered by Claude Sonnet 4 with real‑time streaming and reliable tool use.
- Orchestrate calls to external services via Model Context Protocol (MCP) tools and a lightweight API client layer.
- Offer a secure, session‑based web experience (Streamlit) with authentication and chat history persistence.
- Deliver deployable building blocks for AWS (Lambda + IAM + Gateway), including simple example tools and tests.
 
## 🌟 Features

- **Intelligent Chatbot** - Conversational AI powered by Claude Sonnet 4
- **Lounge Information** - Get access details for airport lounges worldwide
- **Credit Card Benefits** - Check lounge eligibility based on your cards
- **Real-time Streaming** - Token-by-token response streaming for better UX
- **Human Handoff** - Seamless human-in-the-loop capability for complex queries
- **Secure Authentication** - SHA256-encrypted login system
- **Session Persistence** - Maintains chat history throughout your session

## 🏗️ Architecture

```
User Interface (Streamlit) → AI Agent (Claude Sonnet 4) → MCP Tools → External APIs/Services
```

**Components:**
- **Streamlit Web App** - Modern, responsive user interface
- **Claude Sonnet 4** - Advanced AI model for natural conversations  
- **Strands Agent Framework** - Conversation management and tool orchestration
- **MCP Integration** - Model Context Protocol for external tool calling
- **AWS Infrastructure** - EC2 deployment with CloudFormation

## ⚡ AgentCore Wiring

### Agent Registration

```python
from strands_agents import AgentCore

# Initialize AgentCore with Bedrock Claude Sonnet 4
agent = AgentCore(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    region="us-east-1",
    service="bedrock-runtime",
    memory_config={
        "short_term_memory": True,
        "long_term_memory": True,
        "conversation_strategy": "adaptive"
    }
)
```

### MCP Tool Schema Example

```python
# Lounge lookup tool schema
{
    "name": "get_lounge_info",
    "description": "Get detailed information about airport lounges including access requirements, amenities, and location details",
    "inputSchema": {
        "type": "object",
        "properties": {
            "airport_code": {
                "type": "string",
                "description": "3-letter IATA airport code (e.g., 'JFK', 'LAX')"
            },
            "terminal": {
                "type": "string", 
                "description": "Terminal identifier (optional)"
            },
            "user_memberships": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of credit cards or loyalty programs"
            }
        },
        "required": ["airport_code"]
    }
}
```

### Bedrock Model Configuration

- **Model**: Claude Sonnet 4 (`us.anthropic.claude-sonnet-4-20250514-v1:0`)
- **Region**: `us-east-1`
- **Service**: `bedrock-runtime`
- **Memory**: AgentCore Memory with adaptive conversation strategies

## 📊 CloudWatch Logging & Monitoring

### Logging Fields

```json
{
  "run_id": "uuid-4-conversation-session",
  "tool_name": "get_lounge_info",
  "latency_ms": 1250,
  "input_tokens": 145,
  "output_tokens": 320,
  "estimated_cost_usd": 0.0023,
  "timestamp": "2025-01-15T10:30:45Z",
  "user_id": "hashed-user-identifier",
  "success": true,
  "error_code": null
}
```

### Basic Traces

```python
# AgentCore trace example
{
  "trace_id": "trace-abc123",
  "span_id": "span-def456", 
  "operation": "tool_execution",
  "duration_ms": 850,
  "tool_calls": [
    {
      "tool": "get_lounge_info",
      "input": {"airport_code": "JFK", "terminal": "4"},
      "output_size_bytes": 2048,
      "cache_hit": false
    }
  ],
  "bedrock_request_id": "bedrock-req-789xyz"
}
```

### System Limits & Controls

```python
# AgentCore configuration limits
AGENT_LIMITS = {
    "max_steps_per_conversation": 50,
    "max_tokens_per_request": 8192,
    "max_tool_calls_per_step": 5,
    "conversation_timeout_minutes": 30,
    "retry_attempts": 3,
    "exponential_backoff_base": 2
}

# Async processing with DLQ
ASYNC_CONFIG = {
    "enable_async_tools": True,
    "sqs_queue_url": "https://sqs.us-east-1.amazonaws.com/123456789/lounge-advisor-queue",
    "dlq_url": "https://sqs.us-east-1.amazonaws.com/123456789/lounge-advisor-dlq",
    "max_retry_attempts": 3,
    "visibility_timeout_seconds": 300
}
```

### CloudWatch Metrics

- **Conversation Success Rate**: `LoungeAdvisor/ConversationSuccess`
- **Tool Execution Latency**: `LoungeAdvisor/ToolLatency`
- **Token Usage**: `LoungeAdvisor/TokenConsumption`
- **Cost Tracking**: `LoungeAdvisor/EstimatedCost`
- **Error Rate**: `LoungeAdvisor/ErrorRate`

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- AWS Account (for deployment)
- UV package manager (recommended)

### Local Development

```bash
# Clone the repository
git clone <repository-url>
cd -LoungeAccessAdvisor

# Install dependencies with UV (recommended)
uv venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

uv pip install -r pyproject.toml

# Or use pip
pip install -e .

# Run the application
streamlit run app.py
```

### Demo Credentials

For testing purposes, use these credentials:
- **Username**: `admin` | **Password**: `admin123`
- **Username**: `demo` | **Password**: `demo123`
- **Username**: `user` | **Password**: `password123`

## 📁 Project Structure

```
-LoungeAccessAdvisor/
├── README.md                    # Project documentation
├── app.py                       # Main Streamlit application
├── pyproject.toml              # Dependencies and project config
├── cloudformation.yaml         # AWS infrastructure template
│
├── src/                        # Source code
│   ├── auth.py                 # Authentication system
│   ├── login.py                # Login page interface
│   ├── home.py                 # Main chat interface
│   ├── chat.py                 # Chat logic and streaming
│   ├── mcp_client.py          # MCP client for tool integration
│   ├── system_prompts.py      # AI system prompts
│   │
│   └── mcp/                   # MCP tools
│       └── lounge_access/     # Lounge-specific tools
│           ├── lambda_handler.py    # AWS Lambda handler
│           ├── api_client.py        # External API client
│           ├── mcp_handler.py       # Tool implementations
│           └── deployment/          # Deployment scripts
│
└── .github/                   # CI/CD workflows
    └── workflows/
        └── deploy.yml         # Automated deployment
```

## 🛠️ Technology Stack

### Core Technologies
- **Frontend**: Streamlit 1.50.0
- **AI Model**: AWS Bedrock Claude Sonnet 4
- **Agent Framework**: Strands Agents 1.12.0
- **Authentication**: Custom SHA256-based system

### AWS Services
- **Bedrock**: Claude Sonnet 4 model hosting
- **EC2**: Application hosting
- **CloudFormation**: Infrastructure as Code
- **Lambda**: MCP tool execution (when enabled)

### Development Tools
- **UV**: Fast Python package manager
- **Watchdog**: File system monitoring
- **GitHub Actions**: CI/CD pipeline

## 🔧 Configuration

### Environment Variables

Create a `.env` file for configuration:

```env
# AWS Configuration
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0

# MCP Gateway (when enabled)
MCP_GATEWAY_URL=https://your-gateway-url.amazonaws.com/mcp
COGNITO_CLIENT_ID=your-client-id
COGNITO_CLIENT_SECRET=your-client-secret
TOKEN_URL=https://your-domain.auth.us-east-1.amazoncognito.com/oauth2/token
```

### Streamlit Configuration

The app is configured for:
- **Port**: 8501 (default Streamlit port)
- **Layout**: Wide layout for better chat experience
- **Theme**: Custom styling for professional appearance

## 🚀 Deployment

### AWS EC2 Deployment

Use the provided CloudFormation template:

```bash
# Deploy infrastructure
aws cloudformation create-stack \
  --stack-name lounge-access-advisor \
  --template-body file://cloudformation.yaml \
  --parameters ParameterKey=KeyName,ParameterValue=your-ec2-key

# Get public IP
aws cloudformation describe-stacks \
  --stack-name lounge-access-advisor \
  --query 'Stacks[0].Outputs[?OutputKey==`PublicIP`].OutputValue' \
  --output text
```

### Manual Deployment

```bash
# SSH to EC2 instance
ssh -i your-key.pem ec2-user@your-ec2-ip

# Application is auto-deployed at /home/ec2-user/app
# Access via: http://your-ec2-ip:8501
```

## 🧪 Development

### Adding New Tools

1. Create tool functions in `src/mcp/lounge_access/mcp_handler.py`
2. Add API client methods in `src/mcp/lounge_access/api_client.py` 
3. Update Lambda handler in `src/mcp/lounge_access/lambda_handler.py`
4. Enable MCP client in `src/chat.py`

### Testing

```bash
# Test authentication
python -c "from src.auth import verify_credentials; print(verify_credentials('demo', 'demo123'))"

# Test MCP tools (when implemented)
python src/mcp/lounge_access/test_lambda_handler.py
```

## 🔐 Security

### Authentication
- SHA256 password hashing
- Session-based authentication
- Secure credential storage (demo mode)

### AWS Security
- Security groups restrict access to SSH (22) and HTTP (8501)
- IAM roles with minimal required permissions
- VPC isolation (when deployed in VPC)

## 🎯 Use Cases

1. **Lounge Access Lookup**
   - "Which lounges can I access at JFK with my Chase Sapphire card?"
   - "Are there any Priority Pass lounges at London Heathrow Terminal 5?"

2. **Credit Card Benefits**
   - "What lounge access do I get with my American Express Platinum?"
   - "Can my guests access the lounge with me?"

3. **Travel Recommendations**
   - "Best lounges for a layover at Dubai International?"
   - "Quiet lounges with good WiFi for working?"

## 📊 Features Roadmap

- [ ] **Real Lounge Data Integration** - Connect to live lounge databases
- [ ] **Credit Card API Integration** - Real-time benefit verification
- [ ] **Location Services** - Airport terminal mapping
- [ ] **User Profiles** - Save preferences and travel history
- [ ] **Multi-language Support** - International traveler support
- [ ] **Mobile App** - React Native companion app

## 🐛 Troubleshooting

### Common Issues

**Login Issues**
```bash
# Check credentials in src/auth.py
# Ensure proper password hashing
```

**Streamlit Startup Issues**
```bash
# Check Python version
python --version  # Should be 3.12+

# Reinstall dependencies
uv pip install --force-reinstall streamlit
```

**AWS Deployment Issues**
```bash
# Check security group settings
# Verify EC2 instance is running
# Check application logs on EC2
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is part of the AWS Hackathon initiative. See individual file headers for specific licensing terms.

## 🙏 Acknowledgments

- AWS Bedrock team for Claude Sonnet 4 access
- Streamlit community for the excellent framework
- Strands team for the agent orchestration framework

---
**Built with ❤️ for travelers worldwide**
