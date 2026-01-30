# Quick Start with Kiro AI

> **Prerequisites**: You need an AWS account and Kiro AI installed. New to Kiro? Get it at https://kiro.dev/

## Conversational Deployment

Want to deploy Moltbot by just chatting? Kiro AI can guide you through the entire process—from deployment to mobile configuration—through natural conversation.

**No commands to remember. No console clicking. Just chat.**

**New to Kiro?** 
- Get Kiro: https://kiro.dev/
- Quick Start Guide: https://kiro.dev/docs/getting-started/

## How to Use

### Step 1: Clone Repository

```bash
git clone https://github.com/aws-samples/sample-Moltbot-on-AWS-with-Bedrock.git
cd sample-Moltbot-on-AWS-with-Bedrock
```

**Note**: This works for both Linux and Mac deployments. Kiro will ask which platform you want.

### Step 2: Open as Workspace in Kiro

**Important**: You must open this folder as a workspace for Kiro to load the deployment assistant.

#### Option A: Kiro IDE 

**Don't have Kiro yet?** Install from https://kiro.dev/

1. Open your Kiro-enabled IDE (VS Code, Cursor, etc.)
2. File → Open Folder
3. Select `sample-Moltbot-on-AWS-with-Bedrock` folder
4. Kiro will automatically load `.kiro/steering/deploy-moltbot-conversationally.md`

#### Option B: Kiro CLI

**Install Kiro CLI**: See https://kiro.dev/docs/cli/

```bash
cd sample-Moltbot-on-AWS-with-Bedrock
kiro chat
```

Kiro CLI will load the workspace context and steering files.

**Verify it's loaded**:
- You should see `.kiro/steering/` folder in the file tree
- Kiro will respond to "deploy moltbot" keywords

### Step 3: Start Chatting

In Kiro chat panel (IDE) or Kiro CLI, say any of these:

```
"Help me deploy Moltbot on AWS"
"Deploy Moltbot"
"Setup Moltbot on AWS"
"I want to install Moltbot"
```

### Step 4: Follow Kiro's Questions

Kiro will ask you 4 simple questions:

1. **AWS Region**: Where to deploy (default: us-west-2)
2. **AI Model**: Which model to use (default: Nova 2 Lite, cheapest)
3. **Instance Size**: How much compute (default: t4g.medium, $24/mo)
4. **VPC Endpoints**: Private networking or not (default: yes, more secure)

**Pro tip**: Just say "default" or "use defaults" to skip all questions and deploy with best practices.

### Step 5: Wait 8 Minutes

Kiro will:
- ✅ Validate your AWS credentials
- ✅ Create EC2 key pair if needed
- ✅ Deploy CloudFormation stack
- ✅ Monitor progress and explain what's happening
- ✅ Retrieve access URL with token

### Step 6: Connect Your Messaging Platform

After deployment, Kiro asks:

```
"Which messaging platform do you want to connect?
1. WhatsApp
2. Telegram
3. Discord
4. Slack
5. Microsoft Teams"
```

Pick one, and Kiro provides step-by-step mobile/desktop configuration guide.

---

## Example Conversation

```
You: "Help me deploy Moltbot"

Kiro: "Which AWS region? (1-4 or 'default')"

You: "default"

Kiro: "Which AI model? (1-3 or 'default')"

You: "default"

Kiro: "Instance size? (1-4 or 'default')"

You: "default"

Kiro: "VPC endpoints? (yes/no or 'default')"

You: "default"

Kiro: "Configuration:
      - Region: us-west-2
      - Model: Nova 2 Lite (90% cheaper than Claude)
      - Instance: t4g.medium ($24/mo)
      - VPC Endpoints: Yes
      
      Estimated cost: $39-44/month
      
      Proceed? (yes/no)"

You: "yes"

Kiro: "🚀 Deploying... (8 minutes)
      
      ⏱️ Creating VPC... ✓
      ⏱️ Creating security groups... ✓
      ⏱️ Launching EC2... ⏳
      ⏱️ Installing Moltbot... ⏳
      
      ✅ Complete!
      
      Access URL: http://localhost:18789/?token=abc123...
      
      Which platform to connect? (1-5)"

You: "1"

Kiro: "📱 WhatsApp setup (3 steps):
      
      1. In Web UI: Channels → Add → WhatsApp
      2. On phone: WhatsApp → Settings → Linked Devices → Scan QR
      3. Send test message
      
      Done? (yes/no)"

You: "yes"

Kiro: "🎉 All set! Your Moltbot is live on WhatsApp.
      
      Try sending: 'Hello' or 'What can you do?'
      
      Monthly cost: ~$39-44
      
      Need help with anything else?"
```

