# Security Best Practices

> **This is a fork of the AWS Bedrock MoltBot template with security enhancements by Kaushikq.**

---

## 🔒 Security Enhancements (Our Contributions)

This repository adds **application-level security** on top of AWS infrastructure security:

| Enhancement | File | What It Does |
|-------------|------|--------------|
| **Per-Agent Permissions** | `security/permissions.py` | Model allowlists, token limits, action restrictions per agent |
| **Injection Detection** | `security/action_validator.py` | Blocks prompt injection attacks ("ignore instructions", etc.) |
| **Audit Logging** | `security/audit_logger.py` | Append-only logs for all actions with cost tracking |
| **Rate Limiting** | `security/rate_limiter.py` | Per-agent request/token throttling |
| **Security Middleware** | `security/bedrock_middleware.py` | Orchestrates all checks before Bedrock calls |
| **Restricted IAM** | `clawdbot-bedrock.yaml` | Changed `Resource: '*'` to specific model ARNs |
| **Agent Profiles** | `clawdbot-bedrock.yaml` | `main` (full access) and `public` (read-only) agents |
| **Tool Allow/Deny** | `clawdbot-bedrock.yaml` | Explicit tool permissions per agent |

### Before vs After

| Security Aspect | Original Template | Our Enhancements |
|-----------------|------------------|------------------|
| IAM Policy | `Resource: '*'` | Specific model ARNs only |
| Agent Permissions | None | Per-agent model/token limits |
| Injection Protection | None | Pattern-based detection |
| Application Audit | CloudTrail only | + Local JSON logs |
| Rate Limiting | None | Requests/min + tokens/hour |
| Tool Control | None | Allow/deny lists per agent |

---


## Quick Reference: Secure Access Commands

### Connect to EC2 Instance (Secure Method)

```bash
# Get instance ID
INSTANCE_ID=$(aws cloudformation describe-stacks \
  --stack-name moltbot-bedrock \
  --query 'Stacks[0].Outputs[?OutputKey==`InstanceId`].OutputValue' \
  --output text \
  --region us-west-2)

# Connect via SSM (no SSH keys needed)
aws ssm start-session --target $INSTANCE_ID --region us-west-2

# Switch to ubuntu user
sudo su - ubuntu
```

### Port Forwarding (Secure Access to Web UI)

```bash
# Start port forwarding (keep terminal open)
aws ssm start-session \
  --target $INSTANCE_ID \
  --region us-west-2 \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["18789"],"localPortNumber":["18789"]}'

# Access Web UI at: http://localhost:18789/?token=<your-token>
```

---

## Overview

This deployment combines **AWS security best practices** with **moltbot-safe security principles** for defense-in-depth protection.

## Security Layers

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: AWS Infrastructure Security                           │
│  IAM Roles • VPC Endpoints • SSM Session Manager • CloudTrail   │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Application Security (NEW)                            │
│  Permission System • Action Validator • Rate Limiter • Audit   │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Execution Security                                    │
│  Docker Sandbox • Tool Allow/Deny Lists • Session Isolation    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Security Features

### 1. IAM Role-Based Authentication

**No API Keys**: The EC2 instance uses an IAM role to authenticate with Bedrock.

```json
{
  "Sid": "BedrockInvokeAllowedModels",
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream"
  ],
  "Resource": [
    "arn:aws:bedrock:*::foundation-model/amazon.nova-*",
    "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
    "arn:aws:bedrock:*::foundation-model/meta.llama*"
  ]
}
```

**Enhanced**: IAM policy now restricts access to specific model families (no `Resource: '*'`).

**Benefits**:
- ✅ Automatic credential rotation
- ✅ No secrets in code or config files
- ✅ Centralized access control
- ✅ CloudTrail audit logs
- ✅ **Least privilege model access**

### 2. Per-Agent Permission System (NEW)

**Application-Level Access Control**: Each agent has explicit permissions.

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

**Security Modules** (`security/`):
| Module | Purpose |
|--------|---------|
| `permissions.py` | Model allowlists, token limits, action restrictions |
| `action_validator.py` | Schema validation, injection detection |
| `audit_logger.py` | Append-only logging, cost tracking |
| `rate_limiter.py` | Request/token throttling |
| `bedrock_middleware.py` | Orchestrates all security checks |

