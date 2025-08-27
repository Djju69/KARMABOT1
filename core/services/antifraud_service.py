"""
Anti-fraud service for rate limiting and abuse prevention.
"""
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

from core.services.cache import cache_service

logger = logging.getLogger(__name__)

class AntiFraudService:
    """Service for anti-fraud checks and rate limiting."""
    
    # Rate limits (per user/IP)
    RATE_LIMITS = {
        'redeem_qr': {
            'limit': 5,  # max attempts
            'window': 60,  # seconds
            'key_prefix': 'antifraud:qr:'
        },
        'redeem_card': {
            'limit': 10,  # max attempts
            'window': 300,  # 5 minutes
            'key_prefix': 'antifraud:card:'
        },
        'generate_qr': {
            'limit': 5,  # max QR codes per minute
            'window': 60,  # 1 minute
            'key_prefix': 'antifraud:genqr:'
        }
    }
    
    # Global limits (across all users)
    GLOBAL_LIMITS = {
        'total_redeems': {
            'limit': 1000,  # max redeems per hour
            'window': 3600,  # 1 hour
            'key': 'antifraud:global:redeems'
        }
    }
    
    async def check_rate_limit(self, action: str, identifier: str) -> Tuple[bool, Optional[int]]:
        """
        Check if the action is rate limited for the given identifier.
        
        Args:
            action: One of 'redeem_qr', 'redeem_card', 'generate_qr'
            identifier: User ID or IP address
            
        Returns:
            Tuple of (is_allowed, remaining_attempts)
        """
        if action not in self.RATE_LIMITS:
            logger.warning(f"Unknown rate limit action: {action}")
            return True, None
            
        config = self.RATE_LIMITS[action]
        cache_key = f"{config['key_prefix']}{identifier}"
        
        # Get current counter and last update time
        cached = await cache_service.get(cache_key)
        if cached:
            try:
                count, timestamp = map(int, cached.split(':'))
            except (ValueError, AttributeError):
                count, timestamp = 0, 0
        else:
            count, timestamp = 0, 0
            
        # Check if window has passed
        current_time = int(time.time())
        if current_time - timestamp > config['window']:
            count = 0
            timestamp = current_time
            
        # Check limit
        if count >= config['limit']:
            retry_after = (timestamp + config['window']) - current_time
            return False, retry_after
            
        return True, config['limit'] - count - 1
    
    async def increment_counter(self, action: str, identifier: str) -> None:
        """Increment the counter for the given action and identifier."""
        if action not in self.RATE_LIMITS:
            return
            
        config = self.RATE_LIMITS[action]
        cache_key = f"{config['key_prefix']}{identifier}"
        
        # Get current counter and last update time
        cached = await cache_service.get(cache_key)
        if cached:
            try:
                count, timestamp = map(int, cached.split(':'))
            except (ValueError, AttributeError):
                count, timestamp = 0, 0
        else:
            count, timestamp = 0, 0
            
        # Reset counter if window has passed
        current_time = int(time.time())
        if current_time - timestamp > config['window']:
            count = 0
            timestamp = current_time
            
        # Increment counter
        count += 1
        
        # Store with TTL slightly longer than window to handle race conditions
        ttl = config['window'] + 10
        await cache_service.set(
            cache_key, 
            f"{count}:{timestamp}",
            expire_seconds=ttl
        )
    
    async def check_global_limit(self, limit_name: str) -> Tuple[bool, Optional[int]]:
        """Check global rate limits (across all users)."""
        if limit_name not in self.GLOBAL_LIMITS:
            return True, None
            
        config = self.GLOBAL_LIMITS[limit_name]
        current_time = int(time.time())
        
        # Use Redis sorted set for global rate limiting
        # Each member is a timestamp, we count members within the window
        cache_key = config['key']
        
        # Remove old timestamps (outside the window)
        min_score = current_time - config['window']
        await cache_service.zremrangebyscore(cache_key, '-inf', min_score)
        
        # Get current count
        count = await cache_service.zcard(cache_key)
        
        if count >= config['limit']:
            # Get oldest timestamp to calculate when next request will be allowed
            oldest = await cache_service.zrange(cache_key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(oldest[0][1] + config['window'] - current_time)
                return False, max(1, retry_after)
            return False, config['window']
            
        return True, config['limit'] - count - 1
    
    async def increment_global_counter(self, limit_name: str) -> None:
        """Increment the global counter for the given limit."""
        if limit_name not in self.GLOBAL_LIMITS:
            return
            
        config = self.GLOBAL_LIMITS[limit_name]
        current_time = time.time()
        
        # Add current timestamp to sorted set
        await cache_service.zadd(
            config['key'],
            {str(current_time): current_time}
        )
        
        # Set TTL on the key (slightly longer than window)
        await cache_service.expire(
            config['key'],
            config['window'] + 10
        )


# Global instance
antifraud_service = AntiFraudService()
