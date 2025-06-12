from configparser import ConfigParser

config = ConfigParser()
config.read("ai/config.ini")
SYSTEM_MSG = config.get("ai", "system_message")
PROMPT_ADD = config.get("ai", "prompt_msg_additional")

REACTION_SMSG = config.get("ai", "reaction_system_msg")
REACTION_PADD = config.get("ai", "prompt_reaction_additional")

GERRS_SMSG = config.get("ai", "grammatical_errors_system_msg")
GERRS_CHANCE = config.getint('ai', 'grammatical_errors_chance')

AI_MODEL = config.get("ai", "model")
AI_PREFIX = config.get('ai', 'prefix')[1:-1]
AI_SUFFIX = config.get('ai', 'suffix')[1:-1]

ARTIST_API_KEY = config.get("artist", "api_key")
ARTIST_SECRET_KEY = config.get("artist", "secret_key")
ARTIST_URL = config.get("artist", "url")

STYLES_VARIANTS = {
    "anime": ["anime", "аниме", "мультфильм", "мультик", "мультсериал"],
    "kandinsky": ["kandinsky", "кандинский", "свой"],
    "default": ["default", "обычный", "стандартный"],
    "uhd": ["uhd", "hd", "детальное", "фото", "фотография"],
}
