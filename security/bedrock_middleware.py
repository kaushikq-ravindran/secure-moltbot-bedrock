"""
Security Middleware for Bedrock Requests
Orchestrates all security checks before API calls

Flow:
1. Validate action schema
2. Check agent permissions
3. Check rate limits
4. Log action (allowed or denied)
5. If allowed, proceed and log response
"""
from typing import Tuple, Dict, Any, Optional
import time

from .permissions import BedrockPermissionSystem
from .action_validator import ActionValidator
from .audit_logger import AuditLogger
from .rate_limiter import RateLimiter


class BedrockSecurityMiddleware:
    """
    Central security middleware that orchestrates all checks.
    Integrates permission, validation, rate limiting, and audit systems.
    """
    
    # Model pricing (per 1M tokens)
    MODEL_PRICING = {
        'global.amazon.nova-2-lite-v1:0': {'input': 0.30, 'output': 2.50},
        'global.anthropic.claude-sonnet-4-5-20250929-v1:0': {'input': 3.00, 'output': 15.00},
        'global.anthropic.claude-haiku-4-5-20251001-v1:0': {'input': 1.00, 'output': 5.00},
        'us.amazon.nova-pro-v1:0': {'input': 0.80, 'output': 3.20},
        'us.deepseek.r1-v1:0': {'input': 0.55, 'output': 2.19},
        'us.meta.llama3-3-70b-instruct-v1:0': {'input': 0.99, 'output': 0.99},
    }
    
    def __init__(self, 
                 permissions_file: str = '/home/ubuntu/.clawdbot/permissions.json',
                 audit_dir: str = '/home/ubuntu/.clawdbot/audit'):
        """
        Initialize middleware with all security components.
        
        Args:
            permissions_file: Path to permissions JSON file
            audit_dir: Directory for audit logs
        """
        self.permissions = BedrockPermissionSystem(permissions_file)
        self.validator = ActionValidator()
        self.audit = AuditLogger(audit_dir)
        self.rate_limiter = RateLimiter()
    
    def process_request(self, agent_id: str, 
                        request: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Process and validate a Bedrock request.
        
        Args:
            agent_id: Agent making the request
            request: Bedrock request dictionary with:
                - model_id: Bedrock model ID
                - messages: Conversation messages
                - inferenceConfig: Optional inference settings
                - type: Action type (chat, code, etc.)
        
        Returns:
            Tuple of (allowed, reason, metadata)
        """
        start_time = time.time()
        
        # Step 1: Validate request schema
        valid, reason = self.validator.validate_bedrock_request(request)
        if not valid:
            self.audit.log_action(agent_id, request, False, f"Validation failed: {reason}")
            self.audit.log_security_event(
                'validation_failure', agent_id,
                {'reason': reason, 'request_type': request.get('type')},
                'warning'
            )
            return False, f"Validation failed: {reason}", {}
        
        # Step 2: Check permissions
        model_id = request.get('model_id', '')
        token_count = request.get('inferenceConfig', {}).get('maxTokens', 0)
        action_type = request.get('type', 'chat')
        
        allowed, reason = self.permissions.is_allowed(
            agent_id, action_type, model_id, token_count
        )
        if not allowed:
            self.audit.log_action(agent_id, request, False, f"Permission denied: {reason}")
            self.audit.log_security_event(
                'permission_denied', agent_id,
                {'model': model_id, 'action': action_type, 'reason': reason},
                'warning'
            )
            return False, f"Permission denied: {reason}", {}
        
        # Step 3: Check rate limits
        rate_config = self.permissions.get_rate_limit(agent_id)
        rate_ok, reason = self.rate_limiter.check_rate_limit(agent_id, rate_config)
        if not rate_ok:
            self.audit.log_action(agent_id, request, False, f"Rate limit: {reason}")
            self.audit.log_rate_limit(
                agent_id, 'request',
                self.rate_limiter.get_usage(agent_id)['requests_last_minute'],
                rate_config.get('requests_per_minute', 10)
            )
            return False, f"Rate limit exceeded: {reason}", {}
        
        # All checks passed
        self.rate_limiter.record_request(agent_id)
        self.audit.log_action(agent_id, request, True, "Allowed")
        
        processing_time = (time.time() - start_time) * 1000
        
        return True, "Allowed", {
            'validated': True,
            'agent_id': agent_id,
            'model_id': model_id,
            'processing_time_ms': processing_time
        }
    
    def log_response(self, agent_id: str, model_id: str,
                     input_tokens: int, output_tokens: int,
                     latency_ms: Optional[float] = None):
        """
        Log Bedrock API response with usage metrics.
        
        Args:
            agent_id: Agent that made the request
            model_id: Model used
            input_tokens: Input token count
            output_tokens: Output token count
            latency_ms: Response latency
        """
        # Calculate cost
        cost = self._estimate_cost(model_id, input_tokens, output_tokens)
        
        # Record token usage for rate limiting
        self.rate_limiter.record_tokens(agent_id, input_tokens + output_tokens)
        
        # Log the call
        self.audit.log_bedrock_call(
            agent_id, model_id,
            input_tokens, output_tokens,
            cost, latency_ms
        )
    
    def _estimate_cost(self, model_id: str, 
                       input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost based on model pricing.
        
        Args:
            model_id: Bedrock model ID
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        pricing = self.MODEL_PRICING.get(model_id, {'input': 1.0, 'output': 5.0})
        cost = (input_tokens / 1_000_000 * pricing['input'] + 
                output_tokens / 1_000_000 * pricing['output'])
        return round(cost, 6)
    
    def get_agent_stats(self, agent_id: str, hours: int = 24) -> Dict[str, Any]:
        """
        Get comprehensive stats for an agent.
        
        Returns:
            Dictionary with usage statistics
        """
        # Get audit log stats
        audit_stats = self.audit.get_agent_usage(agent_id, hours)
        
        # Get current rate limit status
        rate_usage = self.rate_limiter.get_usage(agent_id)
        rate_config = self.permissions.get_rate_limit(agent_id)
        
        return {
            'agent_id': agent_id,
            'period_hours': hours,
            'usage': audit_stats,
            'rate_limits': {
                'requests': {
                    'current': rate_usage['requests_last_minute'],
                    'limit': rate_config.get('requests_per_minute', 10)
                },
                'tokens': {
                    'current': rate_usage['tokens_last_hour'],
                    'limit': rate_config.get('tokens_per_hour', 100000)
                }
            },
            'permissions': self.permissions.get_agent_permissions(agent_id)
        }
    
    def get_security_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get security summary across all agents.
        
        Returns:
            Summary of security events
        """
        denied = self.audit.get_denied_actions(hours)
        
        return {
            'period_hours': hours,
            'total_denied_actions': len(denied),
            'denied_by_agent': self._group_by_agent(denied),
            'recent_denied': denied[:10]  # Most recent 10
        }
    
    def _group_by_agent(self, entries: list) -> Dict[str, int]:
        """Group log entries by agent"""
        counts = {}
        for entry in entries:
            agent = entry.get('agent_id', 'unknown')
            counts[agent] = counts.get(agent, 0) + 1
        return counts


# Singleton instance for easy access
_middleware_instance = None

def get_middleware() -> BedrockSecurityMiddleware:
    """Get or create singleton middleware instance"""
    global _middleware_instance
    if _middleware_instance is None:
        _middleware_instance = BedrockSecurityMiddleware()
    return _middleware_instance
