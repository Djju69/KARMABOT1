""
Utility functions for integration tests.
"""
from datetime import datetime
from telegram import Update, Message, Chat, User, CallbackQuery

def create_text_update(text, user_id=1, chat_id=1):
    """Create a test Update object with text message."""
    return Update(
        update_id=1,
        message=Message(
            message_id=1,
            date=datetime.now(),
            chat=Chat(id=chat_id, type='private'),
            from_user=User(
                id=user_id, 
                first_name='Test',
                is_bot=False,
                username=f'testuser{user_id}'
            ),
            text=text
        )
    )

def create_callback_update(callback_data, user_id=1, chat_id=1, message_id=1):
    """Create a test Update object with callback query."""
    return Update(
        update_id=1,
        callback_query=CallbackQuery(
            id='test_callback',
            from_user=User(
                id=user_id,
                first_name='Test',
                is_bot=False,
                username=f'testuser{user_id}'
            ),
            chat_instance='test_chat',
            message=Message(
                message_id=message_id,
                date=datetime.now(),
                chat=Chat(id=chat_id, type='private'),
                text='Test message'
            ),
            data=callback_data
        )
    )

async def process_update(application, update):
    """Process an update with the application and return the response."""
    # Store the last response for assertions
    response = None
    
    async def response_callback(update, text, **kwargs):
        nonlocal response
        response = text
        
    # Mock the reply_text method to capture responses
    original_reply = update.message.reply_text if hasattr(update, 'message') else None
    if original_reply:
        update.message.reply_text = response_callback
        
    # Process the update
    await application.process_update(update)
    
    # Restore original method
    if original_reply:
        update.message.reply_text = original_reply
        
    return response
