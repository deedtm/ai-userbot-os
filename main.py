from asyncio import sleep
import sys
import logging
import json
import time
import utils
import custom_filters as cfilters
from botcontrol import BotControl
from ai.generate import AI
from text_to_speech.generate import TTS
from text_to_speech import get_chance
from aiohttp.client_exceptions import ClientResponseError
from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.types import Message
from pyrogram import utils as pyrogram_utils
from pyrogram.errors.exceptions import bad_request_400
from constants import LOGGING_LEVELS, last_message_time
from config import (
    API_HASH,
    API_ID,
    MSGS_LIMIT,
    MSGS_LIMIT_INTERVAL,
    EXCEEDING_LIMIT_REACTION,
    RETRY_SECONDS,
    HISTORY_LEN,
    USER_ID,
    MENTIONS_FILTER_RE,
)
from ai import AI_PREFIX, AI_SUFFIX, GERRS_CHANCE
from traceback import format_exc
from re import IGNORECASE, MULTILINE


with open("exceptions.json", "r", encoding="utf8") as f:
    exceptions: dict = json.load(f)

app = Client(
    "my_account",
    api_id=API_ID,
    api_hash=API_HASH,
    parse_mode=ParseMode.MARKDOWN,
    sleep_threshold=999999,
)
tts = TTS()
ai_client = AI()
bot_control = BotControl(ai_client)
pyrogram_utils.get_peer_type = utils.get_peer_type_new


@app.on_message(filters.regex("\\.help") & filters.me)
async def help_handler(client: Client, msg: Message):
    await msg.edit_text(bot_control.get_help(ai_client.ai))


@app.on_message(filters.regex("\\.o?(n|ff)") & filters.me)
async def status_handler(client: Client, msg: Message):
    status = msg.text[1:]  # removing dot
    await msg.edit_text(bot_control.change_online(status))


@app.on_message(filters.regex("\\.?(voice|memory|model)") & filters.me)
async def changes_handler(client: Client, msg: Message):
    try:
        command, arg = msg.text.split()
        command = command[1:]  # removing dot
        text = bot_control.get_change_command(command)(arg)
        await msg.edit_text(text)
    except ValueError as err:
        err_message = err.__str__()
        if "not enough values to unpack" in err_message:
            await msg.edit_text(exceptions["no_parameter"].format(command=command))


@app.on_message(filters.regex("\\.msg"))
async def system_message_handler(client: Client, msg: Message):
    try:
        _, arg = msg.text.split(maxsplit=1)
        text = bot_control.change_gpt_system_message(arg)
        await msg.edit_text(text)
    except ValueError as err:
        err_message = err.__str__()
        if "not enough values to unpack" in err_message:
            text = bot_control.get_gpt_system_message()
            await msg.edit_text(text)


@app.on_message(filters.regex("\\.?(un|)ignore") & filters.me)
async def ignore_handler(client: Client, msg: Message):
    full_command = msg.text.split()

    if msg.text.startswith(".unignore"):
        if len(full_command) <= 1:
            text = bot_control.get_unignored_msg()
            await msg.edit_text(text, disable_web_page_preview=True)
            return

        arg = int(full_command[1])
        try:
            chat = await client.get_chat(arg)
            text = bot_control.add_unignored(chat)
        except (
            bad_request_400.UsernameInvalid,
            bad_request_400.PeerIdInvalid,
            bad_request_400.UsernameNotOccupied,
            IndexError,
            ValueError,
        ):
            command = full_command[0]
            text = exceptions.get("invalid_parameter").format(
                parameter=arg, command=command, exc=format_exc()
            )

        await msg.edit_text(text, disable_web_page_preview=True)

    elif msg.text.startswith(".ignore"):
        if len(full_command) <= 1:
            text = exceptions["no_parameter"].format(command=full_command[0])
            await msg.edit_text(text)
            return
        arg = int(full_command[1])
        try:
            text = bot_control.ignore(id=arg)
        except KeyError:
            text = exceptions["invalid_parameter"].format(
                parameter=arg, command=full_command[0], exc=format_exc()
            )
        except Exception:
            text = "```\n" + format_exc() + "\n```"
        await msg.edit_text(text, disable_web_page_preview=True)


# @app.on_message(
#     (filters.group | filters.private)
#     & filters.regex(rf"(@{USERNAME} |)\.img .+(\n.+|\n|){0,2}")
#     # filters.group & filters.regex(r"^(.+\s|)@muuuwa(\s.+|)$")
# )
# async def generating_image(client: Client, msg: Message):
#     if msg.chat.type == ChatType.BOT or not bot_control.is_online():
#         return
#     if msg.chat.type != ChatType.PRIVATE and (
#         not msg.text.startswith("@" + client.me.username)
#         and msg.from_user.id != client.me.id
#     ):
#         return

#     if msg.from_user.id == client.me.id:
#         args = " ".join(msg.text.split(" ", 1)[1:]).split("\n")
#         await msg.delete()
#     elif msg.chat.type == ChatType.PRIVATE:
#         args = " ".join(msg.text.split(" ", 1)[1:]).split("\n")
#     else:
#         args = " ".join(msg.text.split(" ", 2)[2:]).split("\n")

