from configparser import ConfigParser

config = ConfigParser()
config.read('text_to_speech/config.ini')

def set_chance(new: str):
    config.set("tts", "chance", new)

def get_chance():
    return int(config.get('tts', 'chance'))
