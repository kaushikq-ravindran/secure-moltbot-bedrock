"""
Rate Limiter for Bedrock API Access
Implements per-agent request and token throttling

Rate limiting strategies:
- Requests per minute
- Tokens per hour
- Sliding window algorithm
"""
import time
from typing import Tuple, Dict, Any
from collections import defaultdict


class RateLimiter:
    """
    Token bucket rate limiter for API access control.
    Tracks usage per-agent and enforces configured limits.
    """
    
    def __init__(self):
        # Track request timestamps per agent
        self.request_timestamps: Dict[str, list] = defaultdict(list)
        # Track token usage per agent (timestamp, token_count)
        self.token_usage: Dict[str, list] = defaultdict(list)
    
    def check_rate_limit(self, agent_id: str, 
                         rate_config: Dict[str, int]) -> Tuple[bool, str]:
        """
        Check if agent is within rate limits.
        
        Args:
            agent_id: Agent to check
            rate_config: Rate limit configuration dict with:
                - requests_per_minute: Max requests per minute
                - tokens_per_hour: Max tokens per hour
                
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        now = time.time()
        
        # Check requests per minute
        rpm_limit = rate_config.get('requests_per_minute', 10)
        minute_ago = now - 60
        
        # Clean old timestamps
        self.request_timestamps[agent_id] = [
            ts for ts in self.request_timestamps[agent_id] 
            if ts > minute_ago
        ]
        
        if len(self.request_timestamps[agent_id]) >= rpm_limit:
            return False, f"Rate limit exceeded: {rpm_limit} requests/minute"
        
        # Check tokens per hour
        tph_limit = rate_config.get('tokens_per_hour', 100000)
        hour_ago = now - 3600
        
        # Clean old token usage
        self.token_usage[agent_id] = [
            (ts, tokens) for ts, tokens in self.token_usage[agent_id]
            if ts > hour_ago
        ]
        
        current_tokens = sum(tokens for _, tokens in self.token_usage[agent_id])
        if current_tokens >= tph_limit:
            return False, f"Token limit exceeded: {tph_limit} tokens/hour"
        
        return True, "Within limits"
    
    def record_request(self, agent_id: str):
        """Record a request for rate limiting"""
        self.request_timestamps[agent_id].append(time.time())
    
    def record_tokens(self, agent_id: str, token_count: int):
        """Record token usage for rate limiting"""
        self.token_usage[agent_id].append((time.time(), token_count))
    
    def get_usage(self, agent_id: str) -> Dict[str, Any]:
        """
        Get current usage statistics for an agent.
        
        Returns:
            Dictionary with current usage metrics
        """
        now = time.time()
        minute_ago = now - 60
        hour_ago = now - 3600
        
        # Count recent requests
        recent_requests = len([
            ts for ts in self.request_timestamps.get(agent_id, [])
            if ts > minute_ago
        ])
        
        # Count recent tokens
        recent_tokens = sum(
            tokens for ts, tokens in self.token_usage.get(agent_id, [])
            if ts > hour_ago
        )
        
        return {
            'requests_last_minute': recent_requests,
            'tokens_last_hour': recent_tokens
        }
    
    def reset_agent(self, agent_id: str):
        """Reset rate limit counters for an agent"""
        self.request_timestamps[agent_id] = []
        self.token_usage[agent_id] = []
    
    def get_wait_time(self, agent_id: str, 
                      rate_config: Dict[str, int]) -> float:
        """
        Get time until next request is allowed.
        
        Returns:
            Seconds to wait (0 if no wait needed)
        """
        now = time.time()
        rpm_limit = rate_config.get('requests_per_minute', 10)
        minute_ago = now - 60
        
        timestamps = sorted([
            ts for ts in self.request_timestamps.get(agent_id, [])
            if ts > minute_ago
        ])
        
        if len(timestamps) < rpm_limit:
            return 0.0
        
        # Wait until oldest request falls out of window
        oldest = timestamps[0]
        wait_time = (oldest + 60) - now
        return max(0.0, wait_time)


class TokenBucket:
    """
    Token bucket algorithm for smoother rate limiting.
    Allows for burst capacity while enforcing average rate.
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: Maximum tokens in bucket
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket.
        
        Returns:
            True if tokens were available, False otherwise
        """
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        """Refill bucket based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
    
    def get_tokens(self) -> float:
        """Get current token count"""
        self._refill()
        return self.tokens
