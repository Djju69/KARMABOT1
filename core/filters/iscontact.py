from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import Message

class IsTrueContact(BaseFilter):
    """
    Passes only if the message contains a contact that belongs to the sender
    (i.e. the user shared their own phone number). Compatible with aiogram v3.
    """

    async def __call__(self, message: Message) -> bool:
        contact = getattr(message, "contact", None)
        if not contact:
            return False
        # If Telegram supplies user_id in contact, check it equals sender id
        if contact.user_id and message.from_user:
            return int(contact.user_id) == int(message.from_user.id)
        # Fallback: if there's no user_id, allow only if phone_number exists
        return bool(getattr(contact, "phone_number", None))

__all__ = ["IsTrueContact"]
