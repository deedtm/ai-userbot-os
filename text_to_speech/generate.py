from gtts import gTTS
import io
from random import choice


class TTS:
    def __init__(self, lang: str = 'ru'):
        self.lang = lang

    def generate_speech(self, text: str, chat_id: int):
        bytes = b''
        for byte in gTTS(text, lang=self.lang).stream():
            bytes += byte
        bin_speech = BinarySpeech(str(chat_id))
        bin_speech.write(bytes)
        return bin_speech

    def is_speech(self, chance):
        chances = [True] * chance
        chances.extend([False] * (100 - chance))
        return choice(chances)


class BinarySpeech(io.BytesIO):
    def __init__(self, name: str):
        self.name = name
