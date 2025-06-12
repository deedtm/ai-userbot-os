from configparser import ConfigParser
from ai.generate import AI
from pyrogram.types import User, Chat
from text_to_speech import set_chance, get_chance
from texted_image import TextedImage
from utils import parse_chat, get_hyperlink
from constants import HYPERLINKF_USER_ID, HYPERLINKF_USERNAME
import json
import os


class BotControl:
    def __init__(self, gpt_client: AI):
        config = ConfigParser()
        config.read("config.ini")
        self.status = config.get("bot", "status")
        self.history_length = config.get("bot", "history")
        self.HELP_OFFSET = int(config.get("bot", "help_offset"))
        self.ai_client = gpt_client

        with open("commands.json", "r", encoding="utf8") as f:
            self.commands: dict[str, str] = json.load(f)
        if 'unignored.json' not in os.listdir():
            f = open('unignored.json', 'w')
            f.write('[[]]')
            f.close()
        with open("unignored.json", "r", encoding="utf8") as f:
            self.unignored: list[dict[str, str | int]] = json.load(f)

        self.generated_img_text = self.commands["generated_img"].format

    def get_help(self, ai_model: str) -> str:
        commands = self.commands
        HELP_OFFSET = self.HELP_OFFSET
        return commands["help"].format(
            status=commands[self.status],
            memory=commands["memory"].format(value=self.history_length, prev_value="")[
                :HELP_OFFSET
            ],
            voice=commands["voice"].format(value=get_chance(), prev_value="")[
                :HELP_OFFSET
            ],
            model=commands["model"].format(value=ai_model, prev_value="")[:HELP_OFFSET],
            commands=self.__get_desc(),
        )

    def get_change_command(self, command: str):
        return {
            "memory": self.change_memory_length,
            "voice": self.change_tts_chance,
            "model": self.change_ai_model,
        }[command]

    def get_processing_image(self, user_request: str):
        texted_img = TextedImage()
        img = texted_img.get(user_request)
        img.name = "processing_image.png"
        return img

    def change_online(self, status: str) -> str:
        """changes online of bot

        Args:
            status: can be `on` or `off`
        """
        self.status = status
        return self.commands.get(self.status)

    def is_online(self) -> bool:
        return True if self.status == "on" else False

    def change_memory_length(self, new_length: str) -> str:
        new_length = int(new_length)
        prev_value = self.history_length
        self.history_length = new_length
        return self.commands.get("memory").format(
            prev_value=prev_value, value=new_length
        )

    def change_tts_chance(self, new_chance: str) -> str:
        prev_value = get_chance()
        set_chance(new_chance)
        return self.commands.get("voice").format(
            prev_value=prev_value, value=new_chance
        )

    def change_ai_model(self, new_model: str) -> str:
        prev_value = self.ai_client.change_model(new_model)
        return self.commands.get("model").format(value=new_model, prev_value=prev_value)

    def change_gpt_system_message(self, new_message: str) -> str:
        prev_msg = self.ai_client.system_msg
        self.ai_client.edit_system_msg(new_message)
        return self.commands["msg"].format(message=new_message, prev_message=prev_msg)

    def get_gpt_system_message(self) -> str:
        return self.commands["msg"].format(
            message=self.ai_client.system_msg, prev_message=""
        )[:-25]

    def get_unignored_msg(self) -> str:
        unignored = self.__get_unignored_str()
        return self.commands["unignore"]["list"].format(unignored=unignored)

    def is_chat_unignored(self, id: int) -> bool:
        return id in self.unignored[0]

    def add_unignored(self, chat: Chat) -> str:
        self.unignored.append(parse_chat(chat))
        self.unignored[0].append(chat.id)

        with open("unignored.json", "w", encoding="utf8") as f:
            json.dump(self.unignored, f, indent=4, ensure_ascii=False)

        return self.commands["unignore"]["new"].format(hyperlink=get_hyperlink(chat))

    def ignore(self, id: int) -> str:
        user_data = self.__get_unignored_chat_by_id(id)
        self.unignored[0].remove(id)
        self.unignored.remove(user_data)

        with open("unignored.json", "w", encoding="utf8") as f:
            json.dump(self.unignored, f, indent=4, ensure_ascii=False)

        return self.commands["ignore"].format(hyperlink=user_data["hyperlink"])

    def __get_unignored_str(self) -> str:
        chats = ["— " + u["hyperlink"] for u in self.unignored[1:]]
        return "\n".join(chats)

    def __get_unignored_chat_by_id(self, chat_id: int) -> dict | None:
        for data in self.unignored[1:]:
            if data["id"] == chat_id:
                return data

    def __get_desc(self) -> str:
        descriptions = self.commands.get("description")
        return "\n".join(
            [f"`.{command}` — {descriptions[command]}" for command in descriptions]
        )
