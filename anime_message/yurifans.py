# -*- coding=utf-8 -*-
import time

import requests, datetime, json, random
from bs4 import BeautifulSoup
import telegram, asyncio


def yulifans():
    url = 'https://yuri.website/'
    json_content = json.loads(open('../data/result.json', 'r', encoding='utf-8').read())
    last_update_time = datetime.datetime.strptime(json_content['yurifans']['last_update_time'], '%Y-%m-%d %H:%M:%S')

    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
    }

    req = requests.get(url, headers=headers)

    # req = open('test.html', 'r', encoding='utf-8').read()
    soup = BeautifulSoup(req.text, 'html.parser')

    info_list = soup.select('li[class="post-list-item item-post-style-3"] h2 a')
    update_time_list = soup.select('li[class="post-list-item item-post-style-3"] div[class="list-footer"] time')
    del req, soup

    message = []
    if len(info_list) == len(update_time_list):
        for i in range(0, len(update_time_list)):
            title = info_list[i].get_text()
            url = info_list[i].get('href')
            update_time = datetime.datetime.strptime(update_time_list[i].get('datetime'), '%Y-%m-%d %H:%M:%S')

            if update_time > last_update_time:
                msg = '''%s
%s''' % (title, url)
                message.append(msg)

        json_content['yurifans']['last_update_time'] = update_time_list[0].get('datetime')
        open('../data/result.json', 'w', encoding='utf-8').write(json.dumps(json_content))
    message.reverse()
    return message


async def sendmessage(token, chat_id, text):
    bot = telegram.Bot(token)
    async with bot:
        await bot.send_message(text=text, chat_id=chat_id)


if __name__ == '__main__':
    token = '5599701266:AAFbrRypK2lOL9of_yQzsJoTOY4cDURUSm8'
    chat_id = -1001592534864

    message_list = yulifans()
    if len(message_list) != 0:
        for message in message_list:
            asyncio.run(sendmessage(token, chat_id, message))
            time.sleep(random.randint(2, 5))
