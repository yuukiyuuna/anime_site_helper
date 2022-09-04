# -*- coding=utf-8 -*-
import time

import requests, datetime, json, random
from loguru import logger
from filelock import FileLock
from bs4 import BeautifulSoup
from bin.telegram_tools import telegram_tool


def yurifans(lock):
    url = 'https://yuri.website/'
    result_json_path = r'./data/result.json'
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
    }
    with FileLock(result_json_path + '.lock'):
        json_content = json.loads(open(result_json_path, 'r', encoding='utf-8').read())
    # json_content = json.loads(open('../data/result.json', 'r', encoding='utf-8').read())
    logger.info('读取配置文件成功， 最后检测时间为：%s' % json_content['yurifans']['last_update_time'])
    last_update_time = datetime.datetime.strptime(json_content['yurifans']['last_update_time'], '%Y-%m-%d %H:%M:%S')
    del json_content


    req = requests.get(url, headers=headers)
    if req.status_code == 200:
        logger.info('网址请求成功  %s' % req.request.url)
    else:
        logger.warning('网址请求失败  %s  返回码: %d' %(req.request.url, req.status_code))
        logger.warning(req.content)

    soup = BeautifulSoup(req.text, 'html.parser')
    info_list = soup.select('li[class="post-list-item item-post-style-3"] h2 a')
    update_time_list = soup.select('li[class="post-list-item item-post-style-3"] div[class="list-footer"] time')
    del req, soup

    message = []
    if len(info_list) == len(update_time_list):
        logger.info('查找到 %d 个新发布' % len(info_list))
        logger.debug(info_list)
        for i in range(0, len(update_time_list)):
            title = info_list[i].get_text()
            url = info_list[i].get('href')
            update_time = datetime.datetime.strptime(update_time_list[i].get('datetime'), '%Y-%m-%d %H:%M:%S')

            if update_time > last_update_time:
                msg = '''%s
%s''' % (title, url)
                message.append(msg)
        del i, title, url, update_time, info_list, msg      # 省 message列表 和 update_time_list列表

        # 因为第一个时间永远是最新的，所以直接用第一个更新时间判断并写入文件
        with FileLock(result_json_path + '.lock'):
            json_content = json.loads(open(result_json_path, 'r', encoding='utf-8').read())
            if datetime.datetime.strptime(update_time_list[0].get('datetime'), '%Y-%m-%d %H:%M:%S') > \
                    datetime.datetime.strptime(json_content['yurifans']['last_update_time'], '%Y-%m-%d %H:%M:%S'):
                json_content['yurifans']['last_update_time'] = update_time_list[0].get('datetime')
                open(result_json_path, 'w', encoding='utf-8').write(json.dumps(json_content))
        del json_content, update_time_list

    else:
        logger.error('查找新发布失败，成功获取内容但内容可能存在问题，数量不一致')
        logger.error(info_list)
        logger.error(update_time_list)

    message.reverse()
    lock.acquire()
    try:
        telegram_api = telegram_tool()
        # telegram_send = threading.Thread(target=telegram_api.send, args=(message, 'markdown'))
        telegram_api.send(message=message)
    except Exception as e:
        logger.error('yurifans 发送消息失败')
        logger.error(e)
    lock.release()


# async def sendmessage(token, chat_id, text):
#     bot = telegram.Bot(token)
#     async with bot:
#         await bot.send_message(text=text, chat_id=chat_id)
#
#
# if __name__ == '__main__':
#     token = '5599701266:AAFbrRypK2lOL9of_yQzsJoTOY4cDURUSm8'
#     chat_id = -1001592534864
#
#     message_list = yulifans()
#     if len(message_list) != 0:
#         for message in message_list:
#             asyncio.run(sendmessage(token, chat_id, message))
#             time.sleep(random.randint(2, 5))
