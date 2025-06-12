from pyrogram.types import Message
from pyrogram import filters


def reply_to_user_id(user_id: int) -> filters.Filter:
    async def func(_, __, message: Message):
        return (
            isinstance(message, Message)
            and message.reply_to_message is not None
            and message.reply_to_message.from_user is not None
            and message.reply_to_message.from_user.id == user_id
            and message.from_user.id != user_id
        )

    return filters.create(func, "ReplyToUserId")


def commands_filter(_, __, message: Message) -> filters.Filter:
    if not isinstance(message, Message):
        return False
    text = message.text is not None and message.text.startswith(("/", "."))
    caption = message.caption is not None and message.caption.startswith(("/", "."))
    return text or caption


commands = filters.create(commands_filter, "IsCommand")
