import asyncio
from g4f.client import AsyncClient
from g4f import Model, Provider
from g4f.providers.retry_provider import IterListProvider
from logging import debug, info, warning
from pyrogram.types import Message
from . import *
from .constants import ais_models, ais_names
from utils import get_full_name
from ai.fusionbrain import AIArtist
from typing import AsyncGenerator
from config import HISTORY_LEN


class AI:
    def __init__(self):
        self.system_msg = SYSTEM_MSG
        self.ai = AI_MODEL
        self.models = ais_models[AI_MODEL]
        self.client = AsyncClient()
        self.artist = AIArtist(ARTIST_URL, ARTIST_API_KEY, ARTIST_SECRET_KEY)

    def change_model(self, ai: str):
        assert ai in ais_models, f"{ai} is not available. Available: {ais_names}"
        self.models = ais_models[ai]
        prev_version = self.ai
        self.ai = ai
        return prev_version

    def edit_system_msg(self, new_message: str):
        self.system_msg = new_message

    async def answer(self, messages: list[Message], msg_id: int, user_id: int) -> str:
        history = await self.get_history(messages, user_id, msg_id, PROMPT_ADD)
        return await self.__get_answer(history)

    async def generate_image(
        self, style: str | None, prompt: str, negative_prompt: str | None = None
    ):
        img, is_censored = await self.artist.generate(prompt, style, negative_prompt)
        img.name = f"{style}; +{prompt}; -{negative_prompt}.png"
        return img, is_censored

    async def get_reaction(self, message: str, emojis: list[str]) -> str | None:
        prompt = f"Отправь мне эмодзи, среди прикрепленных ниже, который больше всего подходит к следующему сообщению, как реакция: `{message}`\n\nЭМОДЗИ:\n```python\n{emojis}\n```"
        history = [
            {"role": "system", "content": REACTION_SMSG},
            {"role": "user", "content": prompt},
        ]
        res = await self.__get_answer(history)
        debug(msg=f"Сообщение для выбора реакции:\n{res}")
        if res is not None:
            for emoji in emojis:
                if emoji in res:
                    info(msg=f"Реакция: {emoji}")
                    return emoji
        info(msg="Реакция не найдена")
        return

    async def add_grammatical_errors(self, text: str):
        prompt = f'Добавь ошибки в следующий текст: "{text}"'
        history = [
            {"role": "system", "content": GERRS_SMSG},
            {"role": "user", "content": prompt},
        ]
        res = await self.__get_answer(history)
        return res

    async def get_history(
        self,
        messages_gen: AsyncGenerator[Message, None],
        user_id: int,
        reply_to_msg_id: int | None = None,
        prompt_additional: str | None = None,
        return_prompt: bool = False,
    ):
        assert return_prompt or (
            reply_to_msg_id is not None and prompt_additional is not None
        ), "`reply_to_msg_id` and `prompt_additional` required without return_prompt=True"
        msgs = [m async for m in messages_gen]
        msgs.reverse()
        msg_ids_inds = {}
        prompt = []
        for ind, m in enumerate(msgs):
            text = m.text
            sender = m.from_user
            is_me = sender and sender.id == user_id
            if text:
                if is_me:
                    text = text.removeprefix(AI_PREFIX).removesuffix(AI_SUFFIX)
                text = f": {text}"
            else:
                text = f" sent an "
                text += (
                    f"interesting {m.media.name} that didn't load"
                    if m.media
                    else "unsupported message"
                )
                if m.caption:
                    text += f" with caption: {m.caption}"
            text.strip()

            name = (
                "You" if is_me else get_full_name(sender) if not is_me else m.chat.title
            )
            if m.reply_to_message_id is not None and ind > 0:
                reply_ind = msg_ids_inds.get(m.reply_to_message_id)
                if reply_ind is not None:
                    name += f" reply to {reply_ind}"
            msg_ids_inds.setdefault(m.id, ind)
            msg = f"**{ind}. {name}**{text}"
            prompt.append(msg)

        reply_to_msg_ind = msg_ids_inds.get(reply_to_msg_id)
        if reply_to_msg_ind is None:
            reply_to_msg_ind = HISTORY_LEN - 1

        if prompt_additional is not None:
            prompt.extend(["", prompt_additional.format(reply_to_msg_ind)])

        if return_prompt:
            return prompt

        history = [
            {"role": "system", "content": self.system_msg},
            {"role": "user", "content": "\n".join(prompt)},
        ]
        return history

    async def __get_answer(self, history: list[dict]):
        tasks = [self.__send_to_ai_model(m, history) for m in self.models]
        results = await asyncio.gather(*tasks)
        # print(*list(zip(self.models, results)), sep="\n|----\n")
        answers = [r for r in results if r is not None or r != ""]
        if not answers:
            warning(f"{self.ai} don't answering")
        else:
            return answers[0]

    async def __send_to_ai_model(self, model: Model, history: list[dict]):
        best_providers: IterListProvider = model.best_provider
        if not isinstance(best_providers, IterListProvider):
            return await self.__send_to_ai(model, best_providers, history)
        for p in best_providers.providers:
            if not p.working:
                continue
            return await self.__send_to_ai(model, p, history)

    async def __send_to_ai(self, model: Model, provider: Provider, history: list[dict]):
        debug(f"Trying {model.name}:{provider.__name__}...")
        try:
            response = await self.client.chat.completions.create(
                history, model, provider
            )
            if response is not None:
                return response.choices[0].message.content
        except Exception as e:
            error_msg = " \\ ".join(e.__str__().split("\n"))
            debug(f"{model.name}:{provider}:{e.__class__.__name__}: {error_msg}")

    # def __get_answer(self, history: list[dict]):
    #     for m in self.models:
    #         debug(f"Trying {m.name}...")
    #         try:
    #             response = self.client.chat.completions.create(history, m)
    #             return response.choices[0].message.content
    #         except Exception as e:
    #             error_msg = " \\ ".join(e.__str__().split("\n"))
    #             debug(f"{e.__class__.__name__}: {error_msg}")
    #     warning(f"{self.ai} don't answering")
