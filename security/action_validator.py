"""
Action Validator for Bedrock Requests

Validates all actions before execution:
- Schema validation
- Injection detection
- Input sanitization
"""
import re
from typing import Tuple, Dict, Any, List


class ActionValidator:
    """
    Validates Bedrock requests against security rules.
    Implements moltbot-safe's validate_action() pattern.
    """
    
    # Suspicious patterns that might indicate injection attempts
    INJECTION_PATTERNS = [
        r'(?i)ignore\s+(previous|above|all)\s+instructions?',
        r'(?i)disregard\s+(previous|above|all)',
        r'(?i)forget\s+(everything|all|previous)',
        r'(?i)you\s+are\s+now\s+',
        r'(?i)new\s+instructions?:',
        r'(?i)override\s+(system|instructions?)',
        r'(?i)jailbreak',
        r'(?i)DAN\s+mode',
        r'(?i)developer\s+mode',
    ]
    
    # Characters that might indicate code injection
    DANGEROUS_CHARS = ['`', '$(', '${', '&&', '||', ';', '|', '>', '<', '\x00']
    
    # Maximum lengths for various fields
    MAX_PROMPT_LENGTH = 100000
    MAX_SYSTEM_PROMPT_LENGTH = 10000
    MAX_MODEL_ID_LENGTH = 100
    
    def __init__(self):
        self.compiled_patterns = [
            re.compile(pattern) for pattern in self.INJECTION_PATTERNS
        ]
    
    def validate_action(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Basic action validation (moltbot-safe compatible).
        
        Args:
            action: Action dictionary to validate
            
        Returns:
            Tuple of (valid: bool, reason: str)
        """
        # Check 1: Must be a dictionary
        if not isinstance(action, dict):
            return False, "Action must be a dictionary"
        
        # Check 2: Must have 'type' field
        if 'type' not in action:
            return False, "Action must have 'type' field"
        
        # Check 3: Type must be string
        if not isinstance(action['type'], str):
            return False, "Action 'type' must be a string"
        
        return True, "Valid"
    
    def validate_bedrock_request(self, request: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate a Bedrock API request.
        
        Args:
            request: Bedrock request dictionary
            
        Returns:
            Tuple of (valid: bool, reason: str)
        """
        # Validate model_id
        model_id = request.get('model_id', '')
        if not model_id:
            return False, "model_id is required"
        if len(model_id) > self.MAX_MODEL_ID_LENGTH:
            return False, f"model_id exceeds max length ({self.MAX_MODEL_ID_LENGTH})"
        
        # Validate messages
        messages = request.get('messages', [])
        if not isinstance(messages, list):
            return False, "messages must be a list"
        
        for i, message in enumerate(messages):
            valid, reason = self._validate_message(message, i)
            if not valid:
                return False, reason
        
        # Validate system prompt if present
        system = request.get('system', '')
        if system:
            if len(system) > self.MAX_SYSTEM_PROMPT_LENGTH:
                return False, f"system prompt exceeds max length ({self.MAX_SYSTEM_PROMPT_LENGTH})"
            
            # Check for injection in system prompt
            injection, pattern = self._check_injection(system)
            if injection:
                return False, f"Potential injection detected in system prompt: {pattern}"
        
        # Validate inference config
        config = request.get('inferenceConfig', {})
        if config:
            max_tokens = config.get('maxTokens', 0)
            if not isinstance(max_tokens, int) or max_tokens < 0:
                return False, "maxTokens must be a positive integer"
            if max_tokens > 100000:
                return False, "maxTokens exceeds maximum allowed (100000)"
        
        return True, "Valid"
    
    def _validate_message(self, message: Dict[str, Any], index: int) -> Tuple[bool, str]:
        """Validate a single message in the conversation"""
        if not isinstance(message, dict):
            return False, f"Message {index} must be a dictionary"
        
        # Check role
        role = message.get('role')
        if role not in ['user', 'assistant']:
            return False, f"Message {index} has invalid role: {role}"
        
        # Check content
        content = message.get('content', [])
        if not isinstance(content, list):
            return False, f"Message {index} content must be a list"
        
        for j, item in enumerate(content):
            if not isinstance(item, dict):
                return False, f"Message {index} content item {j} must be a dictionary"
            
            # Validate text content
            if 'text' in item:
                text = item['text']
                if not isinstance(text, str):
                    return False, f"Message {index} text must be a string"
                
                if len(text) > self.MAX_PROMPT_LENGTH:
                    return False, f"Message {index} text exceeds max length"
                
                # Check for injection
                injection, pattern = self._check_injection(text)
                if injection:
                    return False, f"Potential injection in message {index}: {pattern}"
        
        return True, "Valid"
    
    def _check_injection(self, text: str) -> Tuple[bool, str]:
        """Check text for injection patterns"""
        for pattern in self.compiled_patterns:
            match = pattern.search(text)
            if match:
                return True, match.group(0)
        return False, ""
    
    def sanitize_input(self, text: str) -> str:
        """
        Sanitize user input by removing dangerous characters.
        
        Args:
            text: Input text to sanitize
            
        Returns:
            Sanitized text
        """
        result = text
        for char in self.DANGEROUS_CHARS:
            result = result.replace(char, '')
        return result
    
    def validate_tool_call(self, tool_name: str, tool_args: Dict[str, Any],
                          allowed_tools: List[str], denied_tools: List[str]) -> Tuple[bool, str]:
        """
        Validate a tool call against allow/deny lists.
        
        Args:
            tool_name: Name of the tool to call
            tool_args: Arguments for the tool
            allowed_tools: List of explicitly allowed tools
            denied_tools: List of explicitly denied tools
            
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        # Deny list takes precedence
        if tool_name in denied_tools:
            return False, f"Tool '{tool_name}' is explicitly denied"
        
        # If allow list is specified, tool must be in it
        if allowed_tools and tool_name not in allowed_tools:
            return False, f"Tool '{tool_name}' is not in allowed list"
        
        return True, "Allowed"


# Convenience function
def validate_action(action: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate an action using default validator"""
    validator = ActionValidator()
    return validator.validate_action(action)
