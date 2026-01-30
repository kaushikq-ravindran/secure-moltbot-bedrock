"""
Audit Logger for Bedrock Actions
Based on moltbot-safe audit.py principles

Provides application-level logging:
- All actions logged (allowed and denied)
- Append-only design
- JSON format for easy parsing
- Cost tracking for Bedrock calls
"""
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path


class AuditLogger:
    """
    Append-only audit logger for agent actions.
    Implements moltbot-safe's AuditLog pattern.
    """
    
    def __init__(self, log_dir: str = '/home/ubuntu/.clawdbot/audit'):
        self.log_dir = log_dir
        self._ensure_log_dir()
    
    def _ensure_log_dir(self):
        """Create log directory if it doesn't exist"""
        os.makedirs(self.log_dir, exist_ok=True)
    
    def _get_log_file(self) -> str:
        """Get current log file path (daily rotation)"""
        date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        return os.path.join(self.log_dir, f'audit-{date_str}.jsonl')
    
    def _write_entry(self, entry: Dict[str, Any]):
        """Write a log entry (append-only)"""
        log_file = self._get_log_file()
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def log(self, agent_id: str, action: Dict[str, Any], allowed: bool):
        """
        Log an action (moltbot-safe compatible interface).
        
        Args:
            agent_id: Agent that performed the action
            action: Action details
            allowed: Whether the action was allowed
        """
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'epoch': time.time(),
            'agent_id': agent_id,
            'action': action,
            'allowed': allowed
        }
        self._write_entry(entry)
    
    def log_action(self, agent_id: str, action: Dict[str, Any], 
                   allowed: bool, reason: str):
        """
        Log an action with reason.
        
        Args:
            agent_id: Agent that performed the action
            action: Action details  
            allowed: Whether the action was allowed
            reason: Reason for allow/deny decision
        """
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'epoch': time.time(),
            'type': 'action',
            'agent_id': agent_id,
            'action': action,
            'allowed': allowed,
            'reason': reason
        }
        self._write_entry(entry)
    
    def log_bedrock_call(self, agent_id: str, model_id: str,
                         input_tokens: int, output_tokens: int,
                         cost_estimate: float, latency_ms: Optional[float] = None):
        """
        Log a Bedrock API call with usage metrics.
        
        Args:
            agent_id: Agent that made the call
            model_id: Bedrock model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost_estimate: Estimated cost in USD
            latency_ms: Response latency in milliseconds
        """
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'epoch': time.time(),
            'type': 'bedrock_call',
            'agent_id': agent_id,
            'model_id': model_id,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
            'cost_estimate_usd': cost_estimate,
            'latency_ms': latency_ms
        }
        self._write_entry(entry)
    
    def log_security_event(self, event_type: str, agent_id: str,
                           details: Dict[str, Any], severity: str = 'warning'):
        """
        Log a security-relevant event.
        
        Args:
            event_type: Type of security event
            agent_id: Agent involved
            details: Event details
            severity: Event severity (info, warning, error, critical)
        """
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'epoch': time.time(),
            'type': 'security_event',
            'event_type': event_type,
            'agent_id': agent_id,
            'severity': severity,
            'details': details
        }
        self._write_entry(entry)
    
    def log_rate_limit(self, agent_id: str, limit_type: str, 
                       current: int, limit: int):
        """
        Log a rate limit event.
        
        Args:
            agent_id: Agent that hit the limit
            limit_type: Type of limit (requests, tokens)
            current: Current count
            limit: Maximum allowed
        """
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'epoch': time.time(),
            'type': 'rate_limit',
            'agent_id': agent_id,
            'limit_type': limit_type,
            'current': current,
            'limit': limit
        }
        self._write_entry(entry)
    
    def get_recent_entries(self, count: int = 100) -> list:
        """
        Get recent log entries.
        
        Args:
            count: Number of entries to retrieve
            
        Returns:
            List of log entries (newest first)
        """
        log_file = self._get_log_file()
        if not os.path.exists(log_file):
            return []
        
        entries = []
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    entries.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
        
        return entries[-count:][::-1]
    
    def get_agent_usage(self, agent_id: str, hours: int = 24) -> Dict[str, Any]:
        """
        Get usage statistics for an agent.
        
        Args:
            agent_id: Agent to query
            hours: Time window in hours
            
        Returns:
            Usage statistics dictionary
        """
        cutoff = time.time() - (hours * 3600)
        
        stats = {
            'total_requests': 0,
            'allowed_requests': 0,
            'denied_requests': 0,
            'total_tokens': 0,
            'total_cost': 0.0
        }
        
        log_file = self._get_log_file()
        if not os.path.exists(log_file):
            return stats
        
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if entry.get('agent_id') != agent_id:
                        continue
                    if entry.get('epoch', 0) < cutoff:
                        continue
                    
                    if entry.get('type') == 'action':
                        stats['total_requests'] += 1
                        if entry.get('allowed'):
                            stats['allowed_requests'] += 1
                        else:
                            stats['denied_requests'] += 1
                    
                    elif entry.get('type') == 'bedrock_call':
                        stats['total_tokens'] += entry.get('total_tokens', 0)
                        stats['total_cost'] += entry.get('cost_estimate_usd', 0)
                        
                except json.JSONDecodeError:
                    continue
        
        return stats
    
    def get_denied_actions(self, hours: int = 24) -> list:
        """Get all denied actions in time window"""
        cutoff = time.time() - (hours * 3600)
        denied = []
        
        log_file = self._get_log_file()
        if not os.path.exists(log_file):
            return denied
        
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if entry.get('epoch', 0) < cutoff:
                        continue
                    if entry.get('type') == 'action' and not entry.get('allowed'):
                        denied.append(entry)
                except json.JSONDecodeError:
                    continue
        
        return denied