**Benefits**:
- ✅ Per-agent model access control
- ✅ Token limit enforcement
- ✅ Rate limiting per agent
- ✅ **Default deny** - explicit grants required

### 3. Prompt Injection Detection (NEW)

**Input Validation**: All requests validated before reaching Bedrock.

```python
INJECTION_PATTERNS = [
    r'(?i)ignore\s+(previous|above|all)\s+instructions?',
    r'(?i)you\s+are\s+now\s+',
    r'(?i)override\s+(system|instructions?)',
    r'(?i)jailbreak',
]
```

**Blocked automatically**:
- "Ignore previous instructions"
- "You are now in DAN mode"
- "Forget everything and..."

### 4. SSM Session Manager

**No SSH Keys Needed**: Access instances through AWS Systems Manager.

**Benefits**:
- ✅ No public SSH port (22) required
- ✅ Automatic session logging
- ✅ CloudTrail audit trail
- ✅ Session timeout controls

**Enable SSM-only access**:
```yaml
AllowedSSHCIDR: 127.0.0.1/32  # Disables SSH
```

### 5. VPC Endpoints

**Private Network**: Bedrock API calls stay within AWS network.

**Benefits**:
- ✅ Traffic doesn't traverse internet
- ✅ Lower latency
- ✅ Compliance-friendly (HIPAA, SOC2)

**Cost**: ~$22/month for 3 endpoints

### 6. Application-Level Audit Logging (NEW)

**Append-Only Logs**: All actions logged (allowed and denied).

```json
{
  "timestamp": "2026-01-30T10:15:30Z",
  "type": "action",
  "agent_id": "main",
  "action": {"type": "chat", "model_id": "nova-lite"},
  "allowed": true,
  "reason": "Allowed"
}
```

**Features**:
- Daily log rotation (`audit-YYYY-MM-DD.jsonl`)
- Cost tracking per request
- Denied action tracking
- Per-agent usage statistics

**View logs**:
```bash
# On EC2 instance
cat ~/.clawdbot/audit/audit-$(date +%Y-%m-%d).jsonl | jq
```

### 7. Rate Limiting (NEW)

**Per-Agent Throttling**: Prevents abuse and controls costs.

| Agent | Requests/min | Tokens/hour |
|-------|-------------|-------------|
| main | 30 | 500,000 |
| public | 5 | 10,000 |
| default | 10 | 100,000 |

### 8. Docker Sandbox

**Isolated Execution**: Non-main sessions run in Docker containers.

```json
{
  "agents": {
    "defaults": {
      "sandbox": { "mode": "non-main", "scope": "session" }
    }
  }
}
```

### 9. Tool Allow/Deny Lists (NEW)

**Explicit Tool Permissions**: Control which tools each agent can use.

```json
{
  "main": {
    "tools": {
      "allow": ["read", "write", "edit", "exec", "process"],
      "deny": ["gateway", "nodes"]
    }
  },
  "public": {
    "tools": {
      "allow": ["read"],
      "deny": ["exec", "write", "edit", "apply_patch", "browser", "gateway"]
    }
  }
}
```

---

## Security Checklist

### Deployment

- [x] IAM policy restricted to specific model families
- [x] Per-agent permission system configured
- [x] Prompt injection detection enabled
- [x] Audit logging enabled
- [x] Rate limiting configured
- [ ] VPC endpoints enabled (recommended for production)
- [ ] SSH disabled (`AllowedSSHCIDR: 127.0.0.1/32`)

### Post-Deployment

- [ ] Rotate gateway token regularly
- [ ] Review audit logs weekly
- [ ] Review denied actions
- [ ] Monitor Bedrock usage
- [ ] Set up cost alerts

### Ongoing

- [ ] Update Clawdbot monthly
- [ ] Review permissions.json quarterly
- [ ] Audit session logs
- [ ] Review security group rules

---

## Audit & Compliance

### Application Audit Logs (NEW)

