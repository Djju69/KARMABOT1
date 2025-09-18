"""
Utility helper functions for the KarmaSystemBot.
"""
from typing import Optional, Union, Dict, Any
from aiogram.types import Message, CallbackQuery


async def get_city_id_from_message(message: Union[Message, Dict[str, Any]]) -> Optional[int]:
    """
    Extract city ID from a message or callback query.
    
    Args:
        message: Either a Message object or a dictionary with message data
        
    Returns:
        Optional[int]: The city ID if found, None otherwise
    """
    try:
        # If it's a CallbackQuery, get the message
        if hasattr(message, 'message'):
            message = message.message
            
        # If it's a dictionary, try to get the city_id directly
        if isinstance(message, dict):
            return message.get('city_id')
            
        # If it's a Message object, try to get city_id from state or user data
        if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
            # In a real implementation, you would fetch this from your database
            # For now, we'll return a default value or None
            return 1  # Default city ID
            
    except Exception as e:
        # Log the error but don't crash
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting city ID: {e}")
        
    return None  # Return None if city ID couldn't be determined
