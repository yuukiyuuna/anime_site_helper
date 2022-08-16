# -*- coding=utf-8 -*-

import requests, json, random, time
from loguru import logger
import telegram, asyncio

def abema():
    mainpage_url = 'https://abema.tv'
    new_url = 'https://user-content-api.ep.c3.abema.io'
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.81 Safari/537.36 Edg/104.0.1293.54",
        "origin": mainpage_url,
        "referer": mainpage_url,
        "authorization": "bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkZXYiOiIyZTk4MGJiNS0yN2RhLTQxNjktOThjYS0wZDJkODAxZTZjMWYiLCJleHAiOjIxNDc0ODM2NDcsImlzcyI6ImFiZW1hLmlvL3YxIiwic3ViIjoiRGNlNEsyV2hnOWVVRVQifQ.szCvUXbA11JevhnCv7zIjlz2ZkXDgE6ygWrn86h4d8c"
    }

    limit = 40
    itemNext = 0
    final_signal = 0
    message = []
    while final_signal == 0:
        # 构建请求url
        path = '/v1/modules/CVX74spj9VVV59?itemLimit=%d&itemNext=%d' %(limit, itemNext)
        url = new_url + path
        new_last_update_time = last_update_time = json.loads(open('../data/result.json', 'r',
                                           encoding='utf-8').read())['abema']['last_update_time']
        message_count = len(message)
        # 此文件存放作品分类，用于判断是否为动漫类别
        # 此表中若没有类别则会请求判断然后补充至此disc，再写入此表（全类别一次性写入）
        abema_leibie_json = json.loads(open('../data/abema-save.json', 'r', encoding='utf-8').read())

        logger.info('开始请求 %s 接口信息: ' % url)
        req = requests.get(url, headers=headers)
        for list in req.json()['module']['items']:
            if int(list['startAt']) > last_update_time:
                # 记录最新的最后更新时间
                if int(list['startAt']) > new_last_update_time:
                    new_last_update_time = int(list['startAt'])

                if abema_leibie_json.get(list['id'].split('#')[2]):
                    if abema_leibie_json[list['id'].split('#')[2]] == 'animation':
                        logger.debug(list)
                        caption = list['caption']
                        title = list['title']
                        url_path = mainpage_url + '/video/episode/' + list['id'].split('#')[2]

                        msg = '''番剧名称：%s
番剧集数：%s
%s''' % (caption, title, url_path)
                        message.append(msg)
                else:
                    try:
                        info_url = 'https://api.abema.io'
                        info_path = '/v1/video/programs/%s?division=1&include=tvod' %list['id'].split('#')[2]
                        info_req = requests.get(info_url + info_path, headers=headers)
                        abema_leibie_json[list['id'].split('#')[2]] = info_req.json()['genre']['id']
                        if info_req.json()['genre']['id'] == 'animation':
                            logger.debug(list)
                            caption = list['caption']
                            title = list['title']
                            url_path = mainpage_url + '/video/episode/' + list['id'].split('#')[2]

                            msg = '''番剧名称：%s
番剧集数：%s
%s''' % (caption, title, url_path)
                            message.append(msg)
                    except Exception as e:
                        logger.error('请求作品详情出错 %s' )
                        logger.error(e)

        open('../data/abema-save.json', 'w', encoding='utf-8').write(json.dumps(abema_leibie_json))
        logger.info('本url解析新增 %d 条消息' %(len(message) - message_count))

        if req.json().get('itemNext'):
            itemNext += limit
        else:
            final_signal = 1
    logger.info('共新增 %d 条消息' %len(message))

    return message, new_last_update_time



async def sendmessage(token, chat_id, text):
    bot = telegram.Bot(token)
    async with bot:
        await bot.send_message(text=text, chat_id=chat_id)


if __name__ == '__main__':
    token = '5599701266:AAFbrRypK2lOL9of_yQzsJoTOY4cDURUSm8'
    chat_id = -1001592534864

    list, last_update_time = abema()
    json_data = json.loads(open('../data/result.json', 'r', encoding='utf-8').read())
    json_data['abema']['last_update_time'] = last_update_time
    open('../data/result.json', 'w', encoding='utf-8').write(json.dumps(json_data))

    for i in list:
        asyncio.run(sendmessage(token, chat_id, i))
        time.sleep(random.randint(2, 5))