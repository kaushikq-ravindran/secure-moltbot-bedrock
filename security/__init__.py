"""
Security Modules for Secure MoltBot Bedrock

This package implements security principles for AWS Bedrock:
- Permission System: Per-agent access control
- Action Validator: Schema validation and injection detection  
- Audit Logger: Append-only logging with cost tracking
- Rate Limiter: Request and token throttling
- Security Middleware: Orchestrates all security checks

Usage:
    from security import BedrockSecurityMiddleware, get_middleware
    
    # Get singleton middleware
    middleware = get_middleware()
    
    # Process a request
    allowed, reason, metadata = middleware.process_request(
        agent_id='main',
        request={
            'model_id': 'global.amazon.nova-2-lite-v1:0',
            'messages': [...],
            'type': 'chat'
        }
    )
    
    # Log response
    if allowed:
        middleware.log_response(
            agent_id='main',
            model_id='global.amazon.nova-2-lite-v1:0',
            input_tokens=100,
            output_tokens=500
        )
"""

from .permissions import BedrockPermissionSystem, check_permission
from .action_validator import ActionValidator, validate_action
from .audit_logger import AuditLogger
from .rate_limiter import RateLimiter, TokenBucket
from .bedrock_middleware import BedrockSecurityMiddleware, get_middleware

__all__ = [
    'BedrockPermissionSystem',
    'check_permission',
    'ActionValidator', 
    'validate_action',
    'AuditLogger',
    'RateLimiter',
    'TokenBucket',
    'BedrockSecurityMiddleware',
    'get_middleware',
]

__version__ = '1.0.0'
