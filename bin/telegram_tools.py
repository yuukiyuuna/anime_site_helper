# -*- coding=utf-8 -*-
import json, threading, random, time
import telegram, asyncio
from loguru import logger


class telegram_tool(threading.Thread):
    def __init__(self):
        config_json = json.loads(open('./config.json', 'r', encoding='utf-8').read())['telegram']
        self.token = config_json['token']
        self.chat_id = config_json['chat_id']
        del config_json

    async def sendmessage(self, text, parse_mode=None):
        bot = telegram.Bot(self.token)
        async with bot:
            if parse_mode is None:
                await bot.send_message(text=text, chat_id=self.chat_id)
            else:
                await bot.send_message(text=text, chat_id=self.chat_id, parse_mode=parse_mode)



    def send(self, message, parse_mode=None):
        if type(message).__name__ == 'list':
            for msg in message:
                asyncio.run(self.sendmessage(text=msg, parse_mode=parse_mode))
                time.sleep(random.randint(2, 5))
        elif type(message).__name__ == 'str':
            asyncio.run(self.sendmessage(message, parse_mode))
        else:
            logger.warning('未定义格式')
            logger.warning(message)
