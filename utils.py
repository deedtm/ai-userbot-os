from pyrogram.types import User, Chat
from pyrogram.enums import ChatType
from ai import STYLES_VARIANTS, AI_SUFFIX, AI_PREFIX
from constants import (
    HYPERLINKF_USERNAME,
    HYPERLINKF_USER_ID,
    HYPERLINKF_CHAT_ID,
    PARSING_ANSWER_TRIES,
)
from config import MENTIONS, USERNAME
import random
import re


def get_peer_type_new(peer_id: int) -> str:
    peer_id_str = str(peer_id)
    if not peer_id_str.startswith("-"):
        return "user"
    elif peer_id_str.startswith("-100"):
        return "channel"
    else:
        return "chat"


def chance(probability: int) -> bool:
    if not 0 <= probability <= 100:
        raise ValueError("Probability must be between 0 and 100")
    return random.uniform(0, 100) < probability


def get_full_name(user: User):
    full = user.first_name
    if user.last_name:
        full += " " + user.last_name
    return full


def get_username_hyperlink(text: str, username: str):
    return HYPERLINKF_USERNAME.format(username, text=text)


def get_hyperlink(chat: Chat):
    is_private = chat.type is ChatType.PRIVATE
    text = get_full_name(chat) if is_private else chat.title
    if chat.username:
        return get_username_hyperlink(text, chat.username)
    if is_private:
        hlf, chat_id = HYPERLINKF_USER_ID, chat.id
    else:
        hlf = HYPERLINKF_CHAT_ID
        chat_id = str(chat.id)
        chat_id = chat_id[4:] if chat_id.startswith("-100") else chat_id[1:]
        chat_id = int(chat_id)
    return hlf.format(chat_id, text=text)


def parse_chat(chat: Chat):
    base = {
        "type": chat.type.name,
        "id": chat.id,
        "username": chat.username,
        "hyperlink": get_hyperlink(chat),
    }
    data = base.copy()
    if chat.type is not ChatType.PRIVATE:
        additional = {"title": chat.title}
    else:
        additional = {
            "first_name": chat.first_name,
            "last_name": chat.last_name,
            "full_name": get_full_name(chat),
        }
    data.update(additional)
    return data


def remove_mentions(text: str):
    mentions = MENTIONS.copy()
    mentions.append(USERNAME)
    for m in mentions:
        text = re.sub(rf"^@?{m}:?", "", text).strip()
    return text.strip()


def remove_history_format(text: str):
    try_n = 0
    mentions = MENTIONS.copy()
    mentions.append(USERNAME)

    while '"' in text and try_n < PARSING_ANSWER_TRIES:
        text = text.strip('"').strip()
        try_n += 1
    match = re.match(
        rf"\d+\. ({'|'.join(mentions)}|you): .+", text, re.IGNORECASE | re.MULTILINE
    )
    if match:
        text = match.group().split(": ", 1)[1]

    return text


def remove_spfixes(text: str):
    pattern = re.compile(rf"{re.escape(AI_PREFIX)}.*?{re.escape(AI_SUFFIX)}")
    text = pattern.sub("", text).strip()
    return text


def remove_gerrs_format(text: str):
    match = re.match(r'"(.*?)" -> "(.*?)"', text)
    if match:
        text = match.group(2)
    return text


def parse_answer(text: str):
    return remove_spfixes(
        remove_history_format(remove_gerrs_format(remove_mentions(text)))
    ).strip()


def parse_code(message: str):
    code = ""
    code_start = message.find("```")  # код обычно начинается и заканчивается с ```
    counter = 1
    while code_start != -1:
        code_end = message.find("```", code_start + 1)
        code += f"Код {counter}:\n{message[code_start:code_end + 3]}\n"
        message = f"{message[:code_start]}. Код прикреплен к голосовому сообщению под номером {counter}. {message[code_end + 3:]}"
        counter += 1
        code_start = message.find("```")
    return message, code


def reformat_style(style: str):
    for k, v in STYLES_VARIANTS.items():
        if style in v:
            return k.upper()
    return "UHD"


def get_request_text(prompt: str, negative_prompt: str | None, style: str | None):
    text = [f"Промпт: {prompt}"]
    if negative_prompt:
        text.append(f"Негативный: {negative_prompt}")
    if style:
        text.append(f"Стиль: {style}")
    return "\n\n".join(text)


def get_logging_id():
    return f"{random.randint(0, 9999):04}"
