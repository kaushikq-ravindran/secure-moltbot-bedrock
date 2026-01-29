"""
Permission System for Bedrock Access Control

Implements per-agent access control with:
- Model allowlisting
- Token limits
- Action type restrictions
- Rate limiting configuration
"""
import json
import os
from typing import Tuple, Dict, Any, List


class BedrockPermissionSystem:
    """
    Manages agent permissions for Bedrock API access.
    Follows moltbot-safe principles: explicit grants, default deny, no wildcards.
    """
    
    def __init__(self, config_file: str = '/home/ubuntu/.clawdbot/permissions.json'):
        self.config_file = config_file
        self.permissions = {}
        self._load()
    
    def _load(self):
        """Load permissions from JSON file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.permissions = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to load permissions: {e}")
                self._set_defaults()
        else:
            self._set_defaults()
    
    def _set_defaults(self):
        """Set restrictive default permissions"""
        self.permissions = {
            "default": {
                "allowed_models": ["global.amazon.nova-2-lite-v1:0"],
                "max_tokens": 4096,
                "allowed_actions": ["chat", "summarize", "analyze"],
                "rate_limit": {
                    "requests_per_minute": 10,
                    "tokens_per_hour": 100000
                },
                "sandbox": {
                    "mode": "all",
                    "scope": "session"
                }
            },
            "main": {
                "allowed_models": [
                    "global.amazon.nova-2-lite-v1:0",
                    "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
                    "us.amazon.nova-pro-v1:0"
                ],
                "max_tokens": 8192,
                "allowed_actions": ["chat", "summarize", "analyze", "code", "edit", "exec"],
                "rate_limit": {
                    "requests_per_minute": 30,
                    "tokens_per_hour": 500000
                },
                "sandbox": {
                    "mode": "off"
                }
            },
            "public": {
                "allowed_models": ["global.amazon.nova-2-lite-v1:0"],
                "max_tokens": 2048,
                "allowed_actions": ["chat"],
                "rate_limit": {
                    "requests_per_minute": 5,
                    "tokens_per_hour": 10000
                },
                "sandbox": {
                    "mode": "all",
                    "scope": "agent"
                }
            }
        }
    
    def get_agent_permissions(self, agent_id: str) -> Dict[str, Any]:
        """Get permissions for an agent, falling back to default"""
        return self.permissions.get(agent_id, self.permissions.get("default", {}))
    
    def is_allowed(self, agent_id: str, action_type: str, 
                   model_id: str, token_count: int) -> Tuple[bool, str]:
        """
        Check if agent is allowed to perform action.
        
        Args:
            agent_id: Unique agent identifier
            action_type: Type of action (chat, code, exec, etc.)
            model_id: Bedrock model ID
            token_count: Requested max tokens
            
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        agent_perms = self.get_agent_permissions(agent_id)
        
        if not agent_perms:
            return False, f"No permissions configured for agent: {agent_id}"
        
        # Check 1: Model allowlist
        allowed_models = agent_perms.get("allowed_models", [])
        if model_id not in allowed_models:
            return False, f"Model not allowed: {model_id}. Allowed: {allowed_models}"
        
        # Check 2: Action type
        allowed_actions = agent_perms.get("allowed_actions", [])
        if action_type and action_type not in allowed_actions:
            return False, f"Action not allowed: {action_type}. Allowed: {allowed_actions}"
        
        # Check 3: Token limit
        max_tokens = agent_perms.get("max_tokens", 0)
        if token_count > max_tokens:
            return False, f"Token limit exceeded: {token_count} > {max_tokens}"
        
        return True, "Allowed"
    
    def get_rate_limit(self, agent_id: str) -> Dict[str, int]:
        """Get rate limit configuration for agent"""
        agent_perms = self.get_agent_permissions(agent_id)
        return agent_perms.get("rate_limit", {
            "requests_per_minute": 10,
            "tokens_per_hour": 100000
        })
    
    def get_sandbox_config(self, agent_id: str) -> Dict[str, str]:
        """Get sandbox configuration for agent"""
        agent_perms = self.get_agent_permissions(agent_id)
        return agent_perms.get("sandbox", {
            "mode": "all",
            "scope": "session"
        })
    
    def list_agents(self) -> List[str]:
        """List all configured agents"""
        return list(self.permissions.keys())
    
    def add_agent(self, agent_id: str, permissions: Dict[str, Any]):
        """Add or update agent permissions"""
        self.permissions[agent_id] = permissions
        self._save()
    
    def remove_agent(self, agent_id: str):
        """Remove agent permissions"""
        if agent_id in self.permissions and agent_id != "default":
            del self.permissions[agent_id]
            self._save()
    
    def _save(self):
        """Save permissions to file"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.permissions, f, indent=2)


# Convenience functions
def check_permission(agent_id: str, action_type: str, 
                     model_id: str, token_count: int) -> Tuple[bool, str]:
    """Quick permission check using default config"""
    system = BedrockPermissionSystem()
    return system.is_allowed(agent_id, action_type, model_id, token_count)
