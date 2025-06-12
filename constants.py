import logging

LOGGING_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "fatal": logging.FATAL,
    "critical": logging.CRITICAL,
}

with open("all_emojis.txt") as f:
    ALL_EMOJIS = f.read().split()
with open("default_emojis.txt") as f:
    DEFAULT_EMOJIS = f.read().split()
def EMOJIS(is_premium: bool): return ALL_EMOJIS if is_premium else DEFAULT_EMOJIS

HYPERLINKF = "[{text}]({link})"
HYPERLINKF_USERNAME = HYPERLINKF.format(text="{text}", link="https://t.me/{}")
HYPERLINKF_USER_ID = HYPERLINKF.format(text="{text}", link="tg://user?id={}")
HYPERLINKF_CHAT_ID = HYPERLINKF_USERNAME.format("c/{}", text="{text}")

PARSING_ANSWER_TRIES = 5
last_message_time = 0