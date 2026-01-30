<p align="center">
  <img src="https://github.com/kaushikq-ravindran/secure-moltbot-bedrock/blob/main/images/3.png" alt="Secure MoltBot Bedrock" width="600"/>
</p>

<h1 align="center">🔐 Secure MoltBot on AWS Bedrock</h1>

<p align="center">
  <strong>Application-Level Security Enhancements for AI Agent Deployments</strong>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-security-enhancements">Security</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-deployment">Deployment</a> •
  <a href="#-documentation">Docs</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Security-Enhanced-brightgreen" alt="Security Enhanced"/>
  <img src="https://img.shields.io/badge/AWS-Bedrock-orange" alt="AWS Bedrock"/>
  <img src="https://img.shields.io/badge/License-MIT-blue" alt="MIT License"/>
</p>

---

## 🎯 What is This?

This is a **security-enhanced fork** of the [AWS Bedrock MoltBot template](https://github.com/aws-samples/sample-Moltbot-on-AWS-with-Bedrock), adding **application-level security controls**.

### The Problem

On **January 23, 2026**, the MoltBot security incident exposed **1,000+ gateways** due to a localhost bypass vulnerability:

```
Attacker → Reverse Proxy → Gateway (sees "localhost") → FULL ACCESS
                              ↓
                     API Keys Stolen, Commands Executed
```

### Our Solution

We implement **defense-in-depth** with 5 security modules that validate every request before it reaches Bedrock:

| Module | Purpose | File |
|--------|---------|------|
| **PermissionSystem** | Per-agent model/token limits | `permissions.py` |
| **ActionValidator** | Prompt injection detection | `action_validator.py` |
| **RateLimiter** | Cost/abuse protection | `rate_limiter.py` |
| **AuditLogger** | Append-only action logging | `audit_logger.py` |
| **SecurityMiddleware** | Orchestrates all checks | `bedrock_middleware.py` |

---

## 🚀 Quick Start

### One-Click Deploy

| Region | Launch Stack |
|--------|--------------|
| **US West (Oregon)** | [![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/review?stackName=secure-moltbot&templateURL=https://sharefile-jiade.s3.cn-northwest-1.amazonaws.com.cn/clawdbot-bedrock.yaml) |
| **US East (N. Virginia)** | [![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review?stackName=secure-moltbot&templateURL=https://sharefile-jiade.s3.cn-northwest-1.amazonaws.com.cn/clawdbot-bedrock.yaml) |

**Steps:**
1. Click "Launch Stack" → Select EC2 key pair → Create
2. Wait ~8 minutes
3. Check **Outputs** tab → Copy URL with token
4. Start chatting!

### CLI Deploy

```bash
aws cloudformation create-stack \
  --stack-name secure-moltbot \
  --template-body file://clawdbot-bedrock.yaml \
  --parameters ParameterKey=KeyPairName,ParameterValue=your-key \
  --capabilities CAPABILITY_IAM \
  --region us-west-2
```

---

## 🔒 Security Enhancements

### Before vs After

| Aspect | Original Template | This Project |
|--------|-------------------|--------------|
| IAM Policy | `Resource: '*'` | Specific model ARNs |
| Agent Permissions | None | Per-agent limits |
| Injection Protection | None | Pattern detection |
| Audit Logging | CloudTrail only | + Application logs |
| Rate Limiting | None | Per-agent throttling |
| Tool Control | None | Allow/deny lists |

### Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: AWS Infrastructure                                 │
│  IAM Roles • VPC Endpoints • SSM • CloudTrail               │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Application Security (OUR CONTRIBUTION)           │
│  PermissionSystem • ActionValidator • RateLimiter • Audit   │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Execution Security                                 │
│  Docker Sandbox • Tool Allow/Deny • Session Isolation       │
└─────────────────────────────────────────────────────────────┘
```

### Agent Permissions Example

```json
{
  "main": {
    "allowed_models": ["global.amazon.nova-2-lite-v1:0", "us.amazon.nova-pro-v1:0"],
    "max_tokens": 8192,
    "allowed_actions": ["chat", "code", "exec"],
    "rate_limit": { "requests_per_minute": 30, "tokens_per_hour": 500000 }
  },
  "public": {
    "allowed_models": ["global.amazon.nova-2-lite-v1:0"],
    "max_tokens": 2048,
    "allowed_actions": ["chat"],
    "rate_limit": { "requests_per_minute": 5, "tokens_per_hour": 10000 }
  }
}
```

---

## 🏗️ Architecture

```
┌──────────────┐     ┌─────────────────────────────────────────────────────┐
│   User       │     │  EC2 Instance                                       │
│   Input      │────▶│  ┌──────────────────────────────────────────────┐  │
└──────────────┘     │  │  BedrockSecurityMiddleware                    │  │
                     │  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ │  │
                     │  │  │ Validator  │→│ Permission │→│ RateLimiter│ │  │
                     │  │  └────────────┘ └────────────┘ └────────────┘ │  │
                     │  │         │               │              │       │  │
                     │  │         └───────────────┴──────────────┘       │  │
                     │  │                         ↓                      │  │
                     │  │                  ┌────────────┐               │  │
                     │  │                  │AuditLogger │               │  │
                     │  │                  └────────────┘               │  │
                     │  └──────────────────────────────────────────────┘  │
                     │                         ↓ (if allowed)             │
                     │              ┌─────────────────────┐              │
                     │              │  Bedrock API        │              │
                     │              │  (via IAM Role)     │              │
                     │              └─────────────────────┘              │
                     └─────────────────────────────────────────────────────┘
```

---

## 💰 Cost Breakdown

| Component | Monthly Cost |
|-----------|-------------|
| EC2 (t4g.medium Graviton) | $24 |
| EBS (30GB gp3) | $2.40 |
| VPC Endpoints (3) | $21.60 |
| Data Transfer | $5-10 |
| **Subtotal** | **$53-58** |

**Bedrock Usage** (100 conversations/day with Nova Lite): ~$5-8/month

**Total**: ~$60-66/month for typical usage

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [SECURITY.md](SECURITY.md) | Security best practices and configuration |
| [THREAT_MODEL.md](THREAT_MODEL.md) | Comprehensive threat analysis |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues and solutions |
| [QUICK_START_KIRO.md](QUICK_START_KIRO.md) | Conversational deployment with Kiro AI |

---

## 🔧 Configuration

### Supported Models

```yaml
ClawdbotModel:
  - global.amazon.nova-2-lite-v1:0        # Default, cheapest
  - us.amazon.nova-pro-v1:0               # Balanced
  - global.anthropic.claude-sonnet-4-5    # Most capable
  - us.deepseek.r1-v1:0                   # Open-source reasoning
```

### Instance Types

| Type | RAM | Cost/Month | Best For |
|------|-----|------------|----------|
| t4g.small | 2GB | $12 | Development |
| t4g.medium | 4GB | $24 | Production (default) |
| t4g.large | 8GB | $48 | Heavy usage |

---

## 🧪 Security Testing

Run the test suite:

```bash
# On EC2 instance
cd ~/.clawdbot
python3 -m pytest tests/test_security.py -v
```

Test scenarios covered:
- ✅ Prompt injection blocking
- ✅ Unauthorized model access
- ✅ Rate limit enforcement
- ✅ Token limit validation
- ✅ Audit log integrity

---

## 📊 Monitoring

### View Audit Logs

```bash
# Today's actions
cat ~/.clawdbot/audit/audit-$(date +%Y-%m-%d).jsonl | jq

# Denied actions only
cat ~/.clawdbot/audit/*.jsonl | jq 'select(.allowed == false)'
```

### CloudWatch Alarms

- **High Cost**: Alert when Bedrock spend exceeds threshold
- **Unauthorized Access**: Alert on permission denials
- **Rate Limit Violations**: Alert on abuse attempts

---

## 🚨 Incident Response

### Token Compromised

```bash
# Generate new token
NEW_TOKEN=$(openssl rand -hex 24)
sed -i "s/\"token\": \".*\"/\"token\": \"$NEW_TOKEN\"/" ~/.clawdbot/clawdbot.json
systemctl --user restart clawdbot-gateway
```

### Check Security Events

```bash
cat ~/.clawdbot/audit/*.jsonl | jq 'select(.type == "security_event")'
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add security tests for any new features
4. Submit a pull request

---

## 📚 References

- [MoltBot Official Docs](https://docs.molt.bot/)
- [moltbot-safe Security Principles](https://github.com/moltbot/moltbot-safe)
- [Amazon Bedrock Security](https://docs.aws.amazon.com/bedrock/latest/userguide/security.html)
- [January 2026 Incident Report](https://blogs.cisco.com/ai/personal-ai-agents-like-moltbot-are-a-security-nightmare)

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>Built with security-first principles by Kaushikq</strong><br/>
  <em>Protecting AI agents one request at a time 🔐</em>
</p>