#     prompt = args[0]
#     negative_prompt = args[1] if len(args) > 1 else None
#     style = utils.reformat_style(args[2]) if len(args) > 2 else "UHD"

#     request_text = utils.get_request_text(prompt, negative_prompt, style)
#     processing_img = bot_control.get_processing_image(request_text)
#     new_msg = await client.send_photo(
#         msg.chat.id, photo=processing_img, reply_to_message_id=msg.id
#     )

#     image_bytes, is_censored = await ai_client.generate_image(
#         style, prompt, negative_prompt
#     )
#     prompt = f'{"🔞  " if is_censored else "➕  "}' + prompt
#     await new_msg.edit_media(InputMediaPhoto(image_bytes))
#     await new_msg.edit_caption(
#         bot_control.generated_img_text(
#             style=style, prompt=prompt, negative_prompt=negative_prompt
#         )
#     )


@app.on_message(filters.group & filters.me & filters.regex(r"\.history"))
async def group_history(client: Client, msg: Message):
    msgs_gen = client.get_chat_history(msg.chat.id, HISTORY_LEN)
    history = await ai_client.get_history(msgs_gen, client.me.id, return_prompt=True)
    await msg.edit_text("\n".join(history), disable_web_page_preview=True)


@app.on_message(
    filters.group
    & (
        filters.regex(MENTIONS_FILTER_RE, IGNORECASE | MULTILINE)
        | cfilters.reply_to_user_id(USER_ID)
    )
    & ~cfilters.commands
)
async def group(client: Client, msg: Message):
    global last_message_time, message_count
    lid = utils.get_logging_id()

    if bot_control.is_online() and bot_control.is_chat_unignored(msg.chat.id):
        current_time = time.time()
        if current_time - last_message_time < MSGS_LIMIT_INTERVAL:
            message_count += 1
            if message_count > MSGS_LIMIT:
                logging.info(f'{lid}:Превышен лимит сообщений из-за "{msg.chat.title}"')
                await client.send_reaction(msg.chat.id, msg.id, EXCEEDING_LIMIT_REACTION)
                await sleep(RETRY_SECONDS * (message_count - MSGS_LIMIT))
        else:
            last_message_time = current_time
            message_count = 1
 
        logging.info(msg=f'{lid}:Сообщение из "{msg.chat.title}"')
        try:
            # reaction = await ai_client.get_reaction(msg.text, EMOJIS)
            # if reaction:
            #     await client.send_reaction(msg.chat.id, msg.id, reaction)

            is_speech = tts.is_speech(get_chance())
            action = ChatAction.TYPING if not is_speech else ChatAction.RECORD_AUDIO
            await msg.reply_chat_action(action)

            history = client.get_chat_history(msg.chat.id, HISTORY_LEN)
            ans = await ai_client.answer(history, msg.id, client.me.id)
            if ans is None or ans == "":
                return
            
            # ans = ans.lower()
            ans = utils.parse_answer(ans)
            if utils.chance(GERRS_CHANCE):
                ans = await ai_client.add_grammatical_errors(ans)
                if ans is None or ans == "":
                    return
                ans = utils.parse_answer(ans)

            code = None
            if is_speech:
                ans, code = utils.parse_code(ans)

            if ans is None or ans == "":
                return
            text = f"{AI_PREFIX}{ans.lower().strip()}{AI_SUFFIX}"

            if not is_speech and len(text) < 4096:
                await client.send_message(msg.chat.id, text, reply_to_message_id=msg.id)
                message_type = "сообщение"
            else:
                speech = tts.generate_speech(ans, msg.chat.id)
                if not code:
                    await client.send_voice(
                        msg.chat.id, speech, reply_to_message_id=msg.id
                    )
                else:
                    await client.send_voice(
                        msg.chat.id,
                        speech,
                        reply_to_message_id=msg.id,
                        caption=code[:4096],
                    )
                message_type = "голосовое сообщение"
            logging.info(msg=f"{lid}:Отправлено {message_type}")
        except ClientResponseError as e:
            if e.status == 429:
                logging.warning(
                    msg=f"Слишком частые запросы к нейросети. Повтор попытки через {RETRY_SECONDS} сек."
                )
                await sleep(RETRY_SECONDS)
                await group(client, msg)
        except Exception:
            logging.error(
                msg=f'{lid}:Произошла ошибка при отправке сообщения в "{msg.chat.title}"'
            )
            logging.error(msg=format_exc())
        except KeyboardInterrupt:
            logging.info("Stopping `group` func...")
            return


if __name__ == "__main__":
    log_lvl = logging.INFO
    if len(sys.argv) > 1:
        log_lvl = LOGGING_LEVELS.get(sys.argv[1])
    logging.basicConfig(level=log_lvl)
    logging.critical(f"Chosen logging level: {log_lvl}")

    logging.info("Disabling excessive logging...")
    for name, logger in logging.root.manager.loggerDict.items():
        if name.startswith(
            ("pyrogram.session", "pyrogram.connection", "nodriver")
        ) and isinstance(logger, logging.Logger):
            logging.info(f"Disabled {name}")
            logger.setLevel(logging.WARNING)
    logging.info("Logging was disabled")
    try:
        app.run()
    except KeyboardInterrupt:
        logging.info("Exited")