---

## What If I Don't Have Kiro?

No problem! You have two other options:

### Option 1: One-Click CloudFormation

Click "Launch Stack" button in the main README for your region. Fill in parameters manually.

### Option 2: Manual CLI Deployment

```bash
aws cloudformation create-stack \
  --stack-name moltbot-bedrock \
  --template-body file://clawdbot-bedrock.yaml \
  --parameters \
    ParameterKey=KeyPairName,ParameterValue=your-key \
    ParameterKey=ClawdbotModel,ParameterValue=global.amazon.nova-2-lite-v1:0 \
    ParameterKey=InstanceType,ParameterValue=t4g.medium \
  --capabilities CAPABILITY_IAM \
  --region us-west-2
```

But honestly, **Kiro makes it way more fun**. It's like having a DevOps expert guiding every step.

---

## Troubleshooting

### "Kiro doesn't respond to 'deploy moltbot'"

**Possible causes**:

1. **Not in the workspace**: Make sure you opened the `sample-Moltbot-on-AWS-with-Bedrock` folder as a workspace (File → Open Folder)

2. **Steering file not loaded**: Check if `.kiro/steering/deploy-moltbot-conversationally.md` exists in the file tree

3. **Try being more explicit**: 
   - "Kiro, I need help deploying Moltbot on AWS"
   - "Can you guide me through Moltbot deployment?"

4. **Manual activation**: If automatic detection doesn't work, you can manually reference the steering file:
   - In Kiro chat, type: `#deploy-moltbot-conversationally`
   - Then say: "Help me deploy"

### "I don't have AWS credentials configured"

Kiro will detect this and guide you:

```bash
aws configure
# Enter your Access Key ID
# Enter your Secret Access Key
# Enter region: us-west-2
# Enter output: json
```

Then say "ready" to Kiro.

### "Deployment failed"

Kiro will:
1. Check CloudFormation events
2. Explain the error in simple terms
3. Provide fix commands
4. Offer to retry

Just say "help" and Kiro will troubleshoot with you.

---

## Why This Approach is Better

| Traditional | With Kiro |
|-------------|-----------|
| Read 20-page guide | Chat for 2 minutes |
| Remember 10+ commands | Answer 4 questions |
| Debug errors alone | Kiro troubleshoots with you |
| Copy-paste from docs | Kiro provides exact commands |
| Hope it works | Kiro verifies each step |

**Time saved**: 90%
**Frustration reduced**: 100%
**Success rate**: Higher (Kiro catches mistakes)

---

## Get Started

1. Clone: `git clone https://github.com/aws-samples/sample-Moltbot-on-AWS-with-Bedrock.git`
2. Open in Kiro-enabled IDE
3. Say: "Kiro, help me deploy Moltbot"
4. Follow along
5. Enjoy your AI assistant!

**Questions?** Just ask Kiro. That's what it's here for. 🦞

---

## Learn More About Kiro

- **Kiro Website**: https://kiro.dev/
- **Kiro Documentation**: https://kiro.dev/docs/
- **Kiro Steering Files**: https://kiro.dev/docs/steering/
- **Get Kiro**: https://kiro.dev/download/