```bash
# View today's audit log
cat ~/.clawdbot/audit/audit-$(date +%Y-%m-%d).jsonl | jq

# View denied actions only
cat ~/.clawdbot/audit/*.jsonl | jq 'select(.allowed == false)'

# Get agent usage stats
cat ~/.clawdbot/audit/*.jsonl | jq 'select(.agent_id == "main")' | wc -l
```

### CloudTrail Logs

```bash
# View recent Bedrock calls
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=InvokeModel \
  --max-items 50 \
  --region us-west-2
```

### Cost Tracking

```bash
# View Bedrock costs
aws ce get-cost-and-usage \
  --time-period Start=2026-01-01,End=2026-01-31 \
  --granularity DAILY \
  --metrics BlendedCost \
  --filter '{"Dimensions":{"Key":"SERVICE","Values":["Amazon Bedrock"]}}'
```

---

## Incident Response

### Compromised Instance

```bash
# 1. Isolate instance
aws ec2 modify-instance-attribute \
  --instance-id $INSTANCE_ID \
  --groups sg-isolated

# 2. Create forensic snapshot
aws ec2 create-snapshot \
  --volume-id $VOLUME_ID \
  --description "Forensic snapshot"

# 3. Terminate instance
aws ec2 terminate-instances --instance-ids $INSTANCE_ID

# 4. Review CloudTrail and application audit logs
```

### Suspected Prompt Injection

```bash
# Check audit logs for injection attempts
cat ~/.clawdbot/audit/*.jsonl | jq 'select(.type == "security_event")'
```

### Leaked Gateway Token

```bash
# Regenerate token
sudo su - ubuntu
NEW_TOKEN=$(openssl rand -hex 24)
sed -i "s/\"token\": \".*\"/\"token\": \"$NEW_TOKEN\"/" ~/.clawdbot/clawdbot.json
XDG_RUNTIME_DIR=/run/user/1000 systemctl --user restart clawdbot-gateway
```

---

## Security Recommendations

### For Development

- Use `t4g.small` instance (Graviton, cost-effective)
- Use Nova 2 Lite model (cheapest)
- Disable VPC endpoints (save $22/month)
- Enable sandbox mode
- **Review audit logs for unexpected patterns**

### For Production

- Use `t4g.medium` or larger
- **Enable VPC endpoints** (required for security)
- **Disable SSH** (`AllowedSSHCIDR: 127.0.0.1/32`)
- **Restrict permissions.json to needed models only**
- **Set aggressive rate limits for public agents**
- Set up CloudWatch alarms
- Regular audit log review

### For Compliance (HIPAA, PCI-DSS)

- **Must enable VPC endpoints**
- **Must disable SSH**
- **Must enable application audit logging**
- Enable CloudTrail
- Enable VPC Flow Logs
- Encrypt EBS volumes (enabled by default)
- Regular penetration testing
- Document security controls

---

## Security Architecture

```
┌──────────────┐
│  User Input  │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  Security Middleware (bedrock_middleware.py)                  │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Validator  │─▶│ Permissions │─▶│Rate Limiter │          │
│  │action_valid │  │permissions  │  │rate_limiter │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│         │                │                │                  │
│         └────────────────┼────────────────┘                  │
│                          ▼                                   │
│                   ┌─────────────┐                           │
│                   │ Audit Logger│                           │
│                   │audit_logger │                           │
│                   └─────────────┘                           │
└──────────────────────────┬───────────────────────────────────┘
                           │ (if allowed)
                           ▼
                   ┌─────────────────┐
                   │  Bedrock API    │
                   │  (via IAM Role) │
                   └─────────────────┘
```

---

## Compliance Certifications

Amazon Bedrock supports:
- SOC 1, 2, 3
- ISO 27001, 27017, 27018, 27701
- PCI DSS
- HIPAA eligible
- FedRAMP Moderate (in supported regions)

---

## References

- [AWS Security Best Practices](https://aws.amazon.com/architecture/security-identity-compliance/)
- [Bedrock Security](https://docs.aws.amazon.com/bedrock/latest/userguide/security.html)
- [SSM Security](https://docs.aws.amazon.com/systems-manager/latest/userguide/security.html)
- [moltbot-safe Security Principles](../moltbot-safe-main/SECURITY.md)
