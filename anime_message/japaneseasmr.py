# -*- coding=utf-8 -*-
import random

import requests, datetime, json, time
from bs4 import BeautifulSoup
import telegram, asyncio

def japaneseasmr(path):
    url = 'https://japaneseasmr.com'

    json_content = json.loads(open('../data/result.json', 'r', encoding='utf-8').read())
    last_update_time = datetime.datetime.strptime(json_content['japaneseasmr']['last_update_time'], '%Y-%m-%d')
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
    }


    req = requests.get(url + path, headers=headers)
    # req = open('test.html', 'r', encoding='utf-8').read()
    soup = BeautifulSoup(req.text, 'html.parser')
    del req

    message = []
    final_signal = 0
    date = json_content['japaneseasmr']['last_update_time']
    for info in soup.select('ul[class="site-archive-posts"] li'):
        upload_date = datetime.datetime.strptime(info.select('p[class="entry-tagline"] time')[0].get('datetime'), '%Y-%m-%d')
        page_url = info.select('div[class="op-square"] a')[0].get('href').rstrip('/')
        title = info.select('p[style="text-align: center;"]')[0].get_text()
        cv = info.select('p[style="text-align: center;"]')[1].get_text()
        rj_code = info.select('p[style="text-align: center;"]')[2].get_text()

        if upload_date > last_update_time:
            msg = '''%s
%s
%s
%s''' % (title, cv, rj_code, page_url)
            message.append(msg)
            date = datetime.datetime.strftime(upload_date, '%Y-%m-%d')
        else:
            final_signal = 1






    return {"final_signal": final_signal, "message": message, "upload_date": date}




async def sendmessage(token, chat_id, text):
    bot = telegram.Bot(token)
    async with bot:
        await bot.send_message(text=text, chat_id=chat_id)


if __name__ == '__main__':
    token = '5599701266:AAFbrRypK2lOL9of_yQzsJoTOY4cDURUSm8'
    chat_id = -1001592534864

    count = 0
    json_content = json.loads(open('../data/result.json', 'r', encoding='utf-8').read())
    while True:
        count += 1
        path = '/page/%d/' % count

        req = japaneseasmr(path)
        message_list = req['message']
        for message in message_list:
            asyncio.run(sendmessage(token, chat_id, message))
            time.sleep(random.randint(2, 5))

        if datetime.datetime.strptime(req['upload_date'], '%Y-%m-%d') > \
                datetime.datetime.strptime(json_content['japaneseasmr']['last_update_time'],
                                           '%Y-%m-%d'):
            json_content['japaneseasmr']['last_update_time'] = req['upload_date']

        if req['final_signal'] == 1:
            open('../data/result.json', 'w', encoding='utf-8').write(json.dumps(json_content))
            break



