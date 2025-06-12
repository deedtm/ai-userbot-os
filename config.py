from configparser import ConfigParser

config = ConfigParser()
config.read("config.ini")

API_ID = config.get("telegram_api", "id")
API_HASH = config.get("telegram_api", "hash")

MSGS_LIMIT = config.getint('bot', 'messages_limit')
MSGS_LIMIT_INTERVAL = config.getint('bot', 'msgs_limit_interval')
EXCEEDING_LIMIT_REACTION = config.get('bot', 'exceeding_limit_reaction')

RETRY_SECONDS = int(config.get("bot", "retry_seconds"))
HISTORY_LEN = config.getint("bot", "history")

MENTIONS = config.get("bot", "mentions").split(", ")
USERNAME = config.get("bot", "username")
USER_ID = config.getint("bot", "user_id")

_MENTIONS_FILTER_RE = config.get("bot", "mentions_filter_re")
MENTIONS_FILTER_RE = _MENTIONS_FILTER_RE.format(
    username=USERNAME, mentions="|".join(MENTIONS)
)
